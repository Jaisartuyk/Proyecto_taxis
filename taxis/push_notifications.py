"""
Push Notifications Module
Handles sending web push notifications to users
"""
from pywebpush import webpush, WebPushException
from django.conf import settings
import json
import logging

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
    
    subscriptions = WebPushSubscription.objects.filter(user=user)
    
    if not subscriptions.exists():
        logger.info(f"No push subscriptions found for user {user.username}")
        return 0
    
    # Prepare notification payload
    payload = {
        "title": title,
        "body": body,
        "icon": icon or "/static/imagenes/DE_AQU_PALL_Logo.png",
        "badge": badge or "/static/imagenes/logo1.png",
        "data": data or {},
        "timestamp": int(time.time() * 1000),
    }
    
    success_count = 0
    expired_subscriptions = []
    
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.subscription_info,
                data=json.dumps(payload),
                vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
                vapid_claims={
                    "sub": f"mailto:{settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL']}"
                }
            )
            success_count += 1
            logger.info(f"Push notification sent to {user.username}")
            
        except WebPushException as e:
            logger.error(f"Push notification failed for {user.username}: {e}")
            
            # If subscription is expired or invalid, mark for deletion
            if e.response and e.response.status_code in [404, 410]:
                expired_subscriptions.append(subscription.id)
    
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
