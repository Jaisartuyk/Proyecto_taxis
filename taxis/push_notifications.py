"""
Push Notifications Module
Handles sending web push notifications to users
"""
from pywebpush import webpush, WebPushException
from django.conf import settings
import json
import logging
import time

logger = logging.getLogger(__name__)


def send_push_notification(user, title, body, data=None, icon=None, badge=None):
    """
    Send a push notification to a specific user
    
    Args:
        user: User object to send notification to
        title: Notification title
        body: Notification body text
        data: Optional dict with custom data
        icon: Optional icon URL
        badge: Optional badge URL
    
    Returns:
        int: Number of successful sends
    """
    from taxis.models import WebPushSubscription
    
    # Validate input parameters
    if not user:
        logger.error("No user provided for push notification")
        return 0
        
    if not isinstance(title, str):
        logger.error(f"Title must be a string, got {type(title)}")
        return 0
        
    if not isinstance(body, str):
        logger.error(f"Body must be a string, got {type(body)}")
        return 0
        
            # Ensure data is a dict or None
    if data is not None and not isinstance(data, dict):
        logger.warning(f"Data parameter must be a dict, got {type(data)}, converting to dict")
        try:
            if isinstance(data, str):
                import json as json_lib
                data = json_lib.loads(data)
            else:
                data = {}
        except:
            logger.warning("Could not convert data to dict, using empty dict")
            data = {}
    
    subscriptions = WebPushSubscription.objects.filter(user=user)
    
    if not subscriptions.exists():
        logger.info(f"No push subscriptions found for user {user.username}")
        return 0
    
    # Prepare notification payload
    payload = {
        "title": str(title),
        "body": str(body),
        "icon": icon or "/static/imagenes/DE_AQU_PALL_Logo.png",
        "badge": badge or "/static/imagenes/logo1.png",
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    
    success_count = 0
    expired_subscriptions = []
    
    for subscription in subscriptions:
        try:
            # Validate subscription_info
            if not hasattr(subscription, 'subscription_info') or not subscription.subscription_info:
                logger.warning(f"Invalid subscription_info for user {user.username}")
                continue
                
            # subscription_info should already be a dict thanks to JSONField
            subscription_info = subscription.subscription_info
            
            if not isinstance(subscription_info, dict):
                logger.warning(f"subscription_info must be a dict, got {type(subscription_info)}")
                continue
                
            # Construir audience correctamente para VAPID
            endpoint = subscription_info.get('endpoint', '')
            if not endpoint:
                logger.warning(f"Missing endpoint for user {user.username}")
                continue
                
            from urllib.parse import urlparse
            parsed_endpoint = urlparse(endpoint)
            aud = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
            
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
                vapid_claims={
                    "sub": f"mailto:{settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}",
                    "aud": aud
                }
            )
            success_count += 1
            logger.info(f"📱 Notificación push enviada a {user.username}")
            
        except WebPushException as e:
            # If subscription is expired or invalid, mark for deletion
            if e.response and e.response.status_code in [404, 410]:
                logger.warning(f"⚠️ Suscripción expirada para {user.username} - será eliminada")
                expired_subscriptions.append(subscription.id)
            else:
                logger.error(f"❌ Error al enviar notificación push: {e}")
        except Exception as e:
            logger.error(f"❌ Error inesperado al enviar notificación push: {e}")
            logger.error(f"Debug - payload: {payload}")
            logger.error(f"Debug - subscription_info type: {type(subscription.subscription_info)}")
            logger.error(f"Debug - subscription_info: {subscription.subscription_info}")
    
    # Clean up expired subscriptions
    if expired_subscriptions:
        WebPushSubscription.objects.filter(id__in=expired_subscriptions).delete()
        logger.info(f"Removed {len(expired_subscriptions)} expired subscriptions")
    
    return success_count


def send_push_to_all_drivers(title, body, data=None):
    """
    Send a push notification to all drivers
    
    Args:
        title: Notification title
        body: Notification body text
        data: Optional dict with custom data
    
    Returns:
        int: Number of successful sends
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    drivers = User.objects.filter(role='driver', is_active=True)
    total_sent = 0
    
    for driver in drivers:
        sent = send_push_notification(driver, title, body, data)
        total_sent += sent
    
    logger.info(f"Sent push notification to {total_sent} drivers")
    return total_sent


def send_new_ride_notification(ride):
    """
    Send notification about a new ride to all available drivers
    
    Args:
        ride: Ride object
    """
    title = "🚕 Nueva Carrera Disponible"
    body = f"Origen: {ride.origin}"
    data = {
        "type": "new_ride",
        "ride_id": ride.id,
        "url": f"/ride/{ride.id}/"
    }
    
    return send_push_to_all_drivers(title, body, data)


def send_chat_message_notification(sender, recipient, message):
    """
    Send notification about a new chat message
    
    Args:
        sender: User who sent the message
        recipient: User who should receive the notification
        message: Message text
    """
    title = f"💬 Mensaje de {sender.get_full_name()}"
    body = message[:100]  # Truncate long messages
    data = {
        "type": "chat_message",
        "sender_id": sender.id,
        "url": "/central-comunicacion/" if recipient.is_superuser else "/comunicacion-conductores/"
    }
    
    return send_push_notification(recipient, title, body, data)


def send_audio_message_notification(sender, recipient):
    """
    Send notification about a new audio message
    
    Args:
        sender: User who sent the audio
        recipient: User who should receive the notification
    """
    title = f"🎤 Mensaje de Audio de {sender.get_full_name()}"
    body = "Toca para escuchar"
    data = {
        "type": "audio_message",
        "sender_id": sender.id,
        "url": "/central-comunicacion/" if recipient.is_superuser else "/comunicacion-conductores/"
    }
    
    return send_push_notification(recipient, title, body, data)


import time
