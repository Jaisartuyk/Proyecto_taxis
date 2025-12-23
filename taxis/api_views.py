from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from .models import Taxi, Ride, RideDestination
from datetime import datetime, timedelta

User = get_user_model()

# 🚕 Login para conductores
class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                token, created = Token.objects.get_or_create(user=user)
                role = getattr(user, 'role', None)

                if role == 'driver':
                    return Response({
                        "message": "Inicio de sesión exitoso.",
                        "user_id": user.id,
                        "role": role,
                        "token": token.key
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
        
        # Obtener carreras solicitadas (sin conductor asignado)
        rides = Ride.objects.filter(
            status='requested',
            driver__isnull=True
        ).select_related('customer').prefetch_related('destinations').order_by('-created_at')
        
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
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id, status='requested', driver__isnull=True)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no disponible'
            }, status=status.HTTP_404_NOT_FOUND)
        
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
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id, driver=user)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que la carrera no esté completada
        if ride.status == 'completed':
            return Response({
                'error': 'No se puede cancelar una carrera completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancelar carrera
        ride.status = 'canceled'
        ride.driver = None  # Liberar conductor
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
