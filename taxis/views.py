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
from rest_framework.decorators import api_view
from django.db import models
from django.db.models import Count, Q
from .models import Taxi, TaxiRoute, Ride, RideDestination, AppUser, ConversacionTelegram, Rating
from django.contrib.auth import login, logout
from .forms import CustomerRegistrationForm,CustomerProfileForm, DriverProfileForm, TaxiForm, TaxiRouteForm, RideFilterForm, DriverRegistrationForm, AdminProfileForm
#from django.contrib.auth.forms import DriverRegistrationForm, CustomerRegistrationForm
from django.contrib.auth.decorators import login_required
from .decorators import organization_admin_required
from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.cache import cache
#from taxis.views import telegram_webhook  # cambia "tu_app" por el nombre real de tu app

# Logger
logger = logging.getLogger(__name__)

# Cloudinary (opcional, para subir archivos)
try:
    import cloudinary
    import cloudinary.uploader
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("Cloudinary no está instalado. La funcionalidad de subir archivos no estará disponible.")

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


# ============================================
# REGISTRO CON CÓDIGO QR (MULTI-TENANT)
# ============================================

def register_with_code(request):
    """
    Vista de registro que acepta un código de invitación QR.
    URL: /register/?code=TAXI-ABC123
    """
    from .models import InvitationCode
    from .forms import DriverRegistrationForm, CustomerRegistrationForm
    
    invitation_code = None
    code_param = request.GET.get('code', '').strip()
    error_message = None
    
    # Validar código de invitación si se proporciona
    if code_param:
        try:
            invitation_code = InvitationCode.objects.get(code=code_param)
            is_valid, message = invitation_code.is_valid()
            
            if not is_valid:
                error_message = f"Código de invitación {message.lower()}"
                invitation_code = None
        except InvitationCode.DoesNotExist:
            error_message = "Código de invitación no válido"
            invitation_code = None
    
    # Determinar qué formulario usar
    if invitation_code:
        if invitation_code.role == 'driver':
            FormClass = DriverRegistrationForm
        else:
            FormClass = CustomerRegistrationForm
    else:
        # Sin código, mostrar formulario genérico de cliente
        FormClass = CustomerRegistrationForm
    
    if request.method == 'POST':
        form = FormClass(request.POST, request.FILES)
        
        if form.is_valid():
            user = form.save(commit=False)
            
            # Asignar organización y rol del código de invitación
            if invitation_code:
                user.organization = invitation_code.organization
                user.role = invitation_code.role
                
                # Si es conductor, marcar como pendiente de aprobación
                if invitation_code.role == 'driver':
                    user.driver_status = 'pending'
            
            user.save()
            
            # Incrementar contador de usos del código
            if invitation_code:
                invitation_code.use()
            
            # Iniciar sesión automáticamente
            login(request, user)
            
            # Mensaje de bienvenida personalizado
            if invitation_code:
                messages.success(
                    request,
                    f'¡Bienvenido a {invitation_code.organization.name}! '
                    f'Tu cuenta de {invitation_code.get_role_display()} ha sido creada exitosamente.'
                )
                
                if invitation_code.role == 'driver':
                    messages.info(
                        request,
                        'Tu cuenta está pendiente de aprobación por un administrador. '
                        'Te notificaremos cuando sea aprobada.'
                    )
                    return redirect('driver_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                messages.success(request, '¡Cuenta creada exitosamente!')
                return redirect('customer_dashboard')
        else:
            print(form.errors)  # Debug
    else:
        form = FormClass()
    
    context = {
        'form': form,
        'invitation_code': invitation_code,
        'error_message': error_message,
        'code_param': code_param,
    }
    
    return render(request, 'registration/register_with_code.html', context)


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
        taxi = getattr(user, 'taxi', None)
        context['taxi'] = taxi
        
        # Estadísticas del conductor
        rides_queryset = user.rides_as_driver.all()
        total_rides = rides_queryset.count()
        completed_rides = rides_queryset.filter(status='completed').count()
        active_rides = rides_queryset.filter(status__in=['accepted', 'in_progress']).count()
        canceled_rides = rides_queryset.filter(status='canceled').count()
        
        # Calcular ganancias
        from django.db.models import Sum
        total_earnings = rides_queryset.filter(
            status='completed',
            price__isnull=False
        ).aggregate(total=Sum('price'))['total'] or 0
        
        context.update({
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'active_rides': active_rides,
            'canceled_rides': canceled_rides,
            'total_earnings': total_earnings,
            'has_location': taxi and taxi.latitude and taxi.longitude if taxi else False,
        })
    elif user.role == 'customer':
        # Estadísticas del cliente
        rides_queryset = user.rides_as_customer.all()
        total_rides = rides_queryset.count()
        completed_rides = rides_queryset.filter(status='completed').count()
        active_rides = rides_queryset.filter(status__in=['requested', 'accepted', 'in_progress']).count()
        context.update({
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'active_rides': active_rides,
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
    
    # ✅ MULTI-TENANT: Base queryset filtrado por organización
    if request.user.organization:
        rides_queryset = Ride.objects.filter(organization=request.user.organization)
    else:
        rides_queryset = Ride.objects.none()
    
    # Obtener estadísticas del conductor
    total_rides = rides_queryset.filter(driver=request.user).count()
    completed_rides = rides_queryset.filter(driver=request.user, status='completed').count()
    canceled_rides = rides_queryset.filter(driver=request.user, status='canceled').count()
    active_rides_count = rides_queryset.filter(
        driver=request.user, 
        status__in=['accepted', 'in_progress']
    ).count()
    
    # Calcular ganancias (basado en precio de carreras completadas)
    from django.db.models import Sum
    today = now().date()
    
    # Ganancias del día
    today_earnings = rides_queryset.filter(
        driver=request.user, 
        status='completed',
        created_at__date=today,
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Ganancias del mes
    month_earnings = rides_queryset.filter(
        driver=request.user, 
        status='completed',
        created_at__year=today.year,
        created_at__month=today.month,
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Ganancias totales
    total_earnings = rides_queryset.filter(
        driver=request.user, 
        status='completed',
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Carreras de hoy
    today_rides_count = rides_queryset.filter(
        driver=request.user, 
        status='completed',
        created_at__date=today
    ).count()
    
    # ✅ Obtener carreras disponibles (sin conductor asignado, de su organización)
    available_rides_list = rides_queryset.filter(
        status='requested',
        driver__isnull=True
    ).select_related('customer').order_by('-created_at')[:10]
    
    # Obtener carreras activas del conductor
    active_rides_list = rides_queryset.filter(
        driver=request.user,
        status__in=['accepted', 'in_progress']
    ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
    
    # Obtener últimas carreras completadas
    recent_completed = rides_queryset.filter(
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
    
    # Obtener negociaciones del cliente
    from .models import PriceNegotiation
    my_negotiations = PriceNegotiation.objects.filter(
        customer=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'active_rides': active_rides,
        'recent_rides': recent_rides,
        'my_negotiations': my_negotiations,  # 💰 NUEVO
    }
    
    return render(request, 'customer_dashboard.html', context)

@organization_admin_required
def admin_dashboard(request):
    """
    Dashboard para administradores de cooperativa.
    SIEMPRE filtra datos por organización del admin.
    Super admins son redirigidos a /superadmin/dashboard/
    """
    from django.db.models import Sum, Avg
    from django.utils import timezone
    from django.shortcuts import redirect
    
    # Si es super admin, redirigir a su dashboard
    if request.user.is_superuser:
        return redirect('superadmin_dashboard')
    
    # Validar que el admin tenga organización asignada
    organization = request.user.organization
    if not organization:
        messages.error(request, 'No tienes una organización asignada. Contacta al super administrador.')
        return redirect('login')
    
    # SIEMPRE filtrar por organización del admin
    users_qs = AppUser.objects.filter(organization=organization)
    rides_qs = Ride.objects.filter(organization=organization)
    taxis_qs = Taxi.objects.filter(user__organization=organization)
    ratings_qs = Rating.objects.filter(ride__organization=organization)
    
    # Estadísticas generales
    total_users = users_qs.count()
    total_drivers = users_qs.filter(role='driver').count()
    total_customers = users_qs.filter(role='customer').count()
    total_rides = rides_qs.count()
    
    # Carreras por estado
    requested_rides = rides_qs.filter(status='requested').count()
    accepted_rides = rides_qs.filter(status='accepted').count()
    in_progress_rides = rides_qs.filter(status='in_progress').count()
    completed_rides = rides_qs.filter(status='completed').count()
    canceled_rides = rides_qs.filter(status='canceled').count()
    
    # Ingresos
    total_revenue = rides_qs.filter(status='completed', price__isnull=False).aggregate(
        total=Sum('price')
    )['total'] or 0
    
    # Carreras de hoy
    today = timezone.now().date()
    today_rides = rides_qs.filter(created_at__date=today).count()
    today_revenue = rides_qs.filter(
        status='completed', 
        price__isnull=False,
        created_at__date=today
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Conductores activos (con ubicación)
    active_drivers = taxis_qs.exclude(
        latitude__isnull=True, 
        longitude__isnull=True
    ).count()
    
    # Carreras recientes
    recent_rides = rides_qs.select_related('customer', 'driver').order_by('-created_at')[:10]
    
    # Calificaciones promedio
    try:
        avg_rating = ratings_qs.aggregate(avg=Avg('rating'))['avg'] or 0
        total_ratings = ratings_qs.count()
    except:
        avg_rating = 0
        total_ratings = 0
    
    # Negociaciones de precio pendientes (solo de esta organización)
    from .models import PriceNegotiation
    pending_negotiations = PriceNegotiation.objects.filter(
        organization=organization,
        status='pending'
    ).select_related('customer').order_by('-created_at')[:10]
    
    context = {
        'organization': organization,  # Para mostrar nombre de la cooperativa
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
        'pending_negotiations': pending_negotiations,
    }
    
    return render(request, 'admin_dashboard.html', context)


@login_required
def superadmin_dashboard(request):
    """
    Dashboard exclusivo para Super Admin (dueño del sistema).
    Muestra estadísticas globales y comparativas entre cooperativas.
    """
    from django.db.models import Sum, Avg, Count
    from django.utils import timezone
    from django.shortcuts import redirect
    
    # Solo super admins pueden acceder
    if not request.user.is_superuser:
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('admin_dashboard')
    
    # Estadísticas globales (todas las organizaciones)
    total_organizations = Organization.objects.count()
    active_organizations = Organization.objects.filter(status='active').count()
    trial_organizations = Organization.objects.filter(status='trial').count()
    
    total_users = AppUser.objects.count()
    total_drivers = AppUser.objects.filter(role='driver').count()
    total_customers = AppUser.objects.filter(role='customer').count()
    total_admins = AppUser.objects.filter(role='admin').count()
    
    total_rides = Ride.objects.count()
    completed_rides = Ride.objects.filter(status='completed').count()
    in_progress_rides = Ride.objects.filter(status='in_progress').count()
    
    # Ingresos totales
    total_revenue = Ride.objects.filter(
        status='completed',
        price__isnull=False
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Comisiones totales
    total_commissions = Ride.objects.filter(
        status='completed',
        commission_amount__isnull=False
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    # Estadísticas de hoy
    today = timezone.now().date()
    today_rides = Ride.objects.filter(created_at__date=today).count()
    today_revenue = Ride.objects.filter(
        status='completed',
        price__isnull=False,
        created_at__date=today
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Estadísticas por organización (top 10)
    org_stats = []
    for org in Organization.objects.all().order_by('-created_at')[:10]:
        org_drivers = AppUser.objects.filter(role='driver', organization=org).count()
        org_customers = AppUser.objects.filter(role='customer', organization=org).count()
        org_rides = Ride.objects.filter(organization=org).count()
        org_revenue = Ride.objects.filter(
            organization=org,
            status='completed',
            price__isnull=False
        ).aggregate(total=Sum('price'))['total'] or 0
        org_commissions = Ride.objects.filter(
            organization=org,
            status='completed',
            commission_amount__isnull=False
        ).aggregate(total=Sum('commission_amount'))['total'] or 0
        
        org_stats.append({
            'organization': org,
            'drivers': org_drivers,
            'customers': org_customers,
            'rides': org_rides,
            'revenue': org_revenue,
            'commissions': org_commissions,
        })
    
    # Organizaciones recientes
    recent_organizations = Organization.objects.order_by('-created_at')[:5]
    
    context = {
        'total_organizations': total_organizations,
        'active_organizations': active_organizations,
        'trial_organizations': trial_organizations,
        'total_users': total_users,
        'total_drivers': total_drivers,
        'total_customers': total_customers,
        'total_admins': total_admins,
        'total_rides': total_rides,
        'completed_rides': completed_rides,
        'in_progress_rides': in_progress_rides,
        'total_revenue': total_revenue,
        'total_commissions': total_commissions,
        'today_rides': today_rides,
        'today_revenue': today_revenue,
        'org_stats': org_stats,
        'recent_organizations': recent_organizations,
    }
    
    return render(request, 'superadmin_dashboard.html', context)


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
        sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'service-worker.js')
    
    if not os.path.exists(sw_path):
        sw_path = os.path.join(settings.BASE_DIR, 'taxis', 'static', 'js', 'service-worker.js')
        
    if os.path.exists(sw_path):
        with open(sw_path, 'rb') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/javascript')
        # Allow the service worker to control the entire domain
        response['Service-Worker-Allowed'] = '/'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    else:
        return HttpResponse("Service Worker not found", status=404)


@login_required
def test_notifications(request):
    """
    Vista de prueba para verificar el funcionamiento de las notificaciones push
    """
    return render(request, 'test_notifications.html')


def clear_cache(request):
    """
    Vista para limpiar la caché del navegador y Service Workers
    """
    return render(request, 'clear_cache.html')


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
                from decimal import Decimal
                
                origin_lat = float(origin_lat)
                origin_lng = float(origin_lng)
                price = Decimal(str(price))  # Convertir a Decimal para evitar errores de tipo

                # ✅ Si el origen está vacío o es inválido, obtener dirección desde coordenadas
                if not origin or origin.strip() == '' or 'undefined' in origin.lower():
                    try:
                        origin = obtener_direccion_google(origin_lat, origin_lng, settings.GOOGLE_API_KEY)
                        if not origin:
                            origin = f"Lat: {origin_lat}, Lng: {origin_lng}"
                    except Exception as e:
                        logger.warning(f"No se pudo obtener dirección de origen: {e}")
                        origin = f"Lat: {origin_lat}, Lng: {origin_lng}"

                # ✅ MULTI-TENANT: Asignar organización del cliente
                ride = Ride.objects.create(
                    customer=request.user,
                    organization=request.user.organization,  # Asignar organización
                    origin=origin,
                    origin_latitude=origin_lat,
                    origin_longitude=origin_lng,
                    price=price,
                    status='requested',
                )
                
                # ✅ Calcular comisión automáticamente
                if ride.organization and ride.price:
                    commission_rate = ride.organization.commission_rate / Decimal('100')
                    ride.commission_amount = ride.price * commission_rate
                    ride.save(update_fields=['commission_amount'])

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
    if not request.user.is_superuser and request.user.role not in ['driver', 'admin']:
        return JsonResponse({'error': 'Acceso no permitido'}, status=403)

    # ✅ MULTI-TENANT: Filtrar por organización
    if request.user.is_superuser:
        # Super admin ve todas las carreras
        rides = Ride.objects.filter(status='requested').order_by('created_at')
    elif request.user.organization:
        # Conductor ve solo carreras de su organización
        rides = Ride.objects.filter(
            status='requested',
            organization=request.user.organization
        ).order_by('created_at')
    else:
        # Usuario sin organización no ve nada
        rides = Ride.objects.none()

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
def active_rides(request):
    """Vista para mostrar carreras activas (accepted o in_progress)"""
    if not request.user.is_superuser and request.user.role != 'admin':
        return JsonResponse({'error': 'Acceso no permitido'}, status=403)
    
    # Obtener carreras activas (aceptadas o en progreso)
    rides = Ride.objects.filter(
        status__in=['accepted', 'in_progress']
    ).select_related('driver', 'customer').prefetch_related('destinations').order_by('-created_at')
    
    return render(request, 'active_rides.html', {'rides': rides})



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

        # Verificar si el usuario ya calificó este viaje
        user_rating = None
        has_rated = False
        if ride.status == 'completed':
            from .models import Rating
            user_rating = Rating.objects.filter(
                ride=ride,
                rater=request.user
            ).first()
            has_rated = user_rating is not None
        
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
            'has_rated': has_rated,
            'user_rating': user_rating,
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
    
    # Verificar que la carrera no esté completada
    if ride.status == 'completed':
        messages.error(request, "No se puede cancelar una carrera completada.")
        return redirect('ride_detail', ride_id=ride_id)
    
    # Verificar que la carrera no esté ya cancelada
    if ride.status == 'canceled':
        messages.warning(request, "Esta carrera ya está cancelada.")
        return redirect('ride_detail', ride_id=ride_id)

    # Cambiar el estado de la carrera a 'canceled'
    ride.status = 'canceled'
    
    # Si había un conductor asignado, liberarlo
    if ride.driver:
        ride.driver = None
    
    ride.save()

    # Mensaje de éxito según quién canceló
    if request.user == ride.customer:
        messages.success(request, "Has cancelado la carrera exitosamente.")
    else:
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
    try:
        taxis = Taxi.objects.exclude(latitude__isnull=True, longitude__isnull=True)

        data = []
        for taxi in taxis:
            try:
                # Obtener teléfono de manera segura
                telefono = 'N/A'
                if hasattr(taxi.user, 'phone_number'):
                    telefono = taxi.user.phone_number or 'N/A'
                elif hasattr(taxi.user, 'phone'):
                    telefono = taxi.user.phone or 'N/A'
                
                taxi_data = {
                    "id": taxi.id,
                    "username": taxi.user.username,  # 🔑 Agregar username para actualizaciones de ubicación
                    "nombre_conductor": taxi.user.get_full_name() or taxi.user.username,
                    "latitude": float(taxi.latitude) if taxi.latitude else 0.0,
                    "longitude": float(taxi.longitude) if taxi.longitude else 0.0,
                    "placa": taxi.plate_number or 'N/A',
                    "vehiculo": taxi.vehicle_description or 'N/A',
                    "disponible": getattr(taxi, 'is_available', True),
                    "telefono": telefono
                }
                data.append(taxi_data)
            except Exception as e:
                print(f"Error procesando taxi {taxi.id}: {e}")
                continue

        return JsonResponse(data, safe=False)
        
    except Exception as e:
        print(f"Error en taxis_ubicacion: {e}")
        return JsonResponse([], safe=False)



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

    # Obtener parámetros de búsqueda y filtrado
    search_query = request.GET.get('search', '').strip()
    filter_status = request.GET.get('status', 'all')  # all, online, offline
    filter_vehicle = request.GET.get('vehicle', 'all')  # all, with_vehicle, without_vehicle
    
    # Obtener conductores con información relacionada
    drivers = AppUser.objects.filter(role='driver').select_related('taxi').prefetch_related('rides_as_driver')
    
    # Aplicar búsqueda
    if search_query:
        drivers = drivers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(taxi__plate_number__icontains=search_query)
        )
    
    # Aplicar filtro de estado (ubicación)
    if filter_status == 'online':
        drivers = drivers.filter(taxi__latitude__isnull=False, taxi__longitude__isnull=False)
    elif filter_status == 'offline':
        drivers = drivers.filter(
            Q(taxi__latitude__isnull=True) | Q(taxi__longitude__isnull=True) | Q(taxi__isnull=True)
        )
    
    # Aplicar filtro de vehículo
    if filter_vehicle == 'with_vehicle':
        drivers = drivers.filter(taxi__isnull=False)
    elif filter_vehicle == 'without_vehicle':
        drivers = drivers.filter(taxi__isnull=True)
    
    # Calcular estadísticas (antes de paginación)
    total_drivers_all = AppUser.objects.filter(role='driver').count()
    total_drivers = drivers.count()
    drivers_with_taxi = AppUser.objects.filter(role='driver', taxi__isnull=False).count()
    drivers_with_location = AppUser.objects.filter(
        role='driver', 
        taxi__latitude__isnull=False, 
        taxi__longitude__isnull=False
    ).count()
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(drivers, 12)  # 12 conductores por página
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.get_page(page_number)
    except:
        page_obj = paginator.get_page(1)
    
    # Agregar información adicional a cada conductor
    from django.db.models import Avg, Count
    drivers_list = []
    for driver in page_obj:
        taxi = getattr(driver, 'taxi', None)
        # Usar rides_as_driver que es el related_name definido en el modelo Ride
        rides_queryset = driver.rides_as_driver.all()
        total_rides = rides_queryset.count()
        completed_rides = rides_queryset.filter(status='completed').count()
        active_rides = rides_queryset.filter(status__in=['accepted', 'in_progress']).count()
        
        # Calcular calificaciones
        from .models import Rating
        ratings_stats = Rating.objects.filter(rated=driver).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('id')
        )
        avg_rating = ratings_stats['avg_rating'] or 0
        total_ratings = ratings_stats['total_ratings'] or 0
        
        drivers_list.append({
            'driver': driver,
            'taxi': taxi,
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'active_rides': active_rides,
            'has_location': taxi and taxi.latitude and taxi.longitude if taxi else False,
            'avg_rating': round(avg_rating, 1) if avg_rating else 0,
            'total_ratings': total_ratings,
        })
    
    context = {
        'drivers': drivers_list,
        'page_obj': page_obj,
        'total_drivers': total_drivers,
        'total_drivers_all': total_drivers_all,
        'drivers_with_taxi': drivers_with_taxi,
        'drivers_with_location': drivers_with_location,
        'search_query': search_query,
        'filter_status': filter_status,
        'filter_vehicle': filter_vehicle,
    }
    
    return render(request, 'list_drivers.html', context)

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
    # ✅ MULTI-TENANT: Filtrar taxis por organización
    if request.user.is_authenticated:
        if request.user.is_superuser:
            # Super admin ve TODOS los taxis
            taxis = Taxi.objects.select_related('user').all()
        elif request.user.role == 'admin' and request.user.organization:
            # Admin ve solo taxis de SU organización
            taxis = Taxi.objects.select_related('user').filter(user__organization=request.user.organization)
        else:
            # Otros usuarios no ven nada
            taxis = Taxi.objects.none()
    else:
        # Usuario no autenticado no ve nada
        taxis = Taxi.objects.none()
    
    data = []
    
    for taxi in taxis:
        if taxi.user.role == 'driver':
            data.append({
                'id': taxi.user.id,
                'nombre': taxi.user.get_full_name(),
                'lat': taxi.latitude,
                'lng': taxi.longitude,
                # En Railway normalmente no se sirve /media/ (no hay storage persistente).
                # Usar una imagen estática por defecto para evitar 404.
                'foto': taxi.user.profile_picture.url if taxi.user.profile_picture else '/static/imagenes/logo1.png',
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
    if not (request.user.is_superuser or request.user.role in ['driver', 'admin']):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect('home')

    # ✅ MULTI-TENANT: Filtrar conductores por organización
    if request.user.is_superuser:
        # Super admin ve TODOS los conductores
        drivers = AppUser.objects.filter(role='driver')
    elif request.user.role == 'admin' and request.user.organization:
        # Admin ve solo conductores de SU organización
        drivers = AppUser.objects.filter(role='driver', organization=request.user.organization)
    else:
        # Usuario sin organización no ve nada
        drivers = AppUser.objects.none()
    
    admin_user = AppUser.objects.filter(is_superuser=True).first()

    # Pre-cargar historial de chat para cada conductor
    from .models import ChatMessage
    from django.db.models import Q, Max
    
    drivers_with_history = []
    for driver in drivers:
        # Obtener historial de chat entre el admin y este conductor
        chat_history = []
        last_message = None
        
        # Obtener los IDs de los mensajes más recientes para optimizar la consulta
        if admin_user:
            # Primero obtener el último mensaje para cada par de usuarios
            last_messages = ChatMessage.objects.filter(
                Q(sender=request.user, recipient=driver) | 
                Q(sender=driver, recipient=request.user)
            ).values('sender', 'recipient').annotate(
                max_timestamp=Max('timestamp')
            )
            
            # Obtener los mensajes completos para los timestamps máximos
            if last_messages.exists():
                last_message = ChatMessage.objects.filter(
                    Q(sender=request.user, recipient=driver) | 
                    Q(sender=driver, recipient=request.user)
                ).order_by('-timestamp').first()
            
            # Obtener los últimos 50 mensajes para el historial
            chat_history = ChatMessage.objects.filter(
                Q(sender=request.user, recipient=driver) | 
                Q(sender=driver, recipient=request.user)
            ).select_related('sender', 'recipient').order_by('timestamp')[:50]
        
        drivers_with_history.append({
            'driver': driver,
            'chat_history': chat_history,
            'last_message': last_message
        })

    import time
    import random
    import datetime
    
    # Timestamp súper único con múltiples componentes para forzar recarga
    # Timestamp único que cambia en cada request para evitar cache
    unique_timestamp = f"{int(time.time())}{random.randint(10000,99999)}{datetime.datetime.now().microsecond}"
    
    context = {
        'drivers': drivers,
        'drivers_with_history': drivers_with_history,  # Nueva lista con historial pre-cargado
        'admin_user_id': admin_user.id if admin_user else None,
        'GOOGLE_API_KEY': settings.GOOGLE_API_KEY,  # Para el mapa
        'timestamp': unique_timestamp,  # Timestamp súper único
        'cache_bust': f"v{int(time.time())}"  # Cache buster adicional
    }
    return render(request, 'central_comunicacion.html', context)

def get_chat_history(request, user_id):
    """API para obtener historial de chat con un usuario específico"""
    from .models import ChatMessage, AppUser
    from django.db.models import Q
    from rest_framework.authtoken.models import Token
    
    # Autenticación por token (para app móvil)
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            request.user = token.user
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Token inválido'}, status=401)
    elif not request.user.is_authenticated:
        return JsonResponse({'error': 'No autenticado'}, status=401)
    
    print(f"[CHAT_HISTORY] Petición recibida: user_id={user_id}, request.user={request.user.id}, is_superuser={request.user.is_superuser}")
    
    # ✅ MODIFICADO: Permitir que cualquier usuario autenticado vea el historial con otro usuario
    # Ya no se valida que user_id sea el mismo que request.user.id
    # El historial siempre será entre request.user y other_user
    
    other_user = get_object_or_404(AppUser, id=user_id)
    print(f"[CHAT_HISTORY] Usuario encontrado: {other_user.get_full_name() or other_user.username} (ID: {other_user.id})")
    
    messages = ChatMessage.objects.filter(
        Q(sender=request.user, recipient=other_user) | 
        Q(sender=other_user, recipient=request.user)
    ).order_by('timestamp')
    
    print(f"[CHAT_HISTORY] Mensajes encontrados: {messages.count()}")
    
    data = [{
        'sender_id': msg.sender.id,
        'sender_name': msg.sender.get_full_name() or msg.sender.username,
        'message': msg.message,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'is_sent': msg.sender.id == request.user.id,
        # Campos de media
        'message_type': msg.message_type,
        'media_url': msg.media_url,
        'thumbnail_url': msg.thumbnail_url,
        'metadata': msg.metadata or {},
    } for msg in messages]
    
    print(f"[CHAT_HISTORY] ✅ Retornando {len(data)} mensajes")
    return JsonResponse({'messages': data})


@csrf_exempt
def get_driver_chat_history(request, driver_id):
    """API para que los conductores obtengan su historial de chat con el admin"""
    from .models import ChatMessage, AppUser
    from django.db.models import Q
    
    try:
        # Intentar obtener el conductor por ID numérico o username
        driver = None
        try:
            # Primero intentar como ID numérico
            if isinstance(driver_id, int) or (isinstance(driver_id, str) and driver_id.isdigit()):
                driver = AppUser.objects.get(id=int(driver_id))
            else:
                # Intentar como username
                driver = AppUser.objects.get(username=driver_id)
        except AppUser.DoesNotExist:
            return JsonResponse({'error': f'Conductor "{driver_id}" no encontrado'}, status=404)
        
        admin = AppUser.objects.filter(is_superuser=True).first()
        
        if not admin:
            return JsonResponse({'error': 'Admin no encontrado'}, status=404)
        
        # Obtener mensajes entre el conductor y el admin
        messages = ChatMessage.objects.filter(
            Q(sender=driver, recipient=admin) | 
            Q(sender=admin, recipient=driver)
        ).order_by('timestamp')
        
        print(f"📜 Cargando historial de chat: {driver.username} (ID: {driver.id}) <-> Admin (ID: {admin.id})")
        print(f"   Total mensajes encontrados: {messages.count()}")
        
        data = [{
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'is_sent': msg.sender.id == driver.id,
            # Campos de media
            'message_type': msg.message_type,
            'media_url': msg.media_url,
            'thumbnail_url': msg.thumbnail_url,
            'metadata': msg.metadata or {},
        } for msg in messages]
        
        return JsonResponse({'messages': data})
        
    except Exception as e:
        print(f"❌ Error en get_driver_chat_history: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def upload_chat_media(request):
    """
    Endpoint para subir imágenes/videos a Cloudinary para el chat
    
    POST /api/chat/upload/
    Content-Type: multipart/form-data
    
    Campos:
    - file: Archivo (imagen o video)
    - message_type: 'image' o 'video' (opcional, se detecta automáticamente)
    
    Nota: Usa @csrf_exempt porque el token CSRF se envía en el header X-CSRFToken
    """
    try:
        # Verificar que hay un archivo
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó ningún archivo'
            }, status=400)
        
        file = request.FILES['file']
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return JsonResponse({
                'success': False,
                'error': f'El archivo es demasiado grande. Máximo: {max_size / (1024*1024):.1f}MB'
            }, status=400)
        
        # Detectar tipo de archivo
        file_type = request.POST.get('message_type', '').lower()
        if not file_type:
            # Detectar automáticamente por extensión
            file_name = file.name.lower()
            if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                file_type = 'image'
            elif any(file_name.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi']):
                file_type = 'video'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Tipo de archivo no soportado. Use imágenes (jpg, png, gif) o videos (mp4, webm)'
                }, status=400)
        
        # Verificar que Cloudinary esté disponible
        if not CLOUDINARY_AVAILABLE:
            return JsonResponse({
                'success': False,
                'error': 'Servicio de subida de archivos no disponible. Contacte al administrador.'
            }, status=503)
        
        # Configurar Cloudinary
        cloudinary.config(
            cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', None),
            api_key=getattr(settings, 'CLOUDINARY_API_KEY', None),
            api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', None)
        )
        
        # Subir a Cloudinary
        upload_options = {
            'folder': 'chat_media',
            'resource_type': 'auto',
        }
        
        # Para videos, generar thumbnail
        if file_type == 'video':
            upload_options['eager'] = [
                {'width': 300, 'height': 300, 'crop': 'fill', 'format': 'jpg'}
            ]
        
        result = cloudinary.uploader.upload(
            file,
            **upload_options
        )
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'media_url': result['secure_url'],
            'message_type': file_type,
            'metadata': {
                'width': result.get('width'),
                'height': result.get('height'),
                'format': result.get('format'),
                'size': result.get('bytes'),
                'duration': result.get('duration'),
            }
        }
        
        # Agregar thumbnail si es video
        if file_type == 'video' and 'eager' in result and len(result['eager']) > 0:
            response_data['thumbnail_url'] = result['eager'][0]['secure_url']
        
        return JsonResponse(response_data, status=200)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'Error subiendo archivo: {str(e)}'
        }, status=500)


# ============================================
# VISTAS DE WHATSAPP
# ============================================

@login_required
def whatsapp_panel(request):
    """Panel principal de WhatsApp"""
    if not (request.user.is_superuser or request.user.role == 'admin'):
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
        # 1. Enviar notificación push real con Web Push API
        from .push_notifications import send_push_notification
        
        try:
            send_push_notification(
                user=conductor,
                title=titulo,
                body=mensaje,
                data=datos,
                icon='/static/imagenes/icon-192x192.png',
                badge='/static/imagenes/icon-96x96.png'
            )
            logger.info(f"✅ Push notification enviada a {conductor.username}")
        except Exception as e:
            logger.warning(f"⚠️ Error al enviar push notification: {e}")
        
        # 2. También enviar vía WebSocket (para usuarios conectados en tiempo real)
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
        
        logger.info(f"✅ Notificación PWA enviada a conductores (Push + WebSocket)")
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
@csrf_exempt
@api_view(['POST'])
def register_fcm_token_view(request):
    """
    API endpoint para registrar tokens FCM desde Android/iOS
    
    POST /api/register-fcm-token/
    Body: {
        "token": "fcm_token_string",
        "platform": "android",  // opcional: android, ios, web
        "device_id": "device_unique_id"  // opcional
    }
    """
    from .fcm_notifications import register_fcm_token
    from .models import AppUser
    
    try:
        import json
        
        # Obtener datos del request - SIEMPRE parsear JSON del body primero
        data = {}
        
        # 1. Intentar parsear JSON del body (más confiable)
        if request.body:
            try:
                body_str = request.body.decode('utf-8')
                print(f"📱 [FCM Register] Raw body: {body_str[:200]}...")
                data = json.loads(body_str)
                print(f"📱 [FCM Register] JSON parseado correctamente: {data}")
            except json.JSONDecodeError as e:
                print(f"⚠️ [FCM Register] Error parseando JSON: {e}")
                print(f"   Body recibido: {request.body[:200] if request.body else 'vacío'}...")
            except Exception as e:
                print(f"⚠️ [FCM Register] Error decodificando body: {e}")
        
        # 2. Si no hay datos en el body, intentar request.data (Django REST Framework)
        if not data and hasattr(request, 'data'):
            try:
                data = dict(request.data) if request.data else {}
                print(f"📱 [FCM Register] Usando request.data: {data}")
            except Exception as e:
                print(f"⚠️ [FCM Register] Error con request.data: {e}")
        
        # 3. Si aún no hay datos, intentar request.POST (form-data)
        if not data:
            data = dict(request.POST) if request.POST else {}
            print(f"📱 [FCM Register] Usando request.POST: {data}")
        
        token = data.get('token')
        platform = data.get('platform', 'android')
        device_id = data.get('device_id')
        user_id = data.get('user_id')  # ID del usuario
        
        # Debug: Log de lo que se recibe
        print(f"📱 [FCM Register] ===== DATOS EXTRAÍDOS =====")
        print(f"   Token: {token[:30] if token else 'None'}...")
        print(f"   Platform: {platform}")
        print(f"   Device ID: {device_id}")
        print(f"   User ID: {user_id} (tipo: {type(user_id)})")
        print(f"   Request method: {request.method}")
        print(f"   Content-Type: {request.META.get('CONTENT_TYPE', 'N/A')}")
        print(f"   Data completo: {data}")
        
        if not token:
            print("❌ [FCM Register] Error: Token FCM requerido")
            return JsonResponse({
                'success': False,
                'error': 'Token FCM requerido'
            }, status=400)
        
        # Obtener usuario (puede ser ID numérico o username)
        if user_id:
            try:
                # Intentar como ID numérico primero
                if isinstance(user_id, int) or (isinstance(user_id, str) and user_id.isdigit()):
                    user = AppUser.objects.get(id=int(user_id))
                    print(f"✅ [FCM Register] Usuario encontrado por ID: {user.username} (ID: {user_id})")
                else:
                    # Intentar como username
                    user = AppUser.objects.get(username=user_id)
                    print(f"✅ [FCM Register] Usuario encontrado por username: {user.username} (ID: {user.id})")
            except AppUser.DoesNotExist:
                print(f"❌ [FCM Register] Usuario '{user_id}' no encontrado (ni por ID ni por username)")
                return JsonResponse({
                    'success': False,
                    'error': f'Usuario "{user_id}" no encontrado. Usa el ID numérico o el username.'
                }, status=404)
        elif request.user.is_authenticated:
            user = request.user
            print(f"✅ [FCM Register] Usuario autenticado: {user.username}")
        else:
            print(f"❌ [FCM Register] Error: Usuario no autenticado y no se proporcionó user_id")
            return JsonResponse({
                'success': False,
                'error': 'Usuario no autenticado y no se proporcionó user_id. Por favor, incluye "user_id" en el body del request.'
            }, status=401)
        
        # Registrar token
        fcm_token = register_fcm_token(user, token, platform, device_id)
        
        print(f"✅ Token FCM registrado para {user.username}: {token[:20]}...")
        
        return JsonResponse({
            'success': True,
            'message': 'Token FCM registrado correctamente',
            'user_id': user.id,
            'username': user.username,
            'platform': platform
        })
        
    except Exception as e:
        print(f"❌ Error registrando token FCM: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
