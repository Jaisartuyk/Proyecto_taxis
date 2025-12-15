"""
Audio Push Notifications Module
Handles sending audio notifications for walkie-talkie functionality
"""
from .push_notifications import send_push_notification
import json
import logging
import base64

logger = logging.getLogger(__name__)


def send_audio_push_notification(sender, recipients, audio_data=None, message_type="audio"):
    """
    Send push notification for audio messages (walkie-talkie style)
    
    Args:
        sender: User who sent the audio
        recipients: List of users or single user to receive notification
        audio_data: Base64 audio data (optional)
        message_type: Type of audio message
    """
    if not isinstance(recipients, list):
        recipients = [recipients]
    
    # Preparar datos del audio
    audio_payload = {
        "type": "audio_message",
        "sender_id": sender.id,
        "sender_name": sender.get_full_name() or sender.username,
        "sender_role": getattr(sender, 'role', 'Unknown'),
        "message_type": message_type,
        "timestamp": int(__import__('time').time() * 1000),
        "requires_immediate_attention": True
    }
    
    # Si hay datos de audio, incluirlos (truncado para push)
    if audio_data:
        # Solo los primeros caracteres para identificación
        audio_payload["audio_preview"] = audio_data[:50] + "..." if len(audio_data) > 50 else audio_data
        audio_payload["has_audio"] = True
    else:
        audio_payload["has_audio"] = False
    
    success_count = 0
    
    for recipient in recipients:
        try:
            # Título y mensaje dependiendo del tipo
            if message_type == "central_audio":
                title = f"📢 Mensaje de Central"
                body = f"Audio de {sender.get_full_name() or sender.username}"
                icon = "/static/imagenes/central-icon.png"
            else:
                title = f"🎤 Mensaje de Audio"
                body = f"Audio de {sender.get_full_name() or sender.username}"
                icon = "/static/imagenes/audio-icon.png"
            
            # Enviar notificación push
            result = send_push_notification(
                user=recipient,
                title=title,
                body=body,
                data=audio_payload,
                icon=icon,
                badge="/static/imagenes/audio-badge.png"
            )
            
            if result > 0:
                success_count += result
                logger.info(f"Audio push sent to {recipient.username}")
            
        except Exception as e:
            logger.error(f"Error sending audio push to {recipient.username}: {e}")
    
    return success_count


def send_central_audio_notification(sender, audio_data=None):
    """
    Send audio notification to ALL drivers (central communication)
    """
    from .models import AppUser
    
    # Obtener todos los conductores
    drivers = AppUser.objects.filter(role='driver')
    
    return send_audio_push_notification(
        sender=sender,
        recipients=list(drivers),
        audio_data=audio_data,
        message_type="central_audio"
    )


def send_private_audio_notification(sender, recipient, audio_data=None):
    """
    Send audio notification for private communication
    """
    return send_audio_push_notification(
        sender=sender,
        recipients=[recipient],
        audio_data=audio_data,
        message_type="private_audio"
    )


def notify_audio_missed(user, sender_name, audio_count=1):
    """
    Notify user of missed audio messages when they return
    """
    title = f"🔊 Audios Perdidos"
    body = f"Tienes {audio_count} mensaje(s) de audio de {sender_name}"
    
    return send_push_notification(
        user=user,
        title=title,
        body=body,
        data={
            "type": "missed_audio",
            "count": audio_count,
            "sender": sender_name,
            "action": "open_app"
        },
        icon="/static/imagenes/missed-audio-icon.png"
    )