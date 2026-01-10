"""
Plantillas de mensajes de emergencia para ECU-911 y UPC
Formato optimizado para envío único y respuesta rápida
"""

from datetime import datetime


def get_emergency_message_template(emergency_type, data):
    """
    Genera mensaje de emergencia formateado según el tipo
    
    Args:
        emergency_type: 'driver_panic', 'client_panic', 'accident', 'robbery', etc.
        data: Diccionario con datos de la emergencia
    
    Returns:
        str: Mensaje formateado listo para enviar
    """
    templates = {
        'driver_panic': _template_driver_panic,
        'client_panic': _template_client_panic,
        'accident': _template_accident,
        'robbery': _template_robbery,
        'medical': _template_medical,
        'vehicle_breakdown': _template_vehicle_breakdown,
    }
    
    template_func = templates.get(emergency_type, _template_generic)
    return template_func(data)


def _template_driver_panic(data):
    """Plantilla para pánico del conductor"""
    return f"""🚨 EMERGENCIA TAXI - CONDUCTOR EN PELIGRO

⚠️ TIPO: BOTÓN DE PÁNICO ACTIVADO
🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

👤 CONDUCTOR:
   Nombre: {data.get('conductor_nombre')}
   Cédula: {data.get('conductor_cedula')}
   Teléfono: {data.get('conductor_telefono')}

🚗 VEHÍCULO:
   Placa: {data.get('placa')}
   Marca/Modelo: {data.get('marca')} {data.get('modelo')}
   Color: {data.get('color', 'N/A')}
   Unidad #: {data.get('driver_number', 'N/A')}

👥 PASAJERO:
   Nombre: {data.get('cliente_nombre', 'N/A')}
   Teléfono: {data.get('cliente_telefono', 'N/A')}

📋 CARRERA:
   ID: #{data.get('ride_id')}
   Origen: {data.get('origen', 'N/A')}
   Destino: {data.get('destino', 'N/A')}

⏰ Hora de alerta: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

⚡ REQUIERE ATENCIÓN INMEDIATA"""


def _template_client_panic(data):
    """Plantilla para pánico del cliente"""
    return f"""🚨 EMERGENCIA TAXI - CLIENTE EN PELIGRO

⚠️ TIPO: BOTÓN DE PÁNICO - PASAJERO
🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

👥 PASAJERO:
   Nombre: {data.get('cliente_nombre')}
   Cédula: {data.get('cliente_cedula', 'N/A')}
   Teléfono: {data.get('cliente_telefono')}

🚗 VEHÍCULO:
   Placa: {data.get('placa')}
   Marca/Modelo: {data.get('marca')} {data.get('modelo')}
   Color: {data.get('color', 'N/A')}
   Unidad #: {data.get('driver_number', 'N/A')}

👤 CONDUCTOR:
   Nombre: {data.get('conductor_nombre')}
   Teléfono: {data.get('conductor_telefono')}

📋 CARRERA:
   ID: #{data.get('ride_id')}
   Origen: {data.get('origen', 'N/A')}
   Destino: {data.get('destino', 'N/A')}

⏰ Hora de alerta: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

⚡ REQUIERE ATENCIÓN INMEDIATA"""


def _template_accident(data):
    """Plantilla para accidente de tránsito"""
    return f"""🚨 EMERGENCIA - ACCIDENTE DE TRÁNSITO

⚠️ TIPO: ACCIDENTE VIAL
🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

🚗 VEHÍCULO:
   Placa: {data.get('placa')}
   Marca/Modelo: {data.get('marca')} {data.get('modelo')}

👤 CONDUCTOR:
   Nombre: {data.get('conductor_nombre')}
   Teléfono: {data.get('conductor_telefono')}

🏥 Heridos: {data.get('hay_heridos', 'Desconocido')}
🔥 Fuego: {data.get('hay_fuego', 'No')}
🚑 Ambulancia requerida: {data.get('necesita_ambulancia', 'Sí')}

⏰ Hora: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

⚡ REQUIERE ATENCIÓN INMEDIATA"""


def _template_robbery(data):
    """Plantilla para robo/asalto"""
    return f"""🚨 EMERGENCIA - ROBO EN PROGRESO

⚠️ TIPO: ASALTO/ROBO
🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

🚗 VEHÍCULO:
   Placa: {data.get('placa')}
   Marca/Modelo: {data.get('marca')} {data.get('modelo')}
   Color: {data.get('color', 'N/A')}

👤 CONDUCTOR:
   Nombre: {data.get('conductor_nombre')}
   Teléfono: {data.get('conductor_telefono')}

⚠️ Sospechosos: {data.get('num_sospechosos', 'Desconocido')}
🔫 Armados: {data.get('hay_armas', 'Desconocido')}

⏰ Hora: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

⚡⚡⚡ PRIORIDAD MÁXIMA - PELIGRO INMINENTE"""


def _template_medical(data):
    """Plantilla para emergencia médica"""
    return f"""🚨 EMERGENCIA MÉDICA

⚠️ TIPO: EMERGENCIA MÉDICA
🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

🏥 PACIENTE:
   Nombre: {data.get('paciente_nombre')}
   Teléfono: {data.get('paciente_telefono', 'N/A')}
   Síntomas: {data.get('sintomas', 'No especificado')}
   Consciente: {data.get('consciente', 'Desconocido')}

🚑 AMBULANCIA REQUERIDA

👤 REPORTA:
   Nombre: {data.get('reporta_nombre')}
   Teléfono: {data.get('reporta_telefono')}

⏰ Hora: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

⚡ REQUIERE ATENCIÓN MÉDICA URGENTE"""


def _template_vehicle_breakdown(data):
    """Plantilla para avería de vehículo"""
    return f"""⚠️ AVERÍA DE VEHÍCULO

🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

🚗 VEHÍCULO:
   Placa: {data.get('placa')}
   Marca/Modelo: {data.get('marca')} {data.get('modelo')}

👤 CONDUCTOR:
   Nombre: {data.get('conductor_nombre')}
   Teléfono: {data.get('conductor_telefono')}

🔧 Problema: {data.get('problema', 'No especificado')}
🚧 Obstruyendo vía: {data.get('obstruye_via', 'No')}

⏰ Hora: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

Requiere asistencia vial"""


def _template_generic(data):
    """Plantilla genérica para cualquier emergencia"""
    return f"""🚨 ALERTA DE EMERGENCIA

🚖 Cooperativa: {data.get('cooperativa', 'N/A')}
📍 UBICACIÓN: {data.get('direccion', 'Obteniendo...')}
🗺️ Coordenadas: {data.get('lat')}, {data.get('lng')}
🔗 Google Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}

🚗 Placa: {data.get('placa', 'N/A')}
👤 Conductor: {data.get('conductor_nombre', 'N/A')}
📞 Teléfono: {data.get('conductor_telefono', 'N/A')}

📋 Carrera ID: #{data.get('ride_id', 'N/A')}

⏰ Hora: {data.get('timestamp', datetime.now().strftime('%d/%m/%Y %H:%M:%S'))}

Requiere atención"""


# Plantillas cortas para SMS (límite 160 caracteres)
def get_sms_template(emergency_type, data):
    """Genera mensaje SMS corto (máx 160 caracteres)"""
    return f"""🚨 EMERGENCIA TAXI
Placa: {data.get('placa')}
Ubic: {data.get('lat')},{data.get('lng')}
Maps: https://maps.google.com/?q={data.get('lat')},{data.get('lng')}
Coop: {data.get('cooperativa')}
Conductor: {data.get('conductor_telefono')}"""[:160]


# Plantilla para notificación interna (admin dashboard)
def get_admin_notification_template(emergency_type, data):
    """Plantilla para notificaciones internas del sistema"""
    emoji_map = {
        'driver_panic': '🚨',
        'client_panic': '⚠️',
        'accident': '🚗💥',
        'robbery': '🔴',
        'medical': '🏥',
        'vehicle_breakdown': '🔧',
    }
    
    emoji = emoji_map.get(emergency_type, '⚠️')
    
    return {
        'title': f"{emoji} EMERGENCIA: {emergency_type.replace('_', ' ').upper()}",
        'message': f"Conductor: {data.get('conductor_nombre')}\nPlaca: {data.get('placa')}\nCarrera: #{data.get('ride_id')}",
        'location': {
            'lat': data.get('lat'),
            'lng': data.get('lng'),
            'address': data.get('direccion')
        },
        'priority': 'critical',
        'sound': 'emergency_alert.mp3'
    }
