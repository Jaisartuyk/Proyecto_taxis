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
