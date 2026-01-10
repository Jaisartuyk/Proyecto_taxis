"""
Sistema de notificaciones de emergencia a ECU-911 y UPC
Implementación Fase 1: WhatsApp, SMS y llamadas automáticas
"""

import logging
from geopy.distance import geodesic
from django.conf import settings
from ..data.upc_guayaquil import UPC_GUAYAQUIL, EMERGENCY_CONTACTS
from .emergency_templates import (
    get_emergency_message_template,
    get_sms_template,
    get_admin_notification_template
)

logger = logging.getLogger(__name__)


def get_nearest_upc(latitude, longitude):
    """
    Encuentra la UPC más cercana a una ubicación
    
    Args:
        latitude: Latitud GPS
        longitude: Longitud GPS
    
    Returns:
        dict: UPC más cercana con distancia en km
    """
    if not latitude or not longitude:
        logger.error("❌ Coordenadas inválidas para buscar UPC")
        return None
    
    user_location = (latitude, longitude)
    
    try:
        nearest_upc = min(
            UPC_GUAYAQUIL,
            key=lambda upc: geodesic(user_location, (upc['lat'], upc['lng'])).km
        )
        
        distance = geodesic(
            user_location,
            (nearest_upc['lat'], nearest_upc['lng'])
        ).km
        
        result = {
            **nearest_upc,
            'distance_km': round(distance, 2)
        }
        
        logger.info(f"🚓 UPC más cercana: {nearest_upc['nombre']} ({distance:.2f} km)")
        return result
        
    except Exception as e:
        logger.error(f"❌ Error calculando UPC cercana: {e}")
        return None


def send_whatsapp_to_ecu911(emergency_data):
    """
    Envía alerta de emergencia por WhatsApp a ECU-911
    
    Args:
        emergency_data: Diccionario con datos de la emergencia
    
    Returns:
        bool: True si se envió exitosamente
    """
    try:
        # Verificar que Twilio esté configurado
        if not hasattr(settings, 'TWILIO_ACCOUNT_SID') or not settings.TWILIO_ACCOUNT_SID:
            logger.warning("⚠️ Twilio no configurado - No se puede enviar WhatsApp a ECU-911")
            return False
        
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Generar mensaje con plantilla
        emergency_type = emergency_data.get('type', 'driver_panic')
        message_body = get_emergency_message_template(emergency_type, emergency_data)
        
        # Enviar WhatsApp
        ecu911_whatsapp = EMERGENCY_CONTACTS['ecu911']['whatsapp']
        
        message = client.messages.create(
            body=message_body,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{ecu911_whatsapp}"
        )
        
        logger.critical(
            f"🚨 WhatsApp enviado a ECU-911 | SID: {message.sid} | "
            f"Emergencia: {emergency_data.get('ride_id')} | "
            f"Conductor: {emergency_data.get('conductor_nombre')}"
        )
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando WhatsApp a ECU-911: {e}")
        return False


def send_sms_to_ecu911(emergency_data):
    """
    Envía SMS de emergencia a ECU-911 (fallback si WhatsApp falla)
    
    Args:
        emergency_data: Diccionario con datos de la emergencia
    
    Returns:
        bool: True si se envió exitosamente
    """
    try:
        if not hasattr(settings, 'TWILIO_ACCOUNT_SID') or not settings.TWILIO_ACCOUNT_SID:
            logger.warning("⚠️ Twilio no configurado - No se puede enviar SMS")
            return False
        
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Mensaje corto para SMS
        message_body = get_sms_template(
            emergency_data.get('type', 'driver_panic'),
            emergency_data
        )
        
        ecu911_sms = EMERGENCY_CONTACTS['ecu911']['sms']
        
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=ecu911_sms
        )
        
        logger.critical(f"📱 SMS enviado a ECU-911 | SID: {message.sid}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error enviando SMS a ECU-911: {e}")
        return False


def notify_nearest_upc(emergency_data):
    """
    Notifica a la UPC más cercana mediante SMS
    
    Args:
        emergency_data: Diccionario con datos de la emergencia
    
    Returns:
        dict: Información de la UPC notificada o None
    """
    try:
        latitude = emergency_data.get('lat')
        longitude = emergency_data.get('lng')
        
        # Encontrar UPC más cercana
        upc = get_nearest_upc(latitude, longitude)
        
        if not upc:
            logger.error("❌ No se pudo encontrar UPC cercana")
            return None
        
        # Verificar Twilio
        if not hasattr(settings, 'TWILIO_ACCOUNT_SID') or not settings.TWILIO_ACCOUNT_SID:
            logger.warning(f"⚠️ Twilio no configurado - UPC identificada: {upc['nombre']}")
            return upc
        
        from twilio.rest import Client
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Generar mensaje
        emergency_type = emergency_data.get('type', 'driver_panic')
        message_body = get_emergency_message_template(emergency_type, emergency_data)
        
        # Agregar información de distancia
        message_body += f"\n\n🚓 UPC MÁS CERCANA: {upc['nombre']}\n📏 Distancia: {upc['distance_km']} km"
        
        # Enviar SMS a UPC
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=upc['telefono']
        )
        
        logger.critical(
            f"🚓 UPC NOTIFICADA: {upc['nombre']} | "
            f"Distancia: {upc['distance_km']} km | "
            f"SID: {message.sid}"
        )
        
        return upc
        
    except Exception as e:
        logger.error(f"❌ Error notificando UPC: {e}")
        return None


def trigger_emergency_notifications(emergency_data):
    """
    Activa TODAS las notificaciones de emergencia
    
    Este es el método principal que se llama cuando se activa el botón de pánico.
    Envía notificaciones a:
    1. ECU-911 (WhatsApp + SMS)
    2. UPC más cercana (SMS)
    3. Admin de cooperativa (WebSocket - manejado por el caller)
    
    Args:
        emergency_data: dict con todos los datos de la emergencia
    
    Returns:
        dict: Resultado de las notificaciones
    """
    results = {
        'ecu911_whatsapp': False,
        'ecu911_sms': False,
        'upc_notified': None,
        'errors': []
    }
    
    logger.critical(
        f"\n{'='*60}\n"
        f"🚨🚨🚨 EMERGENCIA ACTIVADA 🚨🚨🚨\n"
        f"Tipo: {emergency_data.get('type', 'N/A')}\n"
        f"Carrera: #{emergency_data.get('ride_id', 'N/A')}\n"
        f"Conductor: {emergency_data.get('conductor_nombre', 'N/A')}\n"
        f"Ubicación: {emergency_data.get('lat')}, {emergency_data.get('lng')}\n"
        f"{'='*60}"
    )
    
    # 1. Intentar WhatsApp a ECU-911
    try:
        results['ecu911_whatsapp'] = send_whatsapp_to_ecu911(emergency_data)
    except Exception as e:
        error_msg = f"Error WhatsApp ECU-911: {str(e)}"
        results['errors'].append(error_msg)
        logger.error(f"❌ {error_msg}")
    
    # 2. Si WhatsApp falla, enviar SMS a ECU-911
    if not results['ecu911_whatsapp']:
        try:
            results['ecu911_sms'] = send_sms_to_ecu911(emergency_data)
        except Exception as e:
            error_msg = f"Error SMS ECU-911: {str(e)}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    
    # 3. Notificar UPC más cercana
    try:
        results['upc_notified'] = notify_nearest_upc(emergency_data)
    except Exception as e:
        error_msg = f"Error notificando UPC: {str(e)}"
        results['errors'].append(error_msg)
        logger.error(f"❌ {error_msg}")
    
    # Log final
    success_count = sum([
        results['ecu911_whatsapp'],
        results['ecu911_sms'],
        results['upc_notified'] is not None
    ])
    
    logger.critical(
        f"📊 RESULTADO NOTIFICACIONES: {success_count}/3 exitosas | "
        f"ECU-911 WhatsApp: {'✅' if results['ecu911_whatsapp'] else '❌'} | "
        f"ECU-911 SMS: {'✅' if results['ecu911_sms'] else '❌'} | "
        f"UPC: {'✅' if results['upc_notified'] else '❌'}"
    )
    
    return results


def get_emergency_call_url():
    """
    Retorna URL para llamar directamente a 911
    Para uso en frontend (PWA y Android)
    """
    return "tel:911"


def get_emergency_contacts_for_frontend():
    """
    Retorna lista de contactos de emergencia para mostrar en frontend
    """
    return {
        'ecu911': {
            'nombre': 'ECU-911',
            'telefono': '911',
            'url': 'tel:911',
            'icono': '🚨'
        },
        'policia': {
            'nombre': 'Policía Nacional',
            'telefono': '101',
            'url': 'tel:101',
            'icono': '🚓'
        },
        'bomberos': {
            'nombre': 'Bomberos',
            'telefono': '102',
            'url': 'tel:102',
            'icono': '🚒'
        },
        'cruz_roja': {
            'nombre': 'Cruz Roja',
            'telefono': '131',
            'url': 'tel:131',
            'icono': '🏥'
        }
    }
