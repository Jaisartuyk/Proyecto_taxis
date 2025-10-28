"""
Asistente de IA Simple (sin Claude) con conversaciones naturales
Sistema basado en reglas inteligentes
"""
import logging
import random

logger = logging.getLogger(__name__)


class SimpleAIAssistant:
    """Asistente de IA simple con conversaciones naturales sin necesidad de Claude"""
    
    def __init__(self):
        self.saludos = [
            "¡Hola! 👋 ¿En qué puedo ayudarte hoy?",
            "¡Hola! 😊 Bienvenido a De Aquí Pa'llá. ¿Necesitas un taxi?",
            "¡Hola! 👋 ¿Qué necesitas? Estoy aquí para ayudarte",
            "¡Hola! 🚕 ¿Te ayudo a solicitar una carrera?"
        ]
        
        self.solicitar_origen = [
            "¡Perfecto! 🚕 ¿Desde dónde te vamos a recoger? Puedes escribir la dirección o enviarme tu ubicación 📍",
            "¡Claro que sí! 😊 ¿Cuál es tu punto de partida? Escribe la dirección o comparte tu ubicación",
            "¡Con gusto! 🚖 ¿Desde dónde te recogemos? Puedes escribir la dirección o enviar tu ubicación GPS",
            "¡Listo! 👍 Dime desde dónde te vamos a buscar. Puedes escribir la dirección o compartir tu ubicación 📍"
        ]
        
        self.solicitar_destino = [
            "Perfecto, te vamos a recoger en {origen} ✅\n\n¿Y a dónde te llevamos? Escribe el destino o envía la ubicación 🗺️",
            "¡Listo! Te recogemos en {origen} 👍\n\n¿A dónde vas? Puedes escribir la dirección o enviar la ubicación",
            "Excelente, origen confirmado: {origen} ✅\n\nAhora dime, ¿cuál es tu destino? 🎯",
            "Perfecto, te esperamos en {origen} 🚕\n\n¿A dónde te llevamos? Escribe el destino o comparte la ubicación"
        ]
        
        self.confirmaciones = [
            "¡Perfecto! ✅",
            "¡Listo! 👍",
            "¡Excelente! 🎉",
            "¡Genial! ✨"
        ]
        
        self.urgente_responses = [
            "Entiendo que es urgente, vamos rápido entonces 🚀\n",
            "¡Claro! Vamos a agilizar esto 💨\n",
            "Entendido, te ayudo rápidamente ⚡\n"
        ]
    
    def generar_respuesta_contextual(self, mensaje_usuario, estado_conversacion, datos_usuario=None):
        """
        Genera una respuesta contextual basada en el estado
        
        Args:
            mensaje_usuario: Mensaje del usuario
            estado_conversacion: Estado actual
            datos_usuario: Datos del usuario
            
        Returns:
            dict con respuesta, accion y datos_extraidos
        """
        mensaje_lower = mensaje_usuario.lower().strip()
        datos_usuario = datos_usuario or {}
        
        # Detectar urgencia
        es_urgente = any(palabra in mensaje_lower for palabra in ['urgente', 'rápido', 'ya', 'apurado', 'pronto'])
        
        # Estado: INICIO
        if estado_conversacion == 'inicio':
            return self._manejar_inicio(mensaje_lower, es_urgente)
        
        # Estado: ESPERANDO_ORIGEN
        elif estado_conversacion == 'esperando_origen':
            return self._manejar_esperando_origen(mensaje_usuario)
        
        # Estado: ESPERANDO_DESTINO
        elif estado_conversacion == 'esperando_destino':
            return self._manejar_esperando_destino(mensaje_usuario, datos_usuario)
        
        # Estado: CONFIRMANDO_CARRERA
        elif estado_conversacion == 'confirmando_carrera':
            return self._manejar_confirmacion(mensaje_lower)
        
        # Estado: CARRERA_ACTIVA
        elif estado_conversacion == 'carrera_activa':
            return self._manejar_carrera_activa(mensaje_lower)
        
        # Por defecto
        return {
            'respuesta': random.choice(self.saludos),
            'accion': 'conversacion_general',
            'datos_extraidos': {}
        }
    
    def _manejar_inicio(self, mensaje_lower, es_urgente):
        """Maneja el estado inicial"""
        
        # Saludos
        if any(palabra in mensaje_lower for palabra in ['hola', 'buenas', 'buenos', 'hey', 'hi']):
            respuesta = random.choice(self.saludos)
            return {
                'respuesta': respuesta,
                'accion': 'conversacion_general',
                'datos_extraidos': {}
            }
        
        # Solicitar taxi
        if any(palabra in mensaje_lower for palabra in ['taxi', 'carrera', 'solicitar', 'pedir', 'necesito', 'quiero']):
            prefijo = random.choice(self.urgente_responses) if es_urgente else ""
            respuesta = prefijo + random.choice(self.solicitar_origen)
            
            return {
                'respuesta': respuesta,
                'accion': 'solicitar_origen',
                'datos_extraidos': {'urgente': es_urgente}
            }
        
        # Estado
        if any(palabra in mensaje_lower for palabra in ['estado', 'cómo va', 'donde', 'ubicación']):
            return {
                'respuesta': "Para consultar el estado de tu carrera, escribe *ESTADO* 📊",
                'accion': 'consultar_estado',
                'datos_extraidos': {}
            }
        
        # Mis carreras
        if any(palabra in mensaje_lower for palabra in ['mis carreras', 'activas', 'viajes']):
            return {
                'respuesta': "Déjame revisar tus carreras activas... 🔍",
                'accion': 'listar_carreras',
                'datos_extraidos': {}
            }
        
        # Ayuda
        if any(palabra in mensaje_lower for palabra in ['ayuda', 'help', 'qué puedes']):
            respuesta = """ℹ️ *¿Cómo puedo ayudarte?*

Puedo ayudarte con:
• 🚕 Solicitar una carrera
• 📊 Ver el estado de tu carrera
• 📋 Ver tus carreras activas
• ❌ Cancelar una carrera

¿Qué necesitas? 😊"""
            return {
                'respuesta': respuesta,
                'accion': 'mostrar_ayuda',
                'datos_extraidos': {}
            }
        
        # Por defecto, ofrecer ayuda
        return {
            'respuesta': "¿Necesitas solicitar un taxi? 🚕 Escribe *SOLICITAR* o cuéntame qué necesitas 😊",
            'accion': 'conversacion_general',
            'datos_extraidos': {}
        }
    
    def _manejar_esperando_origen(self, mensaje):
        """Maneja cuando estamos esperando el origen"""
        return {
            'respuesta': "",  # La respuesta la genera el agente después de geocodificar
            'accion': 'procesar_origen',
            'datos_extraidos': {'direccion': mensaje},
            'nuevo_estado': 'esperando_origen'  # Mantener estado hasta geocodificar
        }
    
    def _manejar_esperando_destino(self, mensaje, datos_usuario):
        """Maneja cuando estamos esperando el destino"""
        return {
            'respuesta': "",  # La respuesta la genera el agente después de geocodificar
            'accion': 'procesar_destino',
            'datos_extraidos': {'direccion': mensaje},
            'nuevo_estado': 'esperando_destino'  # Mantener estado hasta geocodificar
        }
    
    def _manejar_confirmacion(self, mensaje_lower):
        """Maneja la confirmación de la carrera"""
        
        # Confirmación positiva
        if any(palabra in mensaje_lower for palabra in ['sí', 'si', 'yes', 'ok', 'confirmar', 'confirmo', 'dale', 'listo', 'claro']):
            return {
                'respuesta': random.choice(self.confirmaciones),
                'accion': 'crear_carrera',
                'datos_extraidos': {'confirmacion': True}
            }
        
        # Negación
        if any(palabra in mensaje_lower for palabra in ['no', 'cancelar', 'cancel', 'nada', 'mejor no']):
            return {
                'respuesta': "Entendido, carrera cancelada ❌\n\nEscribe *MENU* cuando quieras solicitar otra 😊",
                'accion': 'cancelar_solicitud',
                'datos_extraidos': {'negacion': True}
            }
        
        # No entendió
        return {
            'respuesta': "¿Confirmas esta carrera? 🤔\n\nResponde *SÍ* para confirmar o *NO* para cancelar",
            'accion': 'ninguna',
            'datos_extraidos': {}
        }
    
    def _manejar_carrera_activa(self, mensaje_lower):
        """Maneja comandos durante una carrera activa"""
        
        if any(palabra in mensaje_lower for palabra in ['estado', 'cómo va', 'donde']):
            return {
                'respuesta': "",  # El agente mostrará el estado
                'accion': 'consultar_estado',
                'datos_extraidos': {}
            }
        
        if any(palabra in mensaje_lower for palabra in ['cancelar', 'cancel']):
            return {
                'respuesta': "¿Estás seguro de que quieres cancelar la carrera? Responde *SÍ* para confirmar",
                'accion': 'confirmar_cancelacion',
                'datos_extraidos': {}
            }
        
        if any(palabra in mensaje_lower for palabra in ['menu', 'inicio']):
            return {
                'respuesta': random.choice(self.saludos),
                'accion': 'conversacion_general',
                'datos_extraidos': {}
            }
        
        return {
            'respuesta': """Tienes una carrera activa 🚕

Comandos disponibles:
• *ESTADO* - Ver estado de la carrera
• *CANCELAR* - Cancelar la carrera
• *MENU* - Volver al menú""",
            'accion': 'ninguna',
            'datos_extraidos': {}
        }


# Instancia global del asistente simple
simple_ai_assistant = SimpleAIAssistant()
