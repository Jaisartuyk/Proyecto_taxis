"""
API Views para Firebase Cloud Messaging (FCM)
Endpoints para registrar/desregistrar tokens desde Flutter
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .fcm_notifications import (
    register_fcm_token,
    unregister_fcm_token,
    send_fcm_notification
)
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token_view(request):
    """
    POST /api/fcm/register/
    
    Registrar token FCM del dispositivo móvil
    
    Request Body:
    {
        "token": "fcm_token_here",
        "platform": "android",  // android, ios, web
        "device_id": "unique_device_id"  // opcional
    }
    """
    token = request.data.get('token')
    platform = request.data.get('platform', 'android')
    device_id = request.data.get('device_id')
    
    if not token:
        return Response(
            {'error': 'Se requiere el token FCM'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        fcm_token = register_fcm_token(
            user=request.user,
            token=token,
            platform=platform,
            device_id=device_id
        )
        
        return Response({
            'success': True,
            'message': 'Token FCM registrado exitosamente',
            'token_id': fcm_token.id,
            'platform': fcm_token.platform
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error registrando token FCM: {e}")
        return Response(
            {'error': f'Error registrando token: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unregister_fcm_token_view(request):
    """
    POST /api/fcm/unregister/
    
    Desregistrar token FCM (cuando el usuario cierra sesión)
    
    Request Body:
    {
        "token": "fcm_token_here"
    }
    """
    token = request.data.get('token')
    
    if not token:
        return Response(
            {'error': 'Se requiere el token FCM'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    success = unregister_fcm_token(token)
    
    if success:
        return Response({
            'success': True,
            'message': 'Token FCM eliminado exitosamente'
        })
    else:
        return Response({
            'success': False,
            'message': 'Token no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_fcm_notification_view(request):
    """
    POST /api/fcm/test/
    
    Enviar notificación de prueba al usuario actual
    
    Request Body:
    {
        "title": "Título de prueba",
        "body": "Mensaje de prueba"
    }
    """
    title = request.data.get('title', '🧪 Notificación de Prueba')
    body = request.data.get('body', 'Esta es una notificación de prueba desde la API')
    
    result = send_fcm_notification(
        user=request.user,
        title=title,
        body=body,
        data={'type': 'test'}
    )
    
    if result['success']:
        return Response({
            'success': True,
            'message': 'Notificación enviada',
            'sent': result['sent'],
            'failed': result['failed']
        })
    else:
        return Response({
            'success': False,
            'error': result.get('error', 'Error desconocido')
        }, status=status.HTTP_400_BAD_REQUEST)
