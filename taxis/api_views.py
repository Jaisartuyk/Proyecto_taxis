from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from .models import Taxi, Ride, RideDestination, PriceNegotiation, AppUser
from datetime import datetime, timedelta

User = get_user_model()

# 🚕 Login para conductores
class LoginAPIView(APIView):
    permission_classes = []  # Permitir acceso sin autenticación
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        print(f"🔐 Login attempt: username={username}, password={'*' * len(password) if password else 'None'}")

        if not username or not password:
            print(f"❌ Login failed: Missing credentials")
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)
        print(f"🔍 Authenticate result: user={user}, is_authenticated={user is not None if user else False}")

        if user is not None:
            try:
                token, created = Token.objects.get_or_create(user=user)
                role = getattr(user, 'role', None)

                if role == 'driver':
                    # Obtener el admin de la cooperativa del conductor
                    admin_id = None
                    admin_name = None
                    
                    if user.organization:
                        # Buscar el admin de la organización (excluyendo superusers)
                        admin_user = AppUser.objects.filter(
                            organization=user.organization,
                            role='admin',
                            is_superuser=False  # Excluir superadmin
                        ).first()
                        
                        if admin_user:
                            admin_id = admin_user.id
                            admin_name = admin_user.get_full_name() or admin_user.username
                            print(f"✅ Admin encontrado: {admin_name} (ID: {admin_id})")
                        else:
                            print(f"⚠️ No se encontró admin para organización: {user.organization.name}")
                    
                    return Response({
                        "message": "Inicio de sesión exitoso.",
                        "user_id": user.id,
                        "role": role,
                        "token": token.key,
                        "admin_id": admin_id,
                        "admin_name": admin_name,
                        "organization_id": user.organization.id if user.organization else None,
                        "organization_name": user.organization.name if user.organization else None
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Acceso denegado: Solo conductores pueden iniciar sesión.",
                        "role": role
                    }, status=status.HTTP_403_FORBIDDEN)

            except Exception as e:
                return Response(
                    {"error": f"Error al generar el token: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"error": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_webpush_subscription(request):
    """
    Guarda la información de suscripción de Web Push para el usuario autenticado.
    """
    import json
    
    # El frontend envía el objeto de suscripción directamente
    subscription_data = request.data
    
    # Si viene en subscription_info, usarlo (compatibilidad hacia atrás)
    if 'subscription_info' in subscription_data:
        subscription_info = subscription_data['subscription_info']
    else:
        # Si no, usar todo el objeto como subscription_info
        subscription_info = subscription_data

    if not subscription_info:
        return Response({"error": "No se proporcionó información de suscripción"}, status=status.HTTP_400_BAD_REQUEST)

    # Asegurar que subscription_info sea un diccionario
    if isinstance(subscription_info, str):
        try:
            subscription_info = json.loads(subscription_info)
        except json.JSONDecodeError:
            return Response({"error": "Información de suscripción inválida"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validar que tenga las claves necesarias
    required_keys = ['endpoint', 'keys']
    if not all(key in subscription_info for key in required_keys):
        return Response({"error": "Faltan campos requeridos en la suscripción"}, status=status.HTTP_400_BAD_REQUEST)

    # Evitar duplicados
    from .models import WebPushSubscription
    subscription, created = WebPushSubscription.objects.get_or_create(
        user=request.user,
        defaults={'subscription_info': subscription_info}
    )

    if not created:
        # Si ya existe, actualizarla
        subscription.subscription_info = subscription_info
        subscription.save()
        return Response({"message": "Suscripción actualizada con éxito"}, status=status.HTTP_200_OK)
    
    return Response({"message": "Suscripción guardada con éxito"}, status=status.HTTP_201_CREATED)

class UpdateLocationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'driver':
            return Response(
                {'error': 'Solo los conductores pueden actualizar su ubicación.'},
                status=status.HTTP_403_FORBIDDEN
            )

        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        if latitude is None or longitude is None:
            return Response(
                {'error': 'Latitud y longitud son requeridas.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            taxi = user.taxi # Get the taxi associated with the driver
            taxi.latitude = latitude
            taxi.longitude = longitude
            taxi.save()
        except Taxi.DoesNotExist:
             return Response(
                {'error': 'No hay un taxi asociado a este conductor.'},
                status=status.HTTP_400_BAD_REQUEST
            )


        return Response(
            {'message': 'Ubicación actualizada correctamente.'},
            status=status.HTTP_200_OK
        )

# 🧪 Función de prueba para notificaciones push
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_push_notification(request):
    """
    Vista de prueba para enviar una notificación push al usuario actual
    """
    try:
        from .push_notifications import send_push_notification
        
        # Obtener datos de la solicitud
        title = request.data.get('title', 'Prueba de Notificación')
        message = request.data.get('message', 'Esta es una notificación de prueba')
        
        # Enviar la notificación push al usuario actual
        result = send_push_notification(
            user=request.user,
            title=title,
            message=message,
            url='/driver-dashboard/'  # URL a donde dirigir cuando hagan click
        )
        
        if result:
            return Response({
                'success': True,
                'message': 'Notificación push enviada correctamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': 'No se pudo enviar la notificación. Verifica que tengas una suscripción push activa.'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al enviar la notificación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 📱 Registrar token FCM
@api_view(['POST'])
def register_fcm_token_view(request):
    """
    Registrar token FCM para notificaciones push móviles
    
    Body:
    {
        "token": "fcm_token_here",
        "user_id": "conductor_001",  # Opcional si está autenticado
        "device_type": "android"     # android o ios
    }
    """
    from .fcm_notifications import register_fcm_token
    from .models import AppUser
    
    try:
        token = request.data.get('token')
        user_id = request.data.get('user_id')
        device_type = request.data.get('device_type', 'android')
        
        if not token:
            return Response({
                'success': False,
                'message': 'El token FCM es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si el usuario está autenticado, usar ese usuario
        if request.user.is_authenticated:
            user = request.user
        elif user_id:
            # Buscar usuario por username o ID
            try:
                if user_id.isdigit():
                    user = AppUser.objects.get(id=int(user_id))
                else:
                    user = AppUser.objects.get(username=user_id)
            except AppUser.DoesNotExist:
                return Response({
                    'success': False,
                    'message': f'Usuario {user_id} no encontrado'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'success': False,
                'message': 'Se requiere autenticación o user_id'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Registrar el token
        fcm_token = register_fcm_token(
            user=user,
            token=token,
            platform=device_type
        )
        
        return Response({
            'success': True,
            'message': 'Token FCM registrado exitosamente',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'device_type': device_type,
                'token_id': fcm_token.id
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error al registrar token: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 📊 Obtener estadísticas del conductor
@api_view(['GET'])
def driver_stats_view(request):
    """
    Obtener estadísticas del conductor autenticado
    
    Returns:
    {
        "total_rides": 12,
        "total_earnings": "45.50",
        "average_rating": 4.8,
        "total_hours": 5
    }
    """
    try:
        # Validar token manualmente
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener estadísticas reales del conductor
        from django.db.models import Sum, Avg, Count
        from django.utils import timezone
        
        total_rides = Ride.objects.filter(driver=user).count()
        completed_rides = Ride.objects.filter(driver=user, status='completed').count()
        
        # Ganancias totales
        total_earnings = Ride.objects.filter(
            driver=user,
            status='completed',
            price__isnull=False
        ).aggregate(total=Sum('price'))['total'] or 0
        
        # Rating promedio (si existe el campo)
        average_rating = 4.5  # Placeholder, ajustar si tienes campo de rating
        
        # Horas totales (estimado)
        total_hours = completed_rides * 0.5  # Estimado: 30 min por carrera
        
        stats = {
            'total_rides': total_rides,
            'completed_rides': completed_rides,
            'total_earnings': str(total_earnings),
            'average_rating': average_rating,
            'total_hours': int(total_hours)
        }
        
        return Response(stats, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener estadísticas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 📜 Obtener historial de carreras del conductor
@api_view(['GET'])
def ride_history_view(request):
    """
    Obtener historial de carreras del conductor autenticado
    
    Returns:
    [
        {
            "id": 1,
            "origin": "Av. Principal 123",
            "destination": "Centro Comercial",
            "created_at": "2025-12-17T10:00:00Z",
            "amount": "5.50",
            "status": "completed",
            "rating": 5
        },
        ...
    ]
    """
    try:
        # Validar token manualmente
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener carreras completadas y canceladas del conductor
        rides = Ride.objects.filter(
            driver=user,
            status__in=['completed', 'cancelled']
        ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
        
        rides_data = []
        for ride in rides:
            # Obtener primer destino
            first_destination = ride.destinations.first()
            destination_text = first_destination.destination if first_destination else 'Sin destino'
            
            rides_data.append({
                'id': ride.id,
                'origin': ride.origin,
                'destination': destination_text,
                'created_at': ride.created_at.isoformat(),
                'amount': str(ride.price) if ride.price else '0.00',
                'price': str(ride.price) if ride.price else '0.00',
                'status': ride.status,
                'rating': ride.rating if hasattr(ride, 'rating') and ride.rating else 0,
            })
        
        return Response(rides_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener historial: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 🚕 Obtener carreras disponibles para el conductor
@api_view(['GET'])
def available_rides_view(request):
    """
    Obtener carreras disponibles (status='requested') para que el conductor acepte
    
    Returns:
    [
        {
            "id": 1,
            "customer": "Juan Pérez",
            "origin": "Av. Principal 123",
            "origin_latitude": -12.0464,
            "origin_longitude": -77.0428,
            "destinations": [
                {"address": "Centro Comercial", "latitude": -12.0500, "longitude": -77.0450}
            ],
            "price": "15.00",
            "created_at": "2025-12-17T10:00:00Z",
            "distance": "5.2 km"
        },
        ...
    ]
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # ✅ MULTI-TENANT: Filtrar por organización
        if user.organization:
            # Conductor ve solo carreras de su organización
            rides = Ride.objects.filter(
                status='requested',
                driver__isnull=True,
                organization=user.organization
            ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
        else:
            # Usuario sin organización no ve nada
            rides = Ride.objects.none()
        
        rides_data = []
        for ride in rides:
            destinations = []
            for dest in ride.destinations.all().order_by('order'):
                destinations.append({
                    'address': dest.destination,  # Corregido: destination en lugar de address
                    'latitude': dest.destination_latitude,  # Corregido
                    'longitude': dest.destination_longitude  # Corregido
                })
            
            rides_data.append({
                'id': ride.id,
                'customer': ride.customer.username,
                'origin': ride.origin,
                'origin_latitude': ride.origin_latitude,
                'origin_longitude': ride.origin_longitude,
                'destinations': destinations,
                'price': str(ride.price) if ride.price else '0.00',
                'status': ride.status,  # ✅ Agregar status
                'created_at': ride.created_at.isoformat(),
                'distance': '-- km'  # TODO: Calcular distancia real
            })
        
        return Response(rides_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener carreras disponibles: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 🚗 Obtener carreras en curso del conductor
@api_view(['GET'])
def driver_active_rides_view(request):
    """
    Obtener carreras activas del conductor (accepted, in_progress)
    
    Returns:
    [
        {
            "id": 1,
            "customer": "Juan Pérez",
            "customer_phone": "+51987654321",
            "origin": "Av. Principal 123",
            "origin_latitude": -12.0464,
            "origin_longitude": -77.0428,
            "destinations": [...],
            "price": "15.00",
            "status": "in_progress",
            "start_time": "2025-12-17T10:00:00Z",
            "estimated_duration": "15 min"
        }
    ]
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener carreras activas del conductor
        rides = Ride.objects.filter(
            driver=user,
            status__in=['accepted', 'in_progress']
        ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
        
        rides_data = []
        for ride in rides:
            destinations = []
            for dest in ride.destinations.all().order_by('order'):
                destinations.append({
                    'address': dest.destination,  # ✅ Corregir: destination en lugar de address
                    'latitude': dest.destination_latitude,  # ✅ Corregir: destination_latitude
                    'longitude': dest.destination_longitude  # ✅ Corregir: destination_longitude
                })
            
            rides_data.append({
                'id': ride.id,
                'customer': {
                    'id': ride.customer.id,
                    'username': ride.customer.username,
                    'name': ride.customer.get_full_name() or ride.customer.username,
                    'phone': getattr(ride.customer, 'phone_number', 'N/A'),
                },
                'customer_phone': getattr(ride.customer, 'phone_number', 'N/A'),
                'driver': {
                    'id': ride.driver.id,
                    'username': ride.driver.username,
                    'name': ride.driver.get_full_name() or ride.driver.username,
                    'phone': getattr(ride.driver, 'phone_number', 'N/A'),
                } if ride.driver else None,
                'origin': ride.origin,
                'origin_latitude': ride.origin_latitude,
                'origin_longitude': ride.origin_longitude,
                'destinations': destinations,
                'price': str(ride.price) if ride.price else '0.00',
                'status': ride.status,
                'start_time': ride.start_time.isoformat() if ride.start_time else None,
                'estimated_duration': '-- min'  # TODO: Calcular duración estimada
            })
        
        return Response(rides_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener carreras activas: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Aceptar una carrera
@api_view(['POST'])
def accept_ride_view(request, ride_id):
    """
    Aceptar una carrera disponible
    
    Body: {} (vacío)
    
    Returns:
    {
        "success": true,
        "message": "Carrera aceptada exitosamente",
        "ride": {...}
    }
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verificar que el usuario sea conductor
        if user.role != 'driver':
            return Response({
                'error': 'Solo conductores pueden aceptar carreras'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ✅ VALIDAR: Conductor debe estar aprobado
        if not user.is_active_driver():
            return Response({
                'error': 'Tu cuenta debe estar aprobada para aceptar carreras. Contacta al administrador.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # ✅ VALIDAR: Conductor debe tener organización
        if not user.organization:
            return Response({
                'error': 'No tienes una organización asignada. Contacta al administrador.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id, status='requested', driver__isnull=True)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no disponible'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # ✅ VALIDAR: Carrera debe ser de la misma organización
        if ride.organization and ride.organization != user.organization:
            return Response({
                'error': 'No puedes aceptar carreras de otra cooperativa'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Asignar conductor y cambiar estado
        ride.driver = user
        ride.status = 'accepted'
        ride.save()
        
        return Response({
            'success': True,
            'message': 'Carrera aceptada exitosamente',
            'ride': {
                'id': ride.id,
                'customer': ride.customer.username,
                'origin': ride.origin,
                'price': str(ride.price) if ride.price else '0.00',
                'status': ride.status
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al aceptar carrera: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 🏁 Iniciar carrera
@api_view(['POST'])
def start_ride_view(request, ride_id):
    """
    Iniciar una carrera aceptada
    
    Body: {} (vacío)
    
    Returns:
    {
        "success": true,
        "message": "Carrera iniciada",
        "ride": {...}
    }
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id, driver=user, status='accepted')
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada o no puede ser iniciada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Iniciar carrera
        ride.status = 'in_progress'
        ride.start_time = timezone.now()
        ride.save()
        
        return Response({
            'success': True,
            'message': 'Carrera iniciada',
            'ride': {
                'id': ride.id,
                'status': ride.status,
                'start_time': ride.start_time.isoformat()
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al iniciar carrera: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Completar carrera
@api_view(['POST'])
def complete_ride_view(request, ride_id):
    """
    Completar una carrera en progreso
    
    Body: {} (vacío)
    
    Returns:
    {
        "success": true,
        "message": "Carrera completada",
        "ride": {...}
    }
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id, driver=user, status='in_progress')
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada o no puede ser completada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Completar carrera
        ride.status = 'completed'
        ride.end_time = timezone.now()
        ride.save()
        
        # Calcular duración
        duration = None
        if ride.start_time and ride.end_time:
            duration_seconds = (ride.end_time - ride.start_time).total_seconds()
            duration = f"{int(duration_seconds // 60)} min"
        
        return Response({
            'success': True,
            'message': 'Carrera completada',
            'ride': {
                'id': ride.id,
                'status': ride.status,
                'end_time': ride.end_time.isoformat(),
                'duration': duration,
                'price': str(ride.price) if ride.price else '0.00'
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al completar carrera: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ❌ Cancelar carrera
@api_view(['POST'])
def cancel_ride_view(request, ride_id):
    """
    Cancelar una carrera
    
    Body:
    {
        "reason": "Motivo de cancelación"
    }
    
    Returns:
    {
        "success": true,
        "message": "Carrera cancelada"
    }
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener la carrera (puede ser conductor o cliente)
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el usuario sea el conductor o el cliente
        if user != ride.driver and user != ride.customer:
            return Response({
                'error': 'No tienes permiso para cancelar esta carrera'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la carrera no esté completada
        if ride.status == 'completed':
            return Response({
                'error': 'No se puede cancelar una carrera completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que no esté ya cancelada
        if ride.status == 'canceled':
            return Response({
                'error': 'Esta carrera ya está cancelada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancelar carrera
        ride.status = 'canceled'
        
        # Si había un conductor asignado, liberarlo
        if ride.driver:
            ride.driver = None
        
        ride.save()
        
        return Response({
            'success': True,
            'message': 'Carrera cancelada'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al cancelar carrera: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 📋 Obtener detalles de una carrera específica
@api_view(['GET'])
def ride_detail_api_view(request, ride_id):
    """
    Obtener detalles completos de una carrera
    
    Permite ver si:
    - Es el conductor asignado
    - Es el cliente dueño
    - Es un conductor y la carrera está disponible (requested)
    - Es admin
    
    Returns:
    {
        "id": 1,
        "customer": "Juan Pérez",
        "customer_phone": "+51987654321",
        "driver": "Carlos López" (si ya tiene),
        "origin": "Av. Principal 123",
        "origin_latitude": -12.0464,
        "origin_longitude": -77.0428,
        "destinations": [...],
        "price": "15.00",
        "status": "requested",
        "created_at": "2025-12-17T10:00:00Z",
        "start_time": null,
        "end_time": null
    }
    """
    try:
        # Validar token
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Token '):
            return Response({
                'error': 'Token de autenticación no proporcionado'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token_key = auth_header.replace('Token ', '')
        
        try:
            token = Token.objects.get(key=token_key)
            user = token.user
        except Token.DoesNotExist:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar permisos
        is_involved = (
            user.is_superuser or 
            user == ride.driver or 
            user == ride.customer
        )
        
        # Permitir ver si es un conductor y la carrera está solicitada
        if not is_involved and user.role == 'driver' and ride.status == 'requested':
            pass  # Permitir acceso
        elif not is_involved:
            return Response({
                'error': 'No tiene permiso para ver esta carrera'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Preparar destinos
        destinations = []
        for dest in ride.destinations.all().order_by('order'):
            destinations.append({
                'address': dest.destination,
                'latitude': dest.destination_latitude,
                'longitude': dest.destination_longitude,
                'order': dest.order
            })
        
        # Preparar respuesta
        ride_data = {
            'id': ride.id,
            'customer': {
                'id': ride.customer.id,
                'username': ride.customer.username,
                'name': ride.customer.get_full_name() or ride.customer.username,
                'phone': getattr(ride.customer, 'phone_number', 'N/A'),
            },
            'customer_phone': getattr(ride.customer, 'phone_number', 'N/A'),
            'driver': {
                'id': ride.driver.id,
                'username': ride.driver.username,
                'name': ride.driver.get_full_name() or ride.driver.username,
                'phone': getattr(ride.driver, 'phone_number', 'N/A'),
            } if ride.driver else None,
            'origin': ride.origin,
            'origin_latitude': ride.origin_latitude,
            'origin_longitude': ride.origin_longitude,
            'destinations': destinations,
            'price': str(ride.price) if ride.price else '0.00',
            'status': ride.status,
            'created_at': ride.created_at.isoformat(),
            'start_time': ride.start_time.isoformat() if ride.start_time else None,
            'end_time': ride.end_time.isoformat() if ride.end_time else None,
        }
        
        return Response(ride_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener detalles: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 💰 Crear negociación de precio
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_price_negotiation(request):
    """
    Crear una propuesta de negociación de precio
    
    Body:
    {
        "origin": "Av. Principal 123",
        "origin_latitude": -12.0464,
        "origin_longitude": -77.0428,
        "destination": "Centro Comercial",
        "destination_coords": "-12.0500,-77.0450",
        "suggested_price": "15.00",
        "proposed_price": "12.00",
        "message": "Es una distancia corta"
    }
    
    Returns:
    {
        "success": true,
        "message": "Propuesta enviada exitosamente",
        "negotiation_id": 1
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea cliente
        if user.role != 'customer':
            return Response({
                'error': 'Solo los clientes pueden proponer precios'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validar que el usuario tenga organización
        if not user.organization:
            return Response({
                'error': 'Usuario sin organización asignada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos
        origin = request.data.get('origin')
        origin_lat = request.data.get('origin_latitude')
        origin_lon = request.data.get('origin_longitude')
        destination = request.data.get('destination')
        destination_coords = request.data.get('destination_coords', '')
        suggested_price = request.data.get('suggested_price')
        proposed_price = request.data.get('proposed_price')
        message = request.data.get('message', '')
        
        # Validaciones
        if not all([origin, origin_lat, origin_lon, destination, suggested_price, proposed_price]):
            return Response({
                'error': 'Faltan campos requeridos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Parsear coordenadas del destino
        dest_lat, dest_lon = None, None
        if destination_coords:
            try:
                coords = destination_coords.split(',')
                dest_lat = float(coords[0])
                dest_lon = float(coords[1])
            except:
                pass
        
        # Validar precios
        try:
            suggested_price = float(suggested_price)
            proposed_price = float(proposed_price)
            
            if proposed_price < 0.50:
                return Response({
                    'error': 'El precio mínimo es $0.50'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except ValueError:
            return Response({
                'error': 'Precios inválidos'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular fecha de expiración (15 minutos)
        expires_at = timezone.now() + timedelta(minutes=15)
        
        # Crear negociación
        negotiation = PriceNegotiation.objects.create(
            customer=user,
            organization=user.organization,
            origin=origin,
            origin_latitude=origin_lat,
            origin_longitude=origin_lon,
            destination=destination,
            destination_latitude=dest_lat,
            destination_longitude=dest_lon,
            suggested_price=suggested_price,
            proposed_price=proposed_price,
            response_message=message,
            status='pending',
            expires_at=expires_at
        )
        
        print(f"💰 Nueva negociación creada: #{negotiation.id} - Cliente: {user.get_full_name()} - Precio propuesto: ${proposed_price}")
        
        # TODO: Enviar notificación a la central
        # send_negotiation_notification(negotiation)
        
        return Response({
            'success': True,
            'message': 'Propuesta enviada exitosamente',
            'negotiation_id': negotiation.id
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"❌ Error al crear negociación: {str(e)}")
        return Response({
            'error': f'Error al crear negociación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Aceptar negociación y crear carrera
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_price_negotiation(request, negotiation_id):
    """
    Aceptar una negociación de precio y crear la carrera automáticamente
    
    Returns:
    {
        "success": true,
        "message": "Negociación aceptada y carrera creada",
        "ride_id": 123
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea admin
        if user.role not in ['admin', 'superadmin']:
            return Response({
                'error': 'Solo administradores pueden aceptar negociaciones'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener negociación
        try:
            negotiation = PriceNegotiation.objects.get(id=negotiation_id)
        except PriceNegotiation.DoesNotExist:
            return Response({
                'error': 'Negociación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar organización (si no es super admin)
        if not user.is_superuser and negotiation.organization != user.organization:
            return Response({
                'error': 'No tienes permiso para aceptar esta negociación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validar que esté pendiente
        if negotiation.status != 'pending':
            return Response({
                'error': f'Esta negociación ya fue procesada (estado: {negotiation.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear la carrera con el precio propuesto
        ride = Ride.objects.create(
            customer=negotiation.customer,
            organization=negotiation.organization,
            origin=negotiation.origin,
            origin_latitude=negotiation.origin_latitude,
            origin_longitude=negotiation.origin_longitude,
            price=negotiation.proposed_price,  # Usar precio propuesto
            status='requested'
        )
        
        # Crear destino
        RideDestination.objects.create(
            ride=ride,
            destination=negotiation.destination,
            destination_latitude=negotiation.destination_latitude,
            destination_longitude=negotiation.destination_longitude,
            order=1
        )
        
        # Actualizar negociación
        negotiation.status = 'accepted'
        negotiation.final_price = negotiation.proposed_price
        negotiation.responded_by = user
        negotiation.ride = ride
        negotiation.save()
        
        print(f"✅ Negociación #{negotiation_id} aceptada - Carrera #{ride.id} creada con precio ${negotiation.proposed_price}")
        
        # Enviar notificación push al cliente
        try:
            from .push_notifications import send_push_notification
            send_push_notification(
                user=negotiation.customer,
                title='✅ ¡Precio aceptado!',
                body=f'Tu propuesta de ${negotiation.proposed_price} fue aceptada. Carrera #{ride.id} creada.',
                data={
                    'type': 'negotiation_accepted',
                    'negotiation_id': negotiation.id,
                    'ride_id': ride.id,
                    'url': f'/ride/{ride.id}/'
                }
            )
        except Exception as e:
            print(f"⚠️ Error al enviar notificación al cliente: {str(e)}")
        
        # 🚕 ENVIAR NOTIFICACIÓN FCM A CONDUCTORES DISPONIBLES
        try:
            from .fcm_notifications import send_new_ride_notification_fcm
            
            # Obtener conductores disponibles de la misma organización
            available_drivers = AppUser.objects.filter(
                role='driver',
                organization=ride.organization,
                driver_status='approved',
                is_active=True
            )
            
            print(f"📱 Enviando notificación de carrera #{ride.id} a {available_drivers.count()} conductores")
            
            # Preparar datos completos de la carrera
            ride_data = {
                'ride_id': ride.id,
                'customer_name': ride.customer.get_full_name() if ride.customer else 'Cliente',
                'origin': ride.origin,
                'destination': negotiation.destination,  # ✅ INCLUIR DESTINO
                'price': str(ride.price),
                'origin_latitude': str(ride.origin_latitude) if ride.origin_latitude else None,
                'origin_longitude': str(ride.origin_longitude) if ride.origin_longitude else None,
                'destination_latitude': str(negotiation.destination_latitude) if negotiation.destination_latitude else None,
                'destination_longitude': str(negotiation.destination_longitude) if negotiation.destination_longitude else None,
                'status': ride.status,
                'created_at': ride.created_at.isoformat() if ride.created_at else None,
                'type': 'new_ride'
            }
            
            # Enviar a cada conductor
            for driver in available_drivers:
                send_new_ride_notification_fcm(
                    driver=driver,
                    ride=ride,
                    extra_data=ride_data
                )
            
            print(f"✅ Notificaciones FCM enviadas a conductores para carrera #{ride.id}")
            
        except Exception as e:
            print(f"⚠️ Error al enviar notificaciones FCM a conductores: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Negociación aceptada y carrera creada',
            'ride_id': ride.id,
            'final_price': str(negotiation.proposed_price)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al aceptar negociación: {str(e)}")
        return Response({
            'error': f'Error al aceptar negociación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 💬 Enviar contraoferta
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def counter_offer_negotiation(request, negotiation_id):
    """
    Enviar una contraoferta al cliente
    
    Body:
    {
        "counter_price": "2.75",
        "message": "Te ofrecemos este precio"
    }
    
    Returns:
    {
        "success": true,
        "message": "Contraoferta enviada"
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea admin
        if user.role not in ['admin', 'superadmin']:
            return Response({
                'error': 'Solo administradores pueden enviar contraofertas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener negociación
        try:
            negotiation = PriceNegotiation.objects.get(id=negotiation_id)
        except PriceNegotiation.DoesNotExist:
            return Response({
                'error': 'Negociación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar organización
        if not user.is_superuser and negotiation.organization != user.organization:
            return Response({
                'error': 'No tienes permiso para responder esta negociación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validar que esté pendiente
        if negotiation.status != 'pending':
            return Response({
                'error': f'Esta negociación ya fue procesada (estado: {negotiation.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos
        counter_price = request.data.get('counter_price')
        message = request.data.get('message', '')
        
        if not counter_price:
            return Response({
                'error': 'Falta el precio de contraoferta'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            counter_price = float(counter_price)
            if counter_price < 0.50:
                return Response({
                    'error': 'El precio mínimo es $0.50'
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                'error': 'Precio inválido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar negociación
        negotiation.status = 'counter_offered'
        negotiation.counter_offer_price = counter_price
        negotiation.response_message = message
        negotiation.responded_by = user
        negotiation.save()
        
        print(f"💬 Contraoferta enviada para negociación #{negotiation_id}: ${counter_price}")
        
        # Enviar notificación push al cliente
        try:
            from .push_notifications import send_push_notification
            send_push_notification(
                user=negotiation.customer,
                title='💬 Contraoferta recibida',
                body=f'La central propone ${counter_price}. {message[:50] if message else ""}',
                data={
                    'type': 'negotiation_counter_offer',
                    'negotiation_id': negotiation.id,
                    'counter_price': str(counter_price),
                    'url': '/customer-dashboard/'
                }
            )
        except Exception as e:
            print(f"⚠️ Error al enviar notificación: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Contraoferta enviada al cliente',
            'counter_price': str(counter_price)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al enviar contraoferta: {str(e)}")
        return Response({
            'error': f'Error al enviar contraoferta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ❌ Rechazar negociación
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_price_negotiation(request, negotiation_id):
    """
    Rechazar una negociación de precio
    
    Body:
    {
        "reason": "Precio muy bajo"
    }
    
    Returns:
    {
        "success": true,
        "message": "Negociación rechazada"
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea admin
        if user.role not in ['admin', 'superadmin']:
            return Response({
                'error': 'Solo administradores pueden rechazar negociaciones'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener negociación
        try:
            negotiation = PriceNegotiation.objects.get(id=negotiation_id)
        except PriceNegotiation.DoesNotExist:
            return Response({
                'error': 'Negociación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar organización
        if not user.is_superuser and negotiation.organization != user.organization:
            return Response({
                'error': 'No tienes permiso para rechazar esta negociación'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Validar que esté pendiente
        if negotiation.status != 'pending':
            return Response({
                'error': f'Esta negociación ya fue procesada (estado: {negotiation.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener motivo
        reason = request.data.get('reason', 'Sin motivo especificado')
        
        # Actualizar negociación
        negotiation.status = 'rejected'
        negotiation.response_message = reason
        negotiation.responded_by = user
        negotiation.save()
        
        print(f"❌ Negociación #{negotiation_id} rechazada - Motivo: {reason}")
        
        # Enviar notificación push al cliente
        try:
            from .push_notifications import send_push_notification
            send_push_notification(
                user=negotiation.customer,
                title='❌ Propuesta rechazada',
                body=f'Tu propuesta de ${negotiation.proposed_price} fue rechazada. {reason[:50]}',
                data={
                    'type': 'negotiation_rejected',
                    'negotiation_id': negotiation.id,
                    'url': '/request-ride/'
                }
            )
        except Exception as e:
            print(f"⚠️ Error al enviar notificación: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Negociación rechazada'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al rechazar negociación: {str(e)}")
        return Response({
            'error': f'Error al rechazar negociación: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Cliente acepta contraoferta
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_accept_counter_offer(request, negotiation_id):
    """
    Cliente acepta la contraoferta de la central y crea la carrera
    
    Returns:
    {
        "success": true,
        "message": "Contraoferta aceptada y carrera creada",
        "ride_id": 123
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea cliente
        if user.role != 'customer':
            return Response({
                'error': 'Solo clientes pueden aceptar contraofertas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener negociación
        try:
            negotiation = PriceNegotiation.objects.get(id=negotiation_id, customer=user)
        except PriceNegotiation.DoesNotExist:
            return Response({
                'error': 'Negociación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que tenga contraoferta
        if negotiation.status != 'counter_offered':
            return Response({
                'error': f'Esta negociación no tiene contraoferta (estado: {negotiation.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear la carrera con el precio de la contraoferta
        ride = Ride.objects.create(
            customer=user,
            organization=negotiation.organization,
            origin=negotiation.origin,
            origin_latitude=negotiation.origin_latitude,
            origin_longitude=negotiation.origin_longitude,
            price=negotiation.counter_offer_price,  # Usar precio de contraoferta
            status='requested'
        )
        
        # Crear destino
        RideDestination.objects.create(
            ride=ride,
            destination=negotiation.destination,
            destination_latitude=negotiation.destination_latitude,
            destination_longitude=negotiation.destination_longitude,
            order=1
        )
        
        # Actualizar negociación
        negotiation.status = 'client_accepted'
        negotiation.final_price = negotiation.counter_offer_price
        negotiation.ride = ride
        negotiation.save()
        
        print(f"✅ Cliente aceptó contraoferta #{negotiation_id} - Carrera #{ride.id} creada con precio ${negotiation.counter_offer_price}")
        
        # 🚕 ENVIAR NOTIFICACIÓN FCM A CONDUCTORES DISPONIBLES
        try:
            from .fcm_notifications import send_new_ride_notification_fcm
            
            # Obtener conductores disponibles de la misma organización
            available_drivers = AppUser.objects.filter(
                role='driver',
                organization=ride.organization,
                driver_status='approved',
                is_active=True
            )
            
            print(f"📱 Enviando notificación de carrera #{ride.id} a {available_drivers.count()} conductores")
            
            # Preparar datos completos de la carrera
            ride_data = {
                'ride_id': ride.id,
                'customer_name': ride.customer.get_full_name() if ride.customer else 'Cliente',
                'origin': ride.origin,
                'destination': negotiation.destination,  # ✅ INCLUIR DESTINO
                'price': str(ride.price),
                'origin_latitude': str(ride.origin_latitude) if ride.origin_latitude else None,
                'origin_longitude': str(ride.origin_longitude) if ride.origin_longitude else None,
                'destination_latitude': str(negotiation.destination_latitude) if negotiation.destination_latitude else None,
                'destination_longitude': str(negotiation.destination_longitude) if negotiation.destination_longitude else None,
                'status': ride.status,
                'created_at': ride.created_at.isoformat() if ride.created_at else None,
                'type': 'new_ride'
            }
            
            # Enviar a cada conductor
            for driver in available_drivers:
                send_new_ride_notification_fcm(
                    driver=driver,
                    ride=ride,
                    extra_data=ride_data
                )
            
            print(f"✅ Notificaciones FCM enviadas a conductores para carrera #{ride.id}")
            
        except Exception as e:
            print(f"⚠️ Error al enviar notificaciones FCM a conductores: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'Contraoferta aceptada y carrera creada',
            'ride_id': ride.id,
            'final_price': str(negotiation.counter_offer_price)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al aceptar contraoferta: {str(e)}")
        return Response({
            'error': f'Error al aceptar contraoferta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ❌ Cliente rechaza contraoferta
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def client_reject_counter_offer(request, negotiation_id):
    """
    Cliente rechaza la contraoferta de la central
    
    Returns:
    {
        "success": true,
        "message": "Contraoferta rechazada"
    }
    """
    try:
        user = request.user
        
        # Validar que el usuario sea cliente
        if user.role != 'customer':
            return Response({
                'error': 'Solo clientes pueden rechazar contraofertas'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener negociación
        try:
            negotiation = PriceNegotiation.objects.get(id=negotiation_id, customer=user)
        except PriceNegotiation.DoesNotExist:
            return Response({
                'error': 'Negociación no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que tenga contraoferta
        if negotiation.status != 'counter_offered':
            return Response({
                'error': f'Esta negociación no tiene contraoferta (estado: {negotiation.status})'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar negociación
        negotiation.status = 'client_rejected'
        negotiation.save()
        
        print(f"❌ Cliente rechazó contraoferta #{negotiation_id}")
        
        return Response({
            'success': True,
            'message': 'Contraoferta rechazada'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al rechazar contraoferta: {str(e)}")
        return Response({
            'error': f'Error al rechazar contraoferta: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================
# GESTIÓN DE PERFIL - API MÓVIL
# ============================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    """
    Obtener información del perfil del usuario autenticado
    
    Returns:
    {
        "id": 1,
        "username": "carlos",
        "email": "carlos@example.com",
        "first_name": "Carlos",
        "last_name": "Rodríguez",
        "phone_number": "555-1234",
        "national_id": "123456789",
        "role": "driver",
        "profile_picture": "/media/profiles/carlos.jpg",
        "organization": {
            "id": 1,
            "name": "De Aquí Pa'llá",
            "logo": "/media/logos/logo.png"
        },
        "driver_info": {
            "driver_number": "001",
            "driver_status": "approved",
            "plate_number": "ABC123",
            "car_model": "Toyota Corolla",
            "car_color": "Blanco"
        }
    }
    """
    try:
        user = request.user
        
        # Datos básicos del usuario
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'national_id': user.national_id,
            'role': user.role,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        }
        
        # Información de la organización
        if user.organization:
            profile_data['organization'] = {
                'id': user.organization.id,
                'name': user.organization.name,
                'logo': user.organization.logo.url if user.organization.logo else None,
            }
        else:
            profile_data['organization'] = None
        
        # Información específica del conductor
        if user.role == 'driver':
            try:
                taxi = user.taxi
                profile_data['driver_info'] = {
                    'driver_number': user.driver_number,
                    'driver_status': user.driver_status,
                    'plate_number': taxi.plate_number,
                    'car_model': taxi.car_model,
                    'car_color': taxi.car_color,
                    'car_year': taxi.car_year,
                }
            except:
                profile_data['driver_info'] = {
                    'driver_number': user.driver_number,
                    'driver_status': user.driver_status,
                    'plate_number': None,
                    'car_model': None,
                    'car_color': None,
                    'car_year': None,
                }
        
        return Response({
            'success': True,
            'profile': profile_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al obtener perfil: {str(e)}")
        return Response({
            'error': f'Error al obtener perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    """
    Actualizar información del perfil del usuario
    
    Body:
    {
        "first_name": "Carlos",
        "last_name": "Rodríguez",
        "phone_number": "555-1234",
        "email": "carlos@example.com",
        "profile_picture": <file>  // opcional
    }
    
    Returns:
    {
        "success": true,
        "message": "Perfil actualizado exitosamente",
        "profile": {...}
    }
    """
    try:
        user = request.user
        
        # Actualizar campos básicos
        if 'first_name' in request.data:
            user.first_name = request.data['first_name']
        
        if 'last_name' in request.data:
            user.last_name = request.data['last_name']
        
        if 'phone_number' in request.data:
            user.phone_number = request.data['phone_number']
        
        if 'email' in request.data:
            # Validar que el email no esté en uso por otro usuario
            email = request.data['email']
            if AppUser.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({
                    'error': 'Este email ya está en uso por otro usuario'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.email = email
        
        # Actualizar foto de perfil si se envió
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        
        print(f"✅ Perfil actualizado: {user.get_full_name()}")
        
        # Devolver perfil actualizado
        profile_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'national_id': user.national_id,
            'role': user.role,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        }
        
        return Response({
            'success': True,
            'message': 'Perfil actualizado exitosamente',
            'profile': profile_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al actualizar perfil: {str(e)}")
        return Response({
            'error': f'Error al actualizar perfil: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_driver_vehicle(request):
    """
    Actualizar información del vehículo del conductor
    
    Body:
    {
        "plate_number": "ABC123",
        "car_model": "Toyota Corolla",
        "car_color": "Blanco",
        "car_year": 2020
    }
    """
    try:
        user = request.user
        
        # Validar que sea conductor
        if user.role != 'driver':
            return Response({
                'error': 'Solo conductores pueden actualizar información del vehículo'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener o crear taxi
        try:
            taxi = user.taxi
        except:
            from .models import Taxi
            taxi = Taxi.objects.create(driver=user)
        
        # Actualizar campos
        if 'plate_number' in request.data:
            taxi.plate_number = request.data['plate_number']
        
        if 'car_model' in request.data:
            taxi.car_model = request.data['car_model']
        
        if 'car_color' in request.data:
            taxi.car_color = request.data['car_color']
        
        if 'car_year' in request.data:
            taxi.car_year = request.data['car_year']
        
        taxi.save()
        
        print(f"✅ Vehículo actualizado: {taxi.plate_number}")
        
        return Response({
            'success': True,
            'message': 'Información del vehículo actualizada',
            'vehicle': {
                'plate_number': taxi.plate_number,
                'car_model': taxi.car_model,
                'car_color': taxi.car_color,
                'car_year': taxi.car_year,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error al actualizar vehículo: {str(e)}")
        return Response({
            'error': f'Error al actualizar vehículo: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifications_settings(request):
    """
    Obtener configuración de notificaciones del usuario
    
    Returns:
    {
        "push_enabled": true,
        "email_enabled": false,
        "sms_enabled": false,
        "ride_notifications": true,
        "chat_notifications": true,
        "audio_notifications": true
    }
    """
    try:
        user = request.user
        
        # Por ahora devolvemos valores por defecto
        # En el futuro se puede crear un modelo NotificationSettings
        settings = {
            'push_enabled': True,
            'email_enabled': False,
            'sms_enabled': False,
            'ride_notifications': True,
            'chat_notifications': True,
            'audio_notifications': True,
        }
        
        return Response({
            'success': True,
            'settings': settings
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener configuración: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
