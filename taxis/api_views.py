from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone
from .models import Taxi
  # Asegúrate que el import sea correcto

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
        
        # TODO: Cuando tengas el modelo de Carreras, usar datos reales
        # Por ahora, retornar datos de ejemplo
        stats = {
            'total_rides': 12,
            'total_earnings': '45.50',
            'average_rating': 4.8,
            'total_hours': 5
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
        
        # TODO: Cuando tengas el modelo de Carreras, usar datos reales
        # Por ahora, retornar datos de ejemplo
        from datetime import datetime, timedelta
        
        rides = [
            {
                'id': 1,
                'origin': 'Av. Principal 123',
                'destination': 'Centro Comercial',
                'created_at': (datetime.now() - timedelta(minutes=15)).isoformat(),
                'amount': '5.50',
                'status': 'completed',
                'rating': 5,
            },
            {
                'id': 2,
                'origin': 'Plaza Mayor',
                'destination': 'Aeropuerto Internacional',
                'created_at': (datetime.now() - timedelta(hours=2)).isoformat(),
                'amount': '15.00',
                'status': 'completed',
                'rating': 5,
            },
            {
                'id': 3,
                'origin': 'Hospital Central',
                'destination': 'Universidad Nacional',
                'created_at': (datetime.now() - timedelta(hours=4)).isoformat(),
                'amount': '8.00',
                'status': 'completed',
                'rating': 4,
            },
            {
                'id': 4,
                'origin': 'Estación de Tren',
                'destination': 'Hotel Marriott',
                'created_at': (datetime.now() - timedelta(days=1)).isoformat(),
                'amount': '12.00',
                'status': 'completed',
                'rating': 5,
            },
            {
                'id': 5,
                'origin': 'Parque Central',
                'destination': 'Zona Industrial',
                'created_at': (datetime.now() - timedelta(days=2)).isoformat(),
                'amount': '10.00',
                'status': 'cancelled',
                'rating': 0,
            },
        ]
        
        return Response(rides, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Error al obtener historial: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
