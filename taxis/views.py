import requests
from django.conf import settings
from geopy.distance import geodesic
from django.shortcuts import render, redirect, reverse
from django.http import JsonResponse, HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.db import models
from .models import Taxi, TaxiRoute, Ride, RideDestination, AppUser, ConversacionTelegram, Rating
from django.contrib.auth import login, logout
from .forms import CustomerRegistrationForm,CustomerProfileForm, DriverProfileForm, TaxiForm, TaxiRouteForm, RideFilterForm, DriverRegistrationForm, AdminProfileForm
#from django.contrib.auth.forms import DriverRegistrationForm, CustomerRegistrationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.cache import cache
#from taxis.views import telegram_webhook  # cambia "tu_app" por el nombre real de tu app

# Logger
logger = logging.getLogger(__name__)

#import requests


def home(request):
    return render(request, 'home.html')


@login_required
def revision(request):
    # Verificar si el usuario es superusuario
    if not request.user.is_superuser:
        return redirect('home')  # Redirige si no tiene permisos

    # Obtener todas las carreras
    rides = Ride.objects.all()

    # Procesar los filtros del formulario
    form = RideFilterForm(request.GET or None)
    if form.is_valid():
        status = form.cleaned_data.get('status')
        driver = form.cleaned_data.get('driver')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        # Filtrar por estado
        if status:
            rides = rides.filter(status=status)

        # Filtrar por conductor
        if driver:
            rides = rides.filter(driver=driver)

        # Filtrar por rango de fechas
        if start_date:
            rides = rides.filter(created_at__date__gte=start_date)
        if end_date:
            rides = rides.filter(created_at__date__lte=end_date)

    # Obtener datos adicionales de las carreras
    requested_rides = rides.filter(status='requested')
    in_progress_rides = rides.filter(status='in_progress')
    completed_rides = rides.filter(status='completed')
    canceled_rides = rides.filter(status='canceled')
    drivers = set(ride.driver for ride in rides.exclude(driver=None))

    context = {
        'form': form,
        'rides': rides,
        'requested_rides': requested_rides,
        'in_progress_rides': in_progress_rides,
        'completed_rides': completed_rides,
        'canceled_rides': canceled_rides,
        'drivers': drivers,
    }
    return render(request, 'admin_dashboard.html', context)

def register_driver(request):
    if request.method == 'POST':
        form = DriverRegistrationForm(request.POST, request.FILES)  # Soporte para subir imágenes
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente tras el registro
            return redirect('driver_dashboard')  # Cambia según tu vista de conductores
        else:
            print(form.errors)  # Debug: muestra errores en la consola
    else:
        form = DriverRegistrationForm()
    return render(request, 'registration/register_driver.html', {'form': form})

def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request.FILES)  # Soporte para subir imágenes
        if form.is_valid():
            user = form.save()
            login(request, user)  # Inicia sesión automáticamente tras el registro
            return redirect('customer_dashboard')  # Cambia según tu vista de clientes
        else:
            print(form.errors)  # Debug: muestra errores en la consola
    else:
        form = CustomerRegistrationForm()
    return render(request, 'registration/register_customer.html', {'form': form})
# Vista para el perfil de usuario
@login_required
def profile_view(request):
    # Preparar datos adicionales según el rol del usuario
    user = request.user
    context = {
        'user': user,
    }

    if user.role == 'driver':
        # Verificar si el taxista tiene un taxi asignado
        if hasattr(user, 'taxi'):
            context.update({
                'taxi': user.taxi,  # Relación OneToOne con el modelo Taxi
            })
        else:
            # Si no tiene taxi, puedes asignar un valor por defecto o manejar el caso
            context.update({
                'taxi': None,
            })

    return render(request, 'registration/profile.html', context)


# Vista para cerrar sesión
def logout_view(request):
    logout(request)
    return redirect('login')

def map_view(request):
    return render(request, 'taxis/map.html')

@csrf_exempt
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            if request.user.is_authenticated:
                taxi = request.user.taxi
                taxi.latitude = latitude
                taxi.longitude = longitude
                taxi.save()

                # Enviar la ubicación a los clientes conectados vía WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    "taxi_updates",  # Asegúrate de que este grupo esté configurado en tu WebSocket consumer
                    {
                        "type": "update_location",
                        "message": {
                            "username": request.user.username,
                            "latitude": latitude,
                            "longitude": longitude,
                        },
                    }
                )

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "fail"}, status=400)


def driver_dashboard(request):
    if request.user.role != 'driver':
        return redirect('login')
    
    # Obtener el taxi del conductor
    try:
        taxi = Taxi.objects.get(user=request.user)
    except Taxi.DoesNotExist:
        taxi = None
    
    # Obtener estadísticas del conductor
    total_rides = Ride.objects.filter(driver=request.user).count()
    completed_rides = Ride.objects.filter(driver=request.user, status='completed').count()
    canceled_rides = Ride.objects.filter(driver=request.user, status='canceled').count()
    active_rides_count = Ride.objects.filter(
        driver=request.user, 
        status__in=['accepted', 'in_progress']
    ).count()
    
    # Calcular ganancias (basado en precio de carreras completadas)
    from django.db.models import Sum
    today = now().date()
    
    # Ganancias del día
    today_earnings = Ride.objects.filter(
        driver=request.user, 
        status='completed',
        created_at__date=today,
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Ganancias del mes
    month_earnings = Ride.objects.filter(
        driver=request.user, 
        status='completed',
        created_at__year=today.year,
        created_at__month=today.month,
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Ganancias totales
    total_earnings = Ride.objects.filter(
        driver=request.user, 
        status='completed',
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Carreras de hoy
    today_rides_count = Ride.objects.filter(
        driver=request.user, 
        status='completed',
        created_at__date=today
    ).count()
    
    # Obtener carreras disponibles (sin conductor asignado)
    available_rides_list = Ride.objects.filter(
        status='requested',
        driver__isnull=True
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Obtener carreras activas del conductor
    active_rides_list = Ride.objects.filter(
        driver=request.user,
        status__in=['accepted', 'in_progress']
    ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
    
    # Obtener últimas carreras completadas
    recent_completed = Ride.objects.filter(
        driver=request.user,
        status='completed'
    ).select_related('customer').order_by('-created_at')[:5]
    
    # Calcular rating promedio (si existe campo de rating)
    # Por ahora usamos un placeholder
    rating = 4.8
    
    context = {
        'taxi': taxi,
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'canceled_rides': canceled_rides,
        'active_rides': active_rides_count,
        'today_rides': today_rides_count,
        'today_earnings': today_earnings,
        'month_earnings': month_earnings,
        'total_earnings': total_earnings,
        'rating': rating,
        'available_rides': available_rides_list,
        'active_rides_list': active_rides_list,
        'recent_completed': recent_completed,
    }
    
    return render(request, 'driver_dashboard.html', context)

def customer_dashboard(request):
    if request.user.role != 'customer':
        return redirect('login')
    
    # Obtener estadísticas del usuario
    total_rides = Ride.objects.filter(customer=request.user).count()
    completed_rides = Ride.objects.filter(customer=request.user, status='completed').count()
    active_rides = Ride.objects.filter(
        customer=request.user, 
        status__in=['requested', 'accepted', 'in_progress']
    ).count()
    
    # Obtener viajes recientes (últimos 5)
    recent_rides = Ride.objects.filter(customer=request.user).order_by('-created_at')[:5]
    
    context = {
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'active_rides': active_rides,
        'recent_rides': recent_rides,
    }
    
    return render(request, 'customer_dashboard.html', context)

def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('login')
    
    # Estadísticas generales
    total_users = AppUser.objects.count()
    total_drivers = AppUser.objects.filter(role='driver').count()
    total_customers = AppUser.objects.filter(role='customer').count()
    total_rides = Ride.objects.count()
    
    # Carreras por estado
    requested_rides = Ride.objects.filter(status='requested').count()
    accepted_rides = Ride.objects.filter(status='accepted').count()
    in_progress_rides = Ride.objects.filter(status='in_progress').count()
    completed_rides = Ride.objects.filter(status='completed').count()
    canceled_rides = Ride.objects.filter(status='canceled').count()
    
    # Ingresos
    from django.db.models import Sum
    total_revenue = Ride.objects.filter(status='completed', price__isnull=False).aggregate(
        total=Sum('price')
    )['total'] or 0
    
    # Carreras de hoy
    from django.utils import timezone
    today = timezone.now().date()
    today_rides = Ride.objects.filter(created_at__date=today).count()
    today_revenue = Ride.objects.filter(
        status='completed', 
        price__isnull=False,
        created_at__date=today
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Conductores activos (con ubicación)
    active_drivers = Taxi.objects.exclude(
        latitude__isnull=True, 
        longitude__isnull=True
    ).count()
    
    # Carreras recientes
    recent_rides = Ride.objects.select_related('customer', 'driver').order_by('-created_at')[:10]
    
    # Calificaciones promedio
    from django.db.models import Avg
    avg_rating = Rating.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    total_ratings = Rating.objects.count()
    
    context = {
        'total_users': total_users,
        'total_drivers': total_drivers,
        'total_customers': total_customers,
        'total_rides': total_rides,
        'requested_rides': requested_rides,
        'accepted_rides': accepted_rides,
        'in_progress_rides': in_progress_rides,
        'completed_rides': completed_rides,
        'canceled_rides': canceled_rides,
        'total_revenue': total_revenue,
        'today_rides': today_rides,
        'today_revenue': today_revenue,
        'active_drivers': active_drivers,
        'recent_rides': recent_rides,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'total_ratings': total_ratings,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required
def edit_profile(request):
    if request.user.role == 'customer':  # Cliente
        if request.method == 'POST':
            form = CustomerProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('customer_dashboard')
        else:
            form = CustomerProfileForm(instance=request.user)
        return render(request, 'edit_customer_profile.html', {'form': form})

    elif request.user.role == 'driver':  # Taxista
        # Verificar si el conductor tiene un taxi asignado; si no, crear uno
        if not hasattr(request.user, 'taxi'):
            Taxi.objects.create(user=request.user, plate_number="XXX", vehicle_description="Descripción del vehículo")

        if request.method == 'POST':
            user_form = DriverProfileForm(request.POST, request.FILES, instance=request.user)
            taxi_form = TaxiForm(request.POST, instance=request.user.taxi)
            if user_form.is_valid() and taxi_form.is_valid():
                user_form.save()
                taxi_form.save()
                return redirect('driver_dashboard')
        else:
            user_form = DriverProfileForm(instance=request.user)
            taxi_form = TaxiForm(instance=request.user.taxi)

        return render(request, 'edit_driver_profile.html', {'user_form': user_form, 'taxi_form': taxi_form})

    elif request.user.role == 'admin':  # Administrador
        if request.method == 'POST':
            form = AdminProfileForm(request.POST, request.FILES, instance=request.user)  # Puedes usar el mismo formulario o crear uno específico
            if form.is_valid():
                form.save()
                return redirect('admin_dashboard')
        else:
            form = AdminProfileForm(instance=request.user)
        return render(request, 'edit_admin_profile.html', {'form': form})

    else:
        return redirect('login')  # Redirigir si el rol no es válido


@login_required
def taxi_route_view(request):
    taxi_route, created = TaxiRoute.objects.get_or_create(taxi=request.user.taxi)

    if request.method == 'POST':
        form = TaxiRouteForm(request.POST, instance=taxi_route)
        if form.is_valid():
            # Guarda los datos del formulario sin confirmar aún
            taxi_route = form.save(commit=False)

            # Verifica si se presionó el botón de confirmar disponibilidad
            if 'confirm_available' in request.POST:
                taxi_route.is_available = True

            # Revisa si todos los asientos están ocupados
            if all(taxi_route.passengers):  # Usa la propiedad `passengers`
                taxi_route.is_available = False
                taxi_route.estimated_arrival_time = now() + timedelta(minutes=5)

            # Guarda los cambios
            taxi_route.save()
            return redirect('taxi_route_list')  # Cambia 'taxi_route_list' por el nombre real de tu URL
    else:
        form = TaxiRouteForm(instance=taxi_route)

    # Renderiza la plantilla con el formulario y la lista de pasajeros
    return render(request, 'taxi_route_form.html', {
        'form': form,
        'taxi_route': taxi_route,
        'passengers': taxi_route.passengers  # Pasa la lista de pasajeros
    })


@login_required
def taxi_route_list_view(request):
    # Filtrar solo las rutas asociadas al taxista autenticado
    taxi_routes = TaxiRoute.objects.filter(is_available=True)
    return render(request, 'taxi_route_list.html', {'taxi_routes': taxi_routes})

@login_required
def join_taxi_route_view(request, route_id):
    # Obtener la ruta disponible
    route = get_object_or_404(TaxiRoute, id=route_id, is_available=True)

    # Verifica si el usuario ya está en la lista de pasajeros
    if request.user.username in route.passengers:
        return redirect('taxi_route_list')

    # Encuentra el primer asiento vacío y asigna al usuario
    if not route.passenger_1:
        route.passenger_1 = request.user.username
    elif not route.passenger_2:
        route.passenger_2 = request.user.username
    elif not route.passenger_3:
        route.passenger_3 = request.user.username
    elif not route.passenger_4:
        route.passenger_4 = request.user.username

    # Revisa si todos los asientos están ocupados
    if all(route.passengers):
        route.is_available = False  # Cambiar disponibilidad

    # Guarda los cambios
    route.save()
    return redirect('taxi_route_list')

@login_required
def available_routes_list_view(request):
    # Filtrar rutas disponibles
    available_routes = TaxiRoute.objects.filter(is_available=True)
    return render(request, 'available_routes_list.html', {'routes': available_routes})
# Geocodificación inversa (lat, lng → dirección)
# Constantes
TELEGRAM_CHAT_ID_GRUPO_TAXISTAS = -4767733103
usuarios_estado = {}      # Estado para clientes (chat privado)
conductores_estado = {}   # Estado para conductores (grupo)


# 📩 Enviar mensajes a Telegram
def enviar_telegram(chat_id, mensaje, botones=None, parse_mode='HTML'):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': mensaje,
        'parse_mode': parse_mode
    }
    if botones:
        payload['reply_markup'] = json.dumps({"inline_keyboard": botones})
    response = requests.post(url, data=payload)
    if not response.ok:
        print("❌ Error enviando mensaje a Telegram:", response.text)
    return response


# 📍 Convertir dirección en coordenadas
def direccion_a_coordenadas(direccion, api_key):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(direccion)}&key={api_key}&language=es"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            datos = response.json()
            if datos.get('results'):
                loc = datos['results'][0]['geometry']['location']
                return loc['lat'], loc['lng']
    except Exception as e:
        print(f"❌ Error en direccion_a_coordenadas: {e}")
    return None, None



# 🧭 Obtener dirección legible desde coordenadas usando Google Maps
def obtener_direccion_google(lat, lng, api_key):
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}&language=es"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            datos = response.json()
            for resultado in datos.get("results", []):
                tipos = resultado.get("types", [])
                # Evitar plus_code y tomar tipo de calle o ruta
                if "plus_code" not in tipos and any(t in tipos for t in ("street_address", "route", "premise", "sublocality")):
                    return resultado.get("formatted_address")
            if datos.get("results"):
                return datos["results"][0].get("formatted_address")
    except Exception as e:
        print(f"❌ Error obteniendo dirección: {e}")
    return "Dirección desconocida"



# 🗺️ URL para ver ruta en Google Maps
def get_map_url(lat1, lng1, lat2, lng2):
    return f"https://www.google.com/maps/dir/?api=1&origin={lat1},{lng1}&destination={lat2},{lng2}&travelmode=driving"



# 📏 Obtener distancia y duración estimada entre dos puntos
def get_distance_duration(lat1, lng1, lat2, lng2):
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/distancematrix/json?units=metric"
            f"&origins={lat1},{lng1}&destinations={lat2},{lng2}&key={settings.GOOGLE_API_KEY}"
        )
        response = requests.get(url, timeout=5).json()
        if response.get('status') == 'OK':
            element = response['rows'][0]['elements'][0]
            if element.get('status') == 'OK':
                return element['distance']['text'], element['duration']['text']
    except Exception as e:
        print(f"❌ Error en get_distance_duration: {e}")
    return None, None


# 🚕 Buscar el taxista más cercano a una ubicación
def obtener_taxista_mas_cercano(lat, lng):
    """
    Busca el taxista más cercano a una ubicación
    Ahora acepta conductores con Telegram O WhatsApp
    """
    origen = (lat, lng)
    taxistas = Taxi.objects.select_related('user').filter(
        user__role='driver',
        latitude__isnull=False,
        longitude__isnull=False
    ).filter(
        # Que tenga Telegram O WhatsApp
        models.Q(user__telegram_chat_id__isnull=False) | 
        models.Q(user__phone_number__isnull=False)
    )
    
    if not taxistas.exists():
        logger.warning(f"⚠️ No se encontraron taxistas disponibles cerca de ({lat}, {lng})")
        return None
    
    taxista_cercano = min(
        taxistas,
        key=lambda t: geodesic(origen, (t.latitude, t.longitude)).km
    )
    
    distancia = geodesic(origen, (taxista_cercano.latitude, taxista_cercano.longitude)).km
    logger.info(f"✅ Taxista más cercano: {taxista_cercano.user.get_full_name()} a {distancia:.2f} km")
    
    return taxista_cercano


@csrf_exempt
def telegram_webhook(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"})

    data = json.loads(request.body.decode("utf-8"))

    # ==== Botón presionado ====
    if "callback_query" in data:
        callback = data["callback_query"]
        callback_data = callback.get("data")
        from_user = callback.get("from", {})
        telegram_user_id = str(from_user.get("id"))
        chat_id = callback["message"]["chat"]["id"]
        message_id = callback["message"]["message_id"]

        if callback_data and callback_data.startswith("aceptar_"):
            ride_id = callback_data.split("_")[1]

            try:
                taxista = AppUser.objects.get(telegram_chat_id=telegram_user_id, role='driver')
            except AppUser.DoesNotExist:
                requests.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery", data={
                    "callback_query_id": callback["id"],
                    "text": "❌ Solo conductores registrados pueden aceptar carreras.",
                    "show_alert": True
                })
                return JsonResponse({"ok": True})

            try:
                ride = Ride.objects.get(id=ride_id, status='requested')
            except Ride.DoesNotExist:
                requests.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery", data={
                    "callback_query_id": callback["id"],
                    "text": "🚫 La carrera ya fue aceptada o no existe.",
                    "show_alert": True
                })
                return JsonResponse({"ok": True})

            ride.driver = taxista
            ride.status = "accepted"
            ride.save()

            requests.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/editMessageReplyMarkup", data={
                "chat_id": chat_id,
                "message_id": message_id,
                "reply_markup": json.dumps({"inline_keyboard": []})
            })

            requests.post(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/answerCallbackQuery", data={
                "callback_query_id": callback["id"],
                "text": "✅ Carrera aceptada. ¡Buena ruta!",
                "show_alert": False
            })

            if ride.customer.telegram_chat_id:
                enviar_telegram(
                    ride.customer.telegram_chat_id,
                    f"🚖 Tu carrera fue aceptada por {taxista.get_full_name()}.")

            enviar_telegram(chat_id, f"✅ La carrera ID {ride_id} fue aceptada por {taxista.get_full_name()}.")
            return JsonResponse({"ok": True})

    # ==== Mensajes normales ====
    mensaje = data.get("message", {})
    if not mensaje:
        return JsonResponse({"ok": True})

    chat = mensaje.get("chat", {})
    chat_id = chat.get("id")
    texto = mensaje.get("text")
    ubicacion = mensaje.get("location")
    venue = mensaje.get("venue")
    from_user = mensaje.get("from", {})
    from_id = from_user.get("id")

    if not chat_id:
        return JsonResponse({"ok": False, "error": "No chat ID"})

    # === Registro conductores (grupo) ===
    if str(chat_id) == str(TELEGRAM_CHAT_ID_GRUPO_TAXISTAS):
        if texto and texto.replace("+", "").isdigit() and len(texto) >= 7:
            try:
                taxista = AppUser.objects.get(phone_number=texto.strip(), role='driver')
                if taxista.telegram_chat_id:
                    enviar_telegram(chat_id, f"⚠️ El conductor {taxista.get_full_name()} ya está registrado.")
                else:
                    taxista.telegram_chat_id = str(from_id)
                    taxista.save()
                    enviar_telegram(chat_id, f"✅ Conductor {taxista.get_full_name()} vinculado con éxito.")
            except AppUser.DoesNotExist:
                enviar_telegram(chat_id, "❌ No hay ningún conductor con ese número registrado.")
        else:
            enviar_telegram(chat_id, "📲 Envía tu número celular para vincular tu cuenta.")
        return JsonResponse({"ok": True})

    # === Clientes (chat privado) ===
    
    usuarios_duplicados = AppUser.objects.filter(telegram_chat_id=str(chat_id))
    usuario = usuarios_duplicados.first()

    if usuarios_duplicados.count() > 1:
        # Mantener solo el primero y limpiar los demás
        for u in usuarios_duplicados[1:]:
            u.telegram_chat_id = None
            u.save()

    if not usuario:
        # Registrar usuario usando número de teléfono
        if texto and texto.replace("+", "").isdigit() and len(texto) >= 7:
            try:
                usuario = AppUser.objects.get(phone_number=texto.strip(), role="customer")
                usuario.telegram_chat_id = str(chat_id)
                usuario.save()
                usuarios_estado[chat_id] = {"estado": "esperando_origen"}
                enviar_telegram(chat_id, "✅ Número verificado. Ahora envía tu <b>ubicación de origen</b>.")
            except AppUser.DoesNotExist:
                enviar_telegram(chat_id, "❌ Tu número no está registrado. Regístrate desde la app web.")
        else:
            enviar_telegram(chat_id, "📲 Envía tu número celular para verificar tu cuenta.")
        return JsonResponse({"ok": True})


    estado = usuarios_estado.get(chat_id, {}).get("estado")

    if texto == "/start":
        usuarios_estado[chat_id] = {"estado": "esperando_origen"}
        enviar_telegram(chat_id, "📍 Por favor, envía tu <b>ubicación de origen</b>.")
        return JsonResponse({"ok": True})

    # ==== Esperando origen ====
    if estado == "esperando_origen":
        # 🔹 NUEVO BLOQUE PARA TOMAR VENUE SI EXISTE
        if venue:
            direccion = venue.get("title") or venue.get("address")
            lat, lng = venue.get("location", {}).get("latitude"), venue.get("location", {}).get("longitude")
        elif ubicacion:
            lat, lng = ubicacion["latitude"], ubicacion["longitude"]
            direccion = obtener_direccion_google(lat, lng, settings.GOOGLE_API_KEY)
        elif texto:
            direccion = texto
            lat, lng = direccion_a_coordenadas(texto, settings.GOOGLE_API_KEY)
        else:
            enviar_telegram(chat_id, "❌ Envíame una dirección o ubicación válida.")
            return JsonResponse({"ok": True})

        if lat and lng:
            usuarios_estado[chat_id] = {
                "estado": "esperando_destino",
                "origen": {"direccion": direccion, "lat": lat, "lng": lng}
            }
            enviar_telegram(chat_id, "📍 Ahora envía tu <b>destino</b>.")
        else:
            enviar_telegram(chat_id, "❌ Dirección no encontrada. Intenta de nuevo.")
        return JsonResponse({"ok": True})

    # ==== Esperando destino ====
    if estado == "esperando_destino":
        origen = usuarios_estado[chat_id]["origen"]

        # 🔹 NUEVO BLOQUE PARA TOMAR VENUE SI EXISTE
        if venue:
            direccion = venue.get("title") or venue.get("address")
            lat, lng = venue.get("location", {}).get("latitude"), venue.get("location", {}).get("longitude")
        elif ubicacion:
            lat, lng = ubicacion["latitude"], ubicacion["longitude"]
            direccion = obtener_direccion_google(lat, lng, settings.GOOGLE_API_KEY)
        elif texto:
            direccion = texto
            lat, lng = direccion_a_coordenadas(texto, settings.GOOGLE_API_KEY)
        else:
            enviar_telegram(chat_id, "❌ Dirección de destino no válida.")
            return JsonResponse({"ok": True})

        if lat and lng:
            distancia, duracion = get_distance_duration(origen["lat"], origen["lng"], lat, lng)
            mapa = get_map_url(origen["lat"], origen["lng"], lat, lng)

            ride = Ride.objects.create(
                customer=usuario,
                origin=origen["direccion"],
                origin_latitude=origen["lat"],
                origin_longitude=origen["lng"],
                status="requested"
            )

            RideDestination.objects.create(
                ride=ride,
                destination=direccion,
                destination_latitude=lat,
                destination_longitude=lng,
                order=0
            )

            botones = [[{"text": "✅ Aceptar carrera", "callback_data": f"aceptar_{ride.id}"}]]

            enviar_telegram(chat_id, f"✅ Carrera solicitada\n\n📍 Origen: {origen['direccion']}\n🏁 Destino: {direccion}\n🛣️ Distancia: {distancia}\n⏱️ Duración: {duracion}\n<a href='{mapa}'>📍 Ver mapa</a>")

            taxista = obtener_taxista_mas_cercano(origen["lat"], origen["lng"])
            if taxista and taxista.user.telegram_chat_id:
                enviar_telegram(taxista.user.telegram_chat_id, f"🚖 Nueva carrera cerca tuyo:\n📍 {origen['direccion']}\n🏁 {direccion}", botones=botones)

            enviar_telegram(TELEGRAM_CHAT_ID_GRUPO_TAXISTAS, f"📣 Nueva carrera disponible:\n📍 {origen['direccion']}\n🏁 {direccion}", botones=botones)
            usuarios_estado.pop(chat_id, None)
        else:
            enviar_telegram(chat_id, "❌ Dirección no encontrada. Intenta de nuevo.")
        return JsonResponse({"ok": True})

    enviar_telegram(chat_id, "👋 Hola. Escribe /start para solicitar un taxi 🚕.")
    return JsonResponse({"ok": True})

def service_worker(request):
    """
    Serves the service-worker.js file from the static directory
    but with a root scope.
    """
    from django.conf import settings
    import os
    
    # Try to find the file in staticfiles (production) or static (development)
    sw_path = os.path.join(settings.BASE_DIR, 'staticfiles', 'js', 'service-worker.js')
    if not os.path.exists(sw_path):
        sw_path = os.path.join(settings.BASE_DIR, 'taxis', 'static', 'js', 'service-worker.js')
        
    if os.path.exists(sw_path):
        with open(sw_path, 'rb') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/javascript')
    else:
        return HttpResponse("Service Worker not found", status=404)



@login_required
def request_ride(request):
    if request.method == 'POST':
        origin = request.POST.get('origin')
        price = request.POST.get('price')
        origin_lat = request.POST.get('origin_latitude')
        origin_lng = request.POST.get('origin_longitude')
        destinations = request.POST.getlist('destinations[]')
        destination_coords = request.POST.getlist('destination_coords[]')

        if all([origin, origin_lat, origin_lng, destinations, destination_coords]):
            try:
                origin_lat = float(origin_lat)
                origin_lng = float(origin_lng)
                price = float(price)

                # Crear la solicitud de carrera
                ride = Ride.objects.create(
                    customer=request.user,
                    origin=origin,
                    origin_latitude=origin_lat,
                    origin_longitude=origin_lng,
                    price=price,
                    status='requested',
                )

                # Crear destinos asociados
                for i, destination in enumerate(destinations):
                    lat, lng = map(float, destination_coords[i].split(','))
                    RideDestination.objects.create(
                        ride=ride,
                        destination=destination,
                        destination_latitude=lat,
                        destination_longitude=lng,
                        order=i
                    )

                # Obtener dirección legible para origen
                direccion_legible = obtener_direccion_google(origin_lat, origin_lng, settings.GOOGLE_API_KEY)

                # Formatear lista de destinos legibles
                lista_destinos = "\n".join([f"➡️ Destino {i+1}: {d}" for i, d in enumerate(destinations)])

                # Mensaje para el grupo de conductores
                mensaje_grupo = (
                    f"🚕 <b>Nueva carrera solicitada</b>\n"
                    f"📍 Origen: {direccion_legible}\n"
                    f"{lista_destinos}\n"
                    f"👤 Cliente: {request.user.get_full_name()}\n"
                    f"💰 Precio estimado: ${price:.2f}"
                )

                # Botones para el mensaje: Aceptar y Ver en Google Maps
                botones = [[
                    {"text": "✅ Aceptar carrera", "callback_data": f"aceptar_{ride.id}"},
                    {"text": "🗺 Ver en Google Maps", "url": f"https://maps.google.com/?q={origin_lat},{origin_lng}"}
                ]]

                # Enviar mensaje al grupo de conductores por Telegram
                enviar_telegram(TELEGRAM_CHAT_ID_GRUPO_TAXISTAS, mensaje_grupo, botones)

                # Notificar al taxista más cercano por WhatsApp
                taxista_cercano = obtener_taxista_mas_cercano(origin_lat, origin_lng)
                if taxista_cercano:
                    mensaje_taxista_whatsapp = (
                        f"🚕 *Nueva carrera cerca de ti!*\n\n"
                        f"📍 *Origen:* {direccion_legible}\n"
                        f"{lista_destinos}\n"
                        f"👤 *Cliente:* {request.user.get_full_name()}\n"
                        f"📱 *Teléfono:* {request.user.phone_number}\n"
                        f"💰 *Precio:* ${price:.2f}\n\n"
                        f"🆔 *Carrera #*{ride.id}\n\n"
                        f"Para aceptar, responde:\n"
                        f"*ACEPTAR {ride.id}*"
                    )
                    
                    # Enviar por Telegram si tiene chat_id
                    if taxista_cercano.user.telegram_chat_id:
                        try:
                            mensaje_telegram = (
                                f"📣 Hola {taxista_cercano.user.get_full_name()}, hay una carrera cerca de ti:\n"
                                f"🛫 Desde: {direccion_legible}\n"
                                f"👤 Cliente: {request.user.get_full_name()}"
                            )
                            enviar_telegram(taxista_cercano.user.telegram_chat_id, mensaje_telegram)
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo enviar Telegram: {e}")
                    
                    # Enviar por WhatsApp si tiene número
                    if taxista_cercano.user.phone_number:
                        try:
                            from .whatsapp_agent_ai import whatsapp_agent_ai
                            whatsapp_agent_ai.enviar_mensaje(
                                taxista_cercano.user.phone_number,
                                mensaje_taxista_whatsapp
                            )
                            logger.info(f"✅ Notificación WhatsApp enviada a {taxista_cercano.user.get_full_name()}")
                        except Exception as e:
                            logger.warning(f"⚠️ No se pudo enviar WhatsApp: {e}")
                    
                    # Enviar notificación PWA push
                    try:
                        enviar_notificacion_pwa_conductor(
                            conductor=taxista_cercano.user,
                            titulo='🚕 Nueva carrera cerca de ti!',
                            mensaje=f'Origen: {direccion_legible}\nPrecio: ${price:.2f}',
                            datos={
                                'ride_id': ride.id,
                                'origin': direccion_legible,
                                'price': float(price),
                                'url': '/available-rides/'
                            }
                        )
                        logger.info(f"✅ Notificación PWA enviada a {taxista_cercano.user.get_full_name()}")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo enviar notificación PWA: {e}")

                messages.success(request, '¡Carrera solicitada con éxito!')
                return redirect(reverse('ride_detail', args=[ride.id]))

            except (ValueError, IndexError) as e:
                messages.error(request, f'Error en los datos: {str(e)}')
        else:
            messages.error(request, 'Completa todos los campos.')

    return render(request, 'request_ride.html', {
        'google_api_key': settings.GOOGLE_API_KEY,
        'direccion_legible': 'Aún no se ha seleccionado un origen'
    })


def crear_carrera_desde_whatsapp(user, origin, origin_lat, origin_lng, destination, dest_lat, dest_lng, price):
    """
    Función auxiliar para crear carreras desde WhatsApp
    Usa la misma lógica que request_ride pero sin request HTTP
    
    Args:
        user: Usuario (AppUser)
        origin: Dirección de origen (str)
        origin_lat: Latitud de origen (float)
        origin_lng: Longitud de origen (float)
        destination: Dirección de destino (str)
        dest_lat: Latitud de destino (float)
        dest_lng: Longitud de destino (float)
        price: Precio estimado (float)
        
    Returns:
        Ride object creado
    """
    try:
        # Crear la solicitud de carrera
        ride = Ride.objects.create(
            customer=user,
            origin=origin,
            origin_latitude=origin_lat,
            origin_longitude=origin_lng,
            price=price,
            status='requested',
        )
        
        # Crear destino asociado
        RideDestination.objects.create(
            ride=ride,
            destination=destination,
            destination_latitude=dest_lat,
            destination_longitude=dest_lng,
            order=0
        )
        
        # Obtener dirección legible para origen
        direccion_legible = obtener_direccion_google(origin_lat, origin_lng, settings.GOOGLE_API_KEY)
        
        # Mensaje para el grupo de conductores
        mensaje_grupo = (
            f"🚕 <b>Nueva carrera solicitada (WhatsApp)</b>\n"
            f"📍 Origen: {direccion_legible}\n"
            f"➡️ Destino: {destination}\n"
            f"👤 Cliente: {user.get_full_name()}\n"
            f"📱 Teléfono: {user.phone_number}\n"
            f"💰 Precio estimado: ${price:.2f}"
        )
        
        # Botones para el mensaje
        botones = [[
            {"text": "✅ Aceptar carrera", "callback_data": f"aceptar_{ride.id}"},
            {"text": "🗺 Ver en Google Maps", "url": f"https://maps.google.com/?q={origin_lat},{origin_lng}"}
        ]]
        
        # Enviar mensaje al grupo de conductores (si está configurado)
        try:
            # Usar la función enviar_telegram definida en este mismo archivo
            enviar_telegram(TELEGRAM_CHAT_ID_GRUPO_TAXISTAS, mensaje_grupo, botones)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo enviar a Telegram: {e}")
        
        # Notificar al taxista más cercano
        taxista_cercano = obtener_taxista_mas_cercano(origin_lat, origin_lng)
        if taxista_cercano:
            mensaje_taxista = (
                f"🚕 *Nueva carrera cerca de ti!*\n\n"
                f"📍 *Origen:* {direccion_legible}\n"
                f"🎯 *Destino:* {destination}\n"
                f"👤 *Cliente:* {user.get_full_name()}\n"
                f"📱 *Teléfono:* {user.phone_number}\n"
                f"💰 *Precio:* ${price:.2f}\n\n"
                f"🆔 *Carrera #*{ride.id}\n\n"
                f"Para aceptar, responde:\n"
                f"*ACEPTAR {ride.id}*"
            )
            
            # Enviar por Telegram si tiene chat_id
            if taxista_cercano.user.telegram_chat_id:
                try:
                    # Usar función local
                    enviar_telegram(taxista_cercano.user.telegram_chat_id, mensaje_taxista)
                    logger.info(f"✅ Notificación Telegram enviada a {taxista_cercano.user.get_full_name()}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo enviar a Telegram: {e}")
            
            # Enviar por WhatsApp si tiene número
            if taxista_cercano.user.phone_number:
                try:
                    from .whatsapp_agent_ai import whatsapp_agent_ai
                    whatsapp_agent_ai.enviar_mensaje(
                        taxista_cercano.user.phone_number,
                        mensaje_taxista
                    )
                    logger.info(f"✅ Notificación WhatsApp enviada a {taxista_cercano.user.get_full_name()}")
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo enviar WhatsApp: {e}")
            
            # Enviar notificación PWA push
            try:
                enviar_notificacion_pwa_conductor(
                    conductor=taxista_cercano.user,
                    titulo='🚕 Nueva carrera cerca de ti!',
                    mensaje=f'Origen: {direccion_legible}\nDestino: {destination}\nPrecio: ${price:.2f}',
                    datos={
                        'ride_id': ride.id,
                        'origin': direccion_legible,
                        'destination': destination,
                        'price': float(price),
                        'url': '/available-rides/'
                    }
                )
                logger.info(f"✅ Notificación PWA enviada a {taxista_cercano.user.get_full_name()}")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo enviar notificación PWA: {e}")
        
        logger.info(f"✅ Carrera creada desde WhatsApp: {ride.id}")
        return ride
        
    except Exception as e:
        logger.error(f"❌ Error al crear carrera desde WhatsApp: {e}")
        raise


@login_required
def available_rides(request):
    if not request.user.is_superuser and request.user.role != 'driver':
        return JsonResponse({'error': 'Acceso no permitido'}, status=403)

    # Obtener las solicitudes de taxi
    rides = Ride.objects.filter(status='requested').order_by('created_at')

    # Si es un POST, es para actualizar el precio
    if request.method == 'POST':
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Solo el superusuario puede establecer el precio'}, status=403)

        ride_id = request.POST.get('ride_id')
        price = request.POST.get('price')

        if not price or not price.replace('.', '', 1).isdigit() or float(price) <= 0:
            return JsonResponse({'error': 'Precio no válido'}, status=400)

        ride = get_object_or_404(Ride, id=ride_id)
        ride.price = float(price)
        ride.save()

        # Responder con éxito y el nuevo precio
        return JsonResponse({'success': True, 'ride_id': ride.id, 'new_price': ride.price})

    # Para choferes, simplemente devuelve las solicitudes con precios
    return render(request, 'available_rides.html', {'rides': rides})



@login_required
def update_ride_status(request, ride_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        ride = get_object_or_404(Ride, id=ride_id)

        if ride.driver and ride.driver != request.user:
            return JsonResponse({'error': 'Acceso no autorizado'}, status=403)

        new_status = request.POST.get('status')

        if new_status == 'in_progress' and not ride.driver:
            ride.driver = request.user
            ride.status = 'in_progress'
            ride.save()

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('ride_detail', args=[ride.id])
            })

        elif new_status == 'completed':
            ride.status = 'completed'
            ride.end_time = now()
            ride.save()

            return JsonResponse({
                'success': True,
                'message': 'Carrera completada con éxito',
                'new_status': 'Completada',
                'new_status_color': 'success'
            })

        elif new_status == 'canceled':
            ride.status = 'canceled'
            ride.save()

            return JsonResponse({
                'success': True,
                'message': 'Carrera cancelada con éxito',
                'new_status': 'Cancelada',
                'new_status_color': 'danger'
            })

        else:
            return JsonResponse({'error': 'Estado inválido'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@login_required
def ride_detail(request, ride_id):
    try:
        # Obtener la carrera específica
        ride = get_object_or_404(Ride, id=ride_id)

        # Verificar permisos: admin, conductor asignado, cliente dueño, o conductor disponible (para aceptar)
        is_involved = (
            request.user.is_superuser or 
            request.user == ride.driver or 
            request.user == ride.customer
        )
        
        # Permitir ver si es un conductor y la carrera está solicitada (para aceptarla)
        if not is_involved and request.user.role == 'driver' and ride.status == 'requested':
            pass
        elif not is_involved:
            messages.error(request, 'No tiene permiso para ver esta carrera.')
            return redirect('available_rides')

        # Obtener la dirección de origen
        origin_address = ride.get_origin_address()

        # Obtener TODOS los destinos ordenados
        destinations = ride.destinations.all().order_by('order')
        
        # Preparar datos de destinos para el mapa (JSON serializable)
        destinations_data = []
        for dest in destinations:
            destinations_data.append({
                'lat': dest.destination_latitude,
                'lng': dest.destination_longitude,
                'address': dest.destination,
                'order': dest.order
            })

        # Coordenadas del cliente
        client_lat = None
        client_lng = None
        if ride.customer:
            try:
                taxi = ride.customer.taxi
                client_lat = taxi.latitude
                client_lng = taxi.longitude
            except AttributeError:
                pass

        # Coordenadas del conductor
        driver_lat = None
        driver_lng = None
        if ride.driver:
            try:
                taxi = ride.driver.taxi
                if taxi.latitude is not None and taxi.longitude is not None:
                    driver_lat = taxi.latitude
                    driver_lng = taxi.longitude
            except Taxi.DoesNotExist:
                pass

        # Lógica de Chat
        chat_history = []
        other_user_id = None
        other_user_name = None
        
        if ride.driver and ride.customer:
            if request.user == ride.customer:
                other_user = ride.driver
            elif request.user == ride.driver:
                other_user = ride.customer
            else:
                other_user = None
            
            if other_user:
                other_user_id = other_user.id
                other_user_name = other_user.get_full_name()
                from .models import ChatMessage
                from django.db.models import Q
                chat_history = ChatMessage.objects.filter(
                    Q(sender=request.user, recipient=other_user) | 
                    Q(sender=other_user, recipient=request.user)
                ).order_by('timestamp')

        context = {
            'ride': ride,
            'client_lat': client_lat,
            'client_lng': client_lng,
            'driver_lat': driver_lat,
            'driver_lng': driver_lng,
            'origin_address': origin_address,
            'destinations': destinations,
            'destinations_json': json.dumps(destinations_data),
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_API_KEY,
            'chat_history': chat_history,
            'other_user_id': other_user_id,
            'other_user_name': other_user_name,
        }

        return render(request, 'ride_detail_modern.html', context)

    except Ride.DoesNotExist:
        messages.error(request, 'Carrera no encontrada.')
        return redirect('available_rides')


@login_required
def driver_location_api(request, driver_id):
    """API para obtener la ubicación en tiempo real del conductor"""
    try:
        driver = AppUser.objects.get(id=driver_id, role='driver')
        taxi = Taxi.objects.filter(user=driver).first()
        
        if taxi and taxi.latitude and taxi.longitude:
            return JsonResponse({
                'success': True,
                'latitude': taxi.latitude,
                'longitude': taxi.longitude,
                'updated_at': taxi.updated_at.isoformat() if taxi.updated_at else None
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Ubicación no disponible'
            }, status=404)
    except AppUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Conductor no encontrado'
        }, status=404)


@login_required
def ride_status(request, ride_id):
    try:
        ride = Ride.objects.get(id=ride_id, customer=request.user)
        return render(request, 'ride_status.html', {'ride': ride})
    except Ride.DoesNotExist:
        messages.error(request, 'No se encontró la carrera.')
        return redirect('request_ride')

@login_required
def cancel_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)

    # Verificar si el usuario es el conductor asignado o el cliente que creó la carrera
    if request.user != ride.driver and request.user != ride.customer:
        messages.error(request, "No tiene permiso para cancelar esta carrera.")
        return redirect('ride_detail', ride_id=ride_id)

    # Cambiar el estado de la carrera a 'canceled'
    ride.status = 'canceled'
    ride.save()

    # Mensaje de éxito
    messages.success(request, "La carrera ha sido cancelada.")
    return redirect('ride_detail', ride_id=ride_id)


@login_required
def complete_ride(request, ride_id):
    ride = get_object_or_404(Ride, id=ride_id)

    # Verificar que el usuario sea el conductor asignado
    if request.user != ride.driver:
        messages.error(request, "No tiene permiso para completar esta carrera.")
        return redirect('ride_detail', ride_id=ride_id)

    # Cambiar el estado de la carrera
    ride.status = 'completed'
    ride.save()
    messages.success(request, "La carrera ha sido marcada como completada.")
    return redirect('available_rides')


@login_required
def get_google_maps_key(request):
    """
    Endpoint seguro para obtener la API key de Google Maps
    """
    return JsonResponse({'maps_api_key': settings.GOOGLE_MAPS_API_KEY})

def chat_room(request, room_name):
    return render(request, 'chat/room.html', {
        'room_name': room_name
    })

@login_required
def customer_rides(request):
    rides = Ride.objects.filter(customer=request.user).order_by('-created_at')
    return render(request, 'customer_rides.html', {'rides': rides})

@login_required
def driver_in_progress_rides(request):
    rides = Ride.objects.filter(driver=request.user).order_by('-created_at')
    return render(request, 'driver_in_progress_rides.html', {'rides': rides})



def check_new_rides(request):
    # Filtrar carreras nuevas que aún no han sido notificadas
    new_rides = Ride.objects.filter(status="requested", notified=False).order_by("id")

    if new_rides.exists():
        ride = new_rides.first()  # Tomar la primera nueva carrera

        # Marcar la carrera como notificada para evitar notificaciones repetidas
        Ride.objects.filter(id=ride.id).update(notified=True)

        return JsonResponse({
            "new_ride": True,
            "message": f"¡Nueva solicitud de taxi desde {ride.origin}!",
            "ride": {
                "id": ride.id,
                "origin": ride.origin,
                "destinations": [dest.destination for dest in ride.destinations.all()],
                "price": float(ride.price),  # Asegurar que el precio sea JSON serializable
                "status_display": ride.get_status_display(),
            }
        })

    return JsonResponse({"new_ride": False})

def admin_users(request):
    taxis = Taxi.objects.exclude(latitude__isnull=True, longitude__isnull=True)  # Solo taxistas con ubicación registrada
    return render(request, 'admin_users.html', {'taxis': taxis})

def taxis_ubicacion(request):
    taxis = Taxi.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    data = [
        {
            "name": taxi.user.get_full_name(),
            "latitude": taxi.latitude,
            "longitude": taxi.longitude,
            "plate": taxi.plate_number,
            "vehicle": taxi.vehicle_description
        }
        for taxi in taxis
    ]

    return JsonResponse(data, safe=False)



@csrf_exempt
def actualizar_ubicacion(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user = request.user  # Usuario autenticado (taxista)

        if not user.is_authenticated or user.role != 'driver':
            return JsonResponse({"error": "Acceso no autorizado"}, status=403)

        try:
            taxi = Taxi.objects.get(user=user)
            taxi.latitude = data.get("latitude")
            taxi.longitude = data.get("longitude")
            taxi.save()

            return JsonResponse({"message": "Ubicación actualizada", "latitude": taxi.latitude, "longitude": taxi.longitude})
        except Taxi.DoesNotExist:
            return JsonResponse({"error": "El taxista no tiene un taxi asignado"}, status=400)
    return JsonResponse({"error": "Método no permitido"}, status=405)


@login_required
def list_drivers(request):
    if request.user.role != 'admin':  # Solo permite acceso a administradores
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    drivers = AppUser.objects.filter(role='driver')
    return render(request, 'list_drivers.html', {'drivers': drivers})

@login_required
def delete_driver(request, user_id):
    if request.user.role != 'admin':  # Solo los administradores pueden eliminar
        messages.error(request, "No tienes permiso para realizar esta acción.")
        return redirect('home')

    driver = get_object_or_404(AppUser, id=user_id, role='driver')

    # Eliminar el taxi asociado si existe
    Taxi.objects.filter(user=driver).delete()

    # Eliminar el conductor
    driver.delete()

    messages.success(request, f'El conductor {driver.get_full_name()} ha sido eliminado.')
    return redirect('list_drivers')

@login_required
def comunicacion_conductores(request):
    # Verificar si el usuario es taxista o administrador
    if not (request.user.role == 'driver' or request.user.is_superuser):
        return JsonResponse({'error': 'Acceso no permitido'}, status=403)

    if request.user.is_superuser:
        context = {
            'GOOGLE_API_KEY': settings.GOOGLE_API_KEY
        }
        return render(request, 'comunicacion.html', context)
    else:
        # Obtener el ID del administrador (Central) para el chat
        admin_user = AppUser.objects.filter(is_superuser=True).first()
        
        # Obtener historial de chat
        chat_history = []
        if admin_user:
            from .models import ChatMessage
            from django.db.models import Q
            chat_history = ChatMessage.objects.filter(
                Q(sender=request.user, recipient=admin_user) | 
                Q(sender=admin_user, recipient=request.user)
            ).order_by('timestamp')

        context = {
            'admin_user_id': admin_user.id if admin_user else None,
            'chat_history': chat_history
        }
        return render(request, 'comunicacion_driver.html', context)


def ubicaciones_taxis(request):
    taxis = Taxi.objects.select_related('user').all()
    data = []
    
    for taxi in taxis:
        if taxi.user.role == 'driver':
            data.append({
                'id': taxi.user.id,
                'nombre': taxi.user.get_full_name(),
                'lat': taxi.latitude,
                'lng': taxi.longitude,
                'foto': taxi.user.profile_picture.url if taxi.user.profile_picture else '/media/default.jpg',
                'placa': taxi.plate_number,
                'descripcion': taxi.vehicle_description,
            })
            
    return JsonResponse({'taxis': data})

@csrf_exempt
@login_required
def actualizar_ubicacion_taxi(request):
    print("🔵 Vista llamada")
    print("Usuario:", request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Datos recibidos:", data)

            taxi = Taxi.objects.get(user=request.user)
            taxi.latitude = data.get('lat')
            taxi.longitude = data.get('lng')
            taxi.save()
            return JsonResponse({'status': 'ok'})
        except Taxi.DoesNotExist:
            print("❌ Taxi no encontrado")
            return JsonResponse({'status': 'error', 'message': 'Taxi no encontrado'}, status=404)
        except Exception as e:
            print("❌ Error general:", str(e))
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)


@login_required
def rate_ride(request, ride_id):
    """Calificar un viaje completado"""
    try:
        ride = get_object_or_404(Ride, id=ride_id, status='completed')
        
        # Verificar que el usuario puede calificar este viaje
        if request.user not in [ride.customer, ride.driver]:
            messages.error(request, "No tienes permiso para calificar este viaje.")
            return redirect('customer_dashboard' if request.user.role == 'customer' else 'driver_dashboard')
        
        if request.method == 'POST':
            rating_value = int(request.POST.get('rating'))
            comment = request.POST.get('comment', '')
            
            # Determinar quién califica a quién
            if request.user == ride.customer:
                rated_user = ride.driver
            else:
                rated_user = ride.customer
            
            # Crear o actualizar calificación
            rating, created = Rating.objects.get_or_create(
                ride=ride,
                rater=request.user,
                rated=rated_user,
                defaults={'rating': rating_value, 'comment': comment}
            )
            
            if not created:
                rating.rating = rating_value
                rating.comment = comment
                rating.save()
            
            messages.success(request, f"¡Gracias por calificar con {rating_value} estrellas! ⭐")
            return redirect('ride_detail', ride_id=ride.id)
        
        # Mostrar formulario de calificación
        context = {
            'ride': ride,
            'rated_user': ride.driver if request.user == ride.customer else ride.customer,
        }
        return render(request, 'rate_ride.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al calificar: {str(e)}")
        return redirect('customer_dashboard' if request.user.role == 'customer' else 'driver_dashboard')


@login_required
def user_ratings(request, user_id):
    """Ver calificaciones de un usuario"""
    try:
        user = get_object_or_404(AppUser, id=user_id)
        ratings = Rating.objects.filter(rated=user).order_by('-created_at')
        
        # Calcular promedio
        if ratings.exists():
            avg_rating = sum(r.rating for r in ratings) / len(ratings)
        else:
            avg_rating = 0
        
        context = {
            'rated_user': user,
            'ratings': ratings,
            'avg_rating': round(avg_rating, 1),
            'total_ratings': len(ratings),
        }
        return render(request, 'user_ratings.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al cargar calificaciones: {str(e)}")
        return redirect('home')

def offline_view(request):
    return render(request, 'offline.html')


@login_required
def chat_central(request):
    # Solo admin y conductores pueden entrar
    if not (request.user.is_superuser or request.user.role == 'driver'):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    drivers = AppUser.objects.filter(role='driver')
    admin_user = AppUser.objects.filter(is_superuser=True).first()

    context = {
        'drivers': drivers,
        'admin_user_id': admin_user.id if admin_user else None,
        'GOOGLE_API_KEY': settings.GOOGLE_API_KEY  # Para el mapa
    }
    return render(request, 'central_comunicacion.html', context)

@login_required
def get_chat_history(request, user_id):
    """API para obtener historial de chat con un usuario específico"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    from .models import ChatMessage, AppUser
    from django.db.models import Q
    
    other_user = get_object_or_404(AppUser, id=user_id)
    
    messages = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) | 
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')
    
    data = [{
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.get_full_name(),
        'message': msg.message,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'is_sent': msg.sender.id == request.user.id
    } for msg in messages]
    
    return JsonResponse({'messages': data})


# ============================================
# VISTAS DE WHATSAPP
# ============================================

@login_required
def whatsapp_panel(request):
    """Panel principal de WhatsApp"""
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')
    
    from .models import WhatsAppConversation, WhatsAppMessage, WhatsAppStats
    from datetime import date, timedelta
    from django.db.models import Count, Q
    
    # Estadísticas de hoy
    today = date.today()
    stats_today = WhatsAppStats.objects.filter(date=today).first()
    
    # Conversaciones activas
    active_conversations = WhatsAppConversation.objects.filter(
        status='active'
    ).order_by('-last_message_at')[:10]
    
    # Conversaciones recientes (últimas 24 horas)
    yesterday = timezone.now() - timedelta(days=1)
    recent_conversations = WhatsAppConversation.objects.filter(
        last_message_at__gte=yesterday
    ).order_by('-last_message_at')
    
    # Estadísticas de la última semana
    week_ago = today - timedelta(days=7)
    stats_week = WhatsAppStats.objects.filter(
        date__gte=week_ago
    ).order_by('date')
    
    context = {
        'stats_today': stats_today,
        'active_conversations': active_conversations,
        'recent_conversations': recent_conversations,
        'stats_week': stats_week,
        'total_conversations': WhatsAppConversation.objects.count(),
        'total_messages': WhatsAppMessage.objects.count(),
    }
    
    return render(request, 'whatsapp_panel.html', context)


@login_required
def whatsapp_conversation_detail(request, conversation_id):
    """Detalle de una conversación de WhatsApp"""
    if not request.user.is_superuser:
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')
    
    from .models import WhatsAppConversation
    
    conversation = get_object_or_404(WhatsAppConversation, id=conversation_id)
    messages_list = conversation.messages.all().order_by('created_at')
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
    }
    
    return render(request, 'whatsapp_conversation_detail.html', context)


@login_required
@csrf_exempt
def whatsapp_send_message(request):
    """Enviar mensaje manual de WhatsApp"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    if request.method == 'POST':
        from .whatsapp_agent_ai import whatsapp_agent_ai
        
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return JsonResponse({'error': 'Faltan datos'}, status=400)
        
        success = whatsapp_agent_ai.enviar_mensaje(phone_number, message)
        
        if success:
            return JsonResponse({'success': True, 'message': 'Mensaje enviado'})
        else:
            return JsonResponse({'error': 'Error al enviar mensaje'}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


@login_required
def whatsapp_stats_api(request):
    """API para obtener estadísticas de WhatsApp"""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    from .models import WhatsAppStats, WhatsAppConversation
    from datetime import date, timedelta
    
    today = date.today()
    stats_today = WhatsAppStats.objects.filter(date=today).first()
    
    # Conversaciones por estado
    conversations_by_status = WhatsAppConversation.objects.values('status').annotate(
        count=Count('id')
    )
    
    data = {
        'today': {
            'total_messages': stats_today.total_messages if stats_today else 0,
            'incoming_messages': stats_today.incoming_messages if stats_today else 0,
            'outgoing_messages': stats_today.outgoing_messages if stats_today else 0,
            'new_conversations': stats_today.new_conversations if stats_today else 0,
            'active_conversations': stats_today.active_conversations if stats_today else 0,
            'rides_requested': stats_today.rides_requested if stats_today else 0,
        },
        'conversations_by_status': list(conversations_by_status),
    }


# ============================================
# NOTIFICACIONES PWA PUSH
# ============================================

def enviar_notificacion_pwa_conductor(conductor, titulo, mensaje, datos=None):
    """
    Envía una notificación PWA push a un conductor
    
    Args:
        conductor: Usuario conductor (AppUser)
        titulo: Título de la notificación
        mensaje: Cuerpo del mensaje
        datos: Datos adicionales (dict)
    """
    try:
        # Por ahora, usamos WebSockets para notificar
        # En el futuro, implementar Web Push API real con pywebpush
        
        channel_layer = get_channel_layer()
        
        notification_data = {
            'type': 'nueva_carrera_notification',
            'title': titulo,
            'body': mensaje,
            'data': datos or {}
        }
        
        # Enviar a través del canal de audio/conductores
        async_to_sync(channel_layer.group_send)(
            'audio_conductores',
            {
                'type': 'nueva_carrera',
                'notification': notification_data
            }
        )
        
        logger.info(f"✅ Notificación PWA enviada a conductores")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al enviar notificación PWA: {e}")
        return False


@login_required
def debug_notifications(request):
    """
    Página de debug para notificaciones push
    """
    return render(request, 'debug_notifications.html')
