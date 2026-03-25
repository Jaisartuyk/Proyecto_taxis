"""
API endpoint para suscribirse a notificaciones push
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from taxis.models import WebPushSubscription
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    """
    Registrar suscripción de push notifications para el usuario actual
    
    POST /api/push/subscribe/
    Body:
    {
        "subscription": {
            "endpoint": "https://...",
            "keys": {
                "p256dh": "...",
                "auth": "..."
            }
        }
    }
    """
    try:
        user = request.user
        subscription_data = request.data.get('subscription')
        
        if not subscription_data:
            return Response({
                'error': 'Se requiere información de suscripción'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que tenga los campos necesarios
        if not subscription_data.get('endpoint'):
            return Response({
                'error': 'Falta el endpoint en la suscripción'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not subscription_data.get('keys'):
            return Response({
                'error': 'Faltan las keys en la suscripción'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar si ya existe una suscripción con este endpoint
        endpoint = subscription_data.get('endpoint')
        existing = WebPushSubscription.objects.filter(
            user=user,
            subscription_info__endpoint=endpoint
        ).first()
        
        if existing:
            # Actualizar suscripción existente
            existing.subscription_info = subscription_data
            existing.save()
            print(f'✅ Suscripción push actualizada para {user.username}')
            return Response({
                'success': True,
                'message': 'Suscripción actualizada correctamente',
                'subscription_id': existing.id
            }, status=status.HTTP_200_OK)
        else:
            # Crear nueva suscripción
            subscription = WebPushSubscription.objects.create(
                user=user,
                subscription_info=subscription_data
            )
            print(f'✅ Nueva suscripción push creada para {user.username}')
            return Response({
                'success': True,
                'message': 'Suscripción creada correctamente',
                'subscription_id': subscription.id
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f'❌ Error al registrar suscripción push: {e}')
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Error al registrar suscripción: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsubscribe_push(request):
    """
    Eliminar suscripción de push notifications
    
    POST /api/push/unsubscribe/
    Body:
    {
        "endpoint": "https://..."
    }
    """
    try:
        user = request.user
        endpoint = request.data.get('endpoint')
        
        if not endpoint:
            return Response({
                'error': 'Se requiere el endpoint'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar y eliminar la suscripción
        deleted_count = WebPushSubscription.objects.filter(
            user=user,
            subscription_info__endpoint=endpoint
        ).delete()[0]
        
        if deleted_count > 0:
            print(f'✅ Suscripción push eliminada para {user.username}')
            return Response({
                'success': True,
                'message': 'Suscripción eliminada correctamente'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No se encontró la suscripción'
            }, status=status.HTTP_404_NOT_FOUND)
        
    except Exception as e:
        print(f'❌ Error al eliminar suscripción push: {e}')
        return Response({
            'error': f'Error al eliminar suscripción: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vapid_public_key(request):
    """
    Obtener la clave pública VAPID para suscripciones push
    
    GET /api/push/vapid-public-key/
    """
    try:
        from django.conf import settings
        
        public_key = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')
        
        if not public_key:
            return Response({
                'error': 'Clave pública VAPID no configurada'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({
            'public_key': public_key
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f'❌ Error al obtener clave VAPID: {e}')
        return Response({
            'error': f'Error al obtener clave VAPID: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
