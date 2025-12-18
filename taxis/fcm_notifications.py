"""
Firebase Cloud Messaging (FCM) - Sistema de notificaciones push para móviles
Reemplaza Web Push para apps nativas Flutter/React Native
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model
from firebase_admin import credentials, messaging, initialize_app
import firebase_admin

logger = logging.getLogger(__name__)
User = get_user_model()

# Importar modelo FCMToken (se importa después para evitar circular imports)
def get_fcm_token_model():
    from .models import FCMToken
    return FCMToken

# =====================================================
# INICIALIZACIÓN DE FIREBASE
# =====================================================

def initialize_firebase():
    """
    Inicializar Firebase Admin SDK
    Solo se ejecuta una vez al inicio del servidor
    """
    if not firebase_admin._apps:
        try:
            # Opción 1: Usar archivo de credenciales
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                initialize_app(cred)
                logger.info("✅ Firebase inicializado con archivo de credenciales")
                return True
            
            # Opción 2: Usar JSON desde variable de entorno
            cred_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                initialize_app(cred)
                logger.info("✅ Firebase inicializado con credenciales de entorno")
                return True
            
            logger.warning("⚠️ Firebase no configurado - faltan credenciales")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {e}")
            return False
    else:
        logger.info("✅ Firebase ya estaba inicializado")
        return True


# Inicializar al importar el módulo
initialize_firebase()


# =====================================================
# FUNCIONES DE ENVÍO
# =====================================================

def send_fcm_notification(
    user: User,
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None,
    image_url: Optional[str] = None,
    sound: str = 'default'
) -> Dict[str, Any]:
    """
    Enviar notificación FCM a un usuario específico
    
    Args:
        user: Usuario destinatario
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
        image_url: URL de imagen (opcional)
        sound: Sonido de notificación
    
    Returns:
        Dict con resultados del envío
    """
    if not firebase_admin._apps:
        logger.error("❌ Firebase no está inicializado")
        return {'success': False, 'error': 'Firebase no configurado'}
    
    # Obtener tokens activos del usuario
    FCMToken = get_fcm_token_model()
    tokens = FCMToken.objects.filter(user=user, is_active=True)
    
    if not tokens.exists():
        logger.warning(f"⚠️ Usuario {user.username} no tiene tokens FCM")
        return {'success': False, 'error': 'No hay tokens registrados'}
    
    results = {
        'success': True,
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    for fcm_token in tokens:
        try:
            # ⚠️ IMPORTANTE: Para que las notificaciones funcionen cuando la app está cerrada,
            # necesitamos tanto 'notification' (para mostrar la notificación) como 'data' (para el handler)
            # Además, el payload 'data' debe tener todos los valores como strings
            
            # Convertir data a strings (FCM requiere que todos los valores sean strings)
            data_payload = {}
            if data:
                for key, value in data.items():
                    data_payload[str(key)] = str(value) if value is not None else ''
            
            # Construir mensaje
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                    image=image_url
                ),
                data=data_payload,  # Datos para el handler de background
                android=messaging.AndroidConfig(
                    priority='high',  # Alta prioridad para que llegue incluso cuando la app está cerrada
                    ttl=86400,  # 24 horas de validez
                    notification=messaging.AndroidNotification(
                        sound=sound,
                        channel_id='high_importance_channel',  # Usar el mismo canal que Flutter
                        color='#FF6B35',  # Color de la app
                        icon='ic_notification',
                        priority='high',  # Alta prioridad
                        visibility='public',  # Visible incluso cuando el dispositivo está bloqueado
                        default_sound=True,
                        default_vibrate_timings=True,
                        default_light_settings=True,
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound=sound,
                            badge=1,
                            content_available=True,  # Permite que el handler se ejecute en background
                            alert=messaging.ApsAlert(
                                title=title,
                                body=body,
                            ),
                        )
                    )
                ),
                token=fcm_token.token
            )
            
            # Enviar
            response = messaging.send(message)
            results['sent'] += 1
            logger.info(f"✅ Notificación FCM enviada a {user.username}")
            logger.info(f"   Token: {fcm_token.token[:30]}...")
            logger.info(f"   Título: {title}")
            logger.info(f"   Cuerpo: {body[:50]}...")
            logger.info(f"   Data: {data_payload}")
            logger.info(f"   Response: {response}")
            
        except messaging.UnregisteredError:
            # Token inválido - desactivar
            logger.warning(f"⚠️ Token inválido para {user.username} - desactivando")
            fcm_token.is_active = False
            fcm_token.save()
            results['failed'] += 1
            results['errors'].append('Token no registrado')
            
        except Exception as e:
            logger.error(f"❌ Error enviando a {user.username}: {e}")
            results['failed'] += 1
            results['errors'].append(str(e))
    
    return results


def send_fcm_to_multiple_users(
    users: List[User],
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Enviar notificación FCM a múltiples usuarios
    
    Args:
        users: Lista de usuarios
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
    
    Returns:
        Dict con resultados del envío
    """
    results = {
        'success': True,
        'total_users': len(users),
        'sent': 0,
        'failed': 0
    }
    
    for user in users:
        result = send_fcm_notification(user, title, body, data)
        if result['success']:
            results['sent'] += result['sent']
        results['failed'] += result.get('failed', 0)
    
    return results


def send_fcm_to_all_drivers(
    title: str,
    body: str,
    data: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Enviar notificación a todos los conductores
    
    Args:
        title: Título de la notificación
        body: Cuerpo del mensaje
        data: Datos adicionales (opcional)
    
    Returns:
        Dict con resultados del envío
    """
    drivers = User.objects.filter(role='driver')
    return send_fcm_to_multiple_users(drivers, title, body, data)


# =====================================================
# FUNCIONES ESPECÍFICAS DE LA APP
# =====================================================

def send_new_ride_notification_fcm(ride):
    """
    Notificar a conductores sobre nueva carrera
    
    Args:
        ride: Objeto Ride
    """
    drivers = User.objects.filter(role='driver')
    
    title = "🚖 Nueva Carrera Disponible"
    body = f"Origen: {ride.origin}"
    data = {
        'type': 'new_ride',
        'ride_id': str(ride.id),
        'origin': ride.origin,
        'price': str(ride.price) if ride.price else '0',
        'customer_name': ride.customer.get_full_name()
    }
    
    return send_fcm_to_multiple_users(drivers, title, body, data)


def send_ride_accepted_notification_fcm(ride):
    """
    Notificar al cliente que su carrera fue aceptada
    
    Args:
        ride: Objeto Ride
    """
    if not ride.driver:
        return {'success': False, 'error': 'No hay conductor asignado'}
    
    title = "✅ Carrera Aceptada"
    body = f"El conductor {ride.driver.get_full_name()} aceptó tu carrera"
    data = {
        'type': 'ride_accepted',
        'ride_id': str(ride.id),
        'driver_id': str(ride.driver.id),
        'driver_name': ride.driver.get_full_name(),
        'driver_phone': ride.driver.phone_number or ''
    }
    
    return send_fcm_notification(ride.customer, title, body, data)


def send_ride_started_notification_fcm(ride):
    """
    Notificar al cliente que su carrera comenzó
    
    Args:
        ride: Objeto Ride
    """
    title = "🚗 Carrera Iniciada"
    body = "Tu conductor está en camino"
    data = {
        'type': 'ride_started',
        'ride_id': str(ride.id)
    }
    
    return send_fcm_notification(ride.customer, title, body, data)


def send_ride_completed_notification_fcm(ride):
    """
    Notificar al cliente que su carrera terminó
    
    Args:
        ride: Objeto Ride
    """
    title = "🎉 Carrera Completada"
    body = f"Total: ${ride.price}. ¡Gracias por usar nuestro servicio!"
    data = {
        'type': 'ride_completed',
        'ride_id': str(ride.id),
        'price': str(ride.price) if ride.price else '0'
    }
    
    return send_fcm_notification(ride.customer, title, body, data)


def send_chat_message_notification_fcm(sender: User, recipient: User, message: str):
    """
    Notificar sobre nuevo mensaje de chat
    
    ⚠️ CRÍTICO: Esta función envía notificaciones FCM que funcionan incluso cuando la app está cerrada.
    Requiere que el token FCM esté registrado correctamente.
    
    Args:
        sender: Usuario que envía
        recipient: Usuario que recibe
        message: Contenido del mensaje
    """
    title = f"💬 {sender.get_full_name() or sender.username}"
    body = message[:100]  # Limitar a 100 caracteres
    
    # Datos para el handler de background en Flutter
    data = {
        'type': 'chat_message',
        'sender_id': str(sender.id),
        'sender_name': sender.get_full_name() or sender.username,
        'message': message,
        'click_action': 'FLUTTER_NOTIFICATION_CLICK',  # Para que Flutter maneje el tap
    }
    
    logger.info(f"📤 [FCM CHAT] Enviando notificación FCM de chat")
    logger.info(f"   De: {sender.username} (ID: {sender.id})")
    logger.info(f"   Para: {recipient.username} (ID: {recipient.id})")
    logger.info(f"   Mensaje: {message[:50]}...")
    
    # Verificar si el usuario tiene tokens FCM registrados
    FCMToken = get_fcm_token_model()
    token_count = FCMToken.objects.filter(user=recipient, is_active=True).count()
    logger.info(f"   Tokens FCM activos: {token_count}")
    
    if token_count == 0:
        logger.warning(f"⚠️ [FCM CHAT] Usuario {recipient.username} no tiene tokens FCM registrados")
        logger.warning(f"   💡 El usuario debe abrir la app y registrar su token FCM")
        return {'success': False, 'error': 'No hay tokens FCM registrados'}
    
    # Enviar notificación usando la función base (ya tiene notification + data configurados)
    result = send_fcm_notification(
        user=recipient,
        title=title,
        body=body,
        data=data,
        sound='default'
    )
    
    if result.get('sent', 0) > 0:
        logger.info(f"✅ [FCM CHAT] Notificación enviada exitosamente a {recipient.username}")
    else:
        logger.error(f"❌ [FCM CHAT] Error enviando notificación a {recipient.username}: {result.get('error', 'Desconocido')}")
    
    return result


def send_audio_message_notification_fcm(sender: User, recipient: User):
    """
    Notificar sobre nuevo mensaje de audio
    
    Args:
        sender: Usuario que envía
        recipient: Usuario que recibe
    """
    title = f"🎤 {sender.get_full_name()}"
    body = "Te envió un mensaje de audio"
    data = {
        'type': 'audio_message',
        'sender_id': str(sender.id),
        'sender_name': sender.get_full_name()
    }
    
    return send_fcm_notification(recipient, title, body, data)


# =====================================================
# FUNCIONES DE GESTIÓN DE TOKENS
# =====================================================

def register_fcm_token(user: User, token: str, platform: str = 'android', device_id: Optional[str] = None):
    """
    Registrar o actualizar token FCM de un usuario
    
    Args:
        user: Usuario
        token: Token FCM
        platform: Plataforma (android/ios/web)
        device_id: ID del dispositivo (opcional)
    
    Returns:
        FCMToken object
    """
    FCMToken = get_fcm_token_model()
    fcm_token, created = FCMToken.objects.update_or_create(
        token=token,
        defaults={
            'user': user,
            'platform': platform,
            'device_id': device_id,
            'is_active': True
        }
    )
    
    if created:
        logger.info(f"✅ Nuevo token FCM registrado para {user.username}")
    else:
        logger.info(f"🔄 Token FCM actualizado para {user.username}")
    
    return fcm_token


def unregister_fcm_token(token: str):
    """
    Desregistrar token FCM
    
    Args:
        token: Token FCM a eliminar
    """
    FCMToken = get_fcm_token_model()
    try:
        fcm_token = FCMToken.objects.get(token=token)
        fcm_token.delete()
        logger.info(f"✅ Token FCM eliminado: {token[:20]}...")
        return True
    except FCMToken.DoesNotExist:
        logger.warning(f"⚠️ Token FCM no encontrado: {token[:20]}...")
        return False
