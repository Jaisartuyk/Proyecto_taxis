"""
Asistente de IA Inteligente con Claude (Anthropic)
Sistema conversacional avanzado con comprensión natural
"""
import logging
import os
import json
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class ClaudeAIAssistant:
    """Asistente de IA avanzado con Claude para conversaciones naturales"""
    
    def __init__(self):
        # Inicializar Claude (buscar en CLAUDE_API_KEY o ANTHROPIC_API_KEY)
        api_key = os.getenv('CLAUDE_API_KEY') or os.getenv('ANTHROPIC_API_KEY', '')
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.model = "claude-3-5-sonnet-20241022"
        
        # System prompt optimizado para taxi
        self.system_prompt = """Eres un asistente virtual inteligente para "De Aquí Pa'llá", un servicio de taxis en Ecuador.

TU PERSONALIDAD:
- Amigable, profesional y eficiente
- Usas emojis apropiados (🚕 🗺️ ✅ 👍)
- Hablas español de Ecuador de forma natural
- Eres paciente y comprensivo

TU OBJETIVO:
Ayudar a los usuarios a solicitar taxis de forma rápida y eficiente.

FLUJO DE SOLICITUD:
1. ORIGEN: Preguntar desde dónde los recogemos
2. DESTINO: Preguntar a dónde van
3. CONFIRMACIÓN: Mostrar resumen y confirmar
4. BÚSQUEDA: Buscar taxista disponible

CAPACIDADES:
- Entiendes direcciones escritas de cualquier forma
- Reconoces ubicaciones GPS
- Detectas urgencia y actúas en consecuencia
- Manejas cancelaciones y cambios
- Respondes preguntas sobre el servicio

REGLAS:
- Si el usuario dice "necesito un taxi", "una carrera", etc. → Pedir origen
- Si menciona una dirección → Extraer y confirmar
- Si envía ubicación GPS → Confirmar automáticamente
- Si dice "sí", "confirmar", "ok" → Proceder con la acción
- Si dice "no", "cancelar" → Cancelar y preguntar qué necesita
- Siempre ser claro sobre el siguiente paso

FORMATO DE RESPUESTA:
Debes responder en JSON con esta estructura:
{
    "respuesta": "Tu respuesta al usuario (con emojis)",
    "accion": "solicitar_origen|solicitar_destino|confirmar_carrera|cancelar|conversacion_general",
    "datos_extraidos": {
        "direccion": "dirección si la mencionó",
        "urgente": true/false,
        "confirmacion": true/false
    },
    "nuevo_estado": "inicio|esperando_origen|esperando_destino|confirmando_carrera|carrera_activa"
}

EJEMPLOS:
Usuario: "Necesito un taxi urgente"
Respuesta: {
    "respuesta": "¡Claro! Vamos rápido 🚀 ¿Desde dónde te recogemos? Puedes escribir la dirección o enviar tu ubicación 📍",
    "accion": "solicitar_origen",
    "datos_extraidos": {"urgente": true},
    "nuevo_estado": "esperando_origen"
}

Usuario: "Estoy en la Av. 9 de Octubre y Malecón"
Respuesta: {
    "respuesta": "Perfecto, te recogemos en Av. 9 de Octubre y Malecón ✅\n\n¿A dónde te llevamos? 🗺️",
    "accion": "solicitar_destino",
    "datos_extraidos": {"direccion": "Av. 9 de Octubre y Malecón"},
    "nuevo_estado": "esperando_destino"
}

Usuario: "Al aeropuerto"
Respuesta: {
    "respuesta": "¡Listo! 👍\n\n📍 Origen: Av. 9 de Octubre y Malecón\n🎯 Destino: Aeropuerto\n💰 Tarifa estimada: $12.50\n\n¿Confirmas la carrera? Responde SÍ para continuar",
    "accion": "confirmar_carrera",
    "datos_extraidos": {"direccion": "Aeropuerto"},
    "nuevo_estado": "confirmando_carrera"
}

Sé natural, amigable y eficiente. ¡Ayuda a los usuarios a llegar a su destino!"""
    
    def generar_respuesta_contextual(self, mensaje_usuario, estado_conversacion, datos_usuario=None):
        """
        Genera una respuesta inteligente usando Claude
        
        Args:
            mensaje_usuario: Mensaje del usuario
            estado_conversacion: Estado actual (inicio, esperando_origen, etc.)
            datos_usuario: Dict con nombre, datos (origen, destino, etc.)
            
        Returns:
            dict con respuesta, accion, datos_extraidos, nuevo_estado
        """
        try:
            # Si no hay API key, usar fallback simple
            if not self.client:
                logger.warning("⚠️ Claude API key no configurada, usando asistente simple")
                return self._fallback_simple(mensaje_usuario, estado_conversacion, datos_usuario)
            
            # Preparar contexto
            datos_usuario = datos_usuario or {}
            nombre = datos_usuario.get('nombre', 'Usuario')
            datos = datos_usuario.get('datos', {})
            
            # Construir mensaje de contexto
            contexto = f"""CONTEXTO ACTUAL:
- Estado de conversación: {estado_conversacion}
- Nombre del usuario: {nombre}
- Datos guardados: {json.dumps(datos, ensure_ascii=False)}

MENSAJE DEL USUARIO:
{mensaje_usuario}

Analiza el mensaje y responde en JSON según las instrucciones."""
            
            # Llamar a Claude
            logger.info(f"🤖 Consultando a Claude...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": contexto}
                ]
            )
            
            # Extraer respuesta
            respuesta_texto = response.content[0].text
            logger.info(f"✅ Claude respondió: {respuesta_texto[:100]}...")
            
            # Parsear JSON
            try:
                resultado = json.loads(respuesta_texto)
                
                # Validar estructura
                if 'respuesta' not in resultado:
                    raise ValueError("Respuesta sin campo 'respuesta'")
                
                # Completar campos faltantes
                resultado.setdefault('accion', 'conversacion_general')
                resultado.setdefault('datos_extraidos', {})
                resultado.setdefault('nuevo_estado', estado_conversacion)
                
                return resultado
                
            except json.JSONDecodeError:
                # Si Claude no respondió en JSON, extraer manualmente
                logger.warning("⚠️ Claude no respondió en JSON, extrayendo manualmente")
                return {
                    'respuesta': respuesta_texto,
                    'accion': 'conversacion_general',
                    'datos_extraidos': {},
                    'nuevo_estado': estado_conversacion
                }
        
        except Exception as e:
            logger.error(f"❌ Error con Claude: {e}")
            return self._fallback_simple(mensaje_usuario, estado_conversacion, datos_usuario)
    
    def _fallback_simple(self, mensaje_usuario, estado_conversacion, datos_usuario):
        """Fallback simple si Claude falla"""
        mensaje_lower = mensaje_usuario.lower().strip()
        
        # Detectar intención básica
        if any(palabra in mensaje_lower for palabra in ['taxi', 'carrera', 'necesito', 'quiero']):
            return {
                'respuesta': "¡Claro! 🚕 ¿Desde dónde te recogemos? Puedes escribir la dirección o enviar tu ubicación 📍",
                'accion': 'solicitar_origen',
                'datos_extraidos': {},
                'nuevo_estado': 'esperando_origen'
            }
        
        elif estado_conversacion == 'esperando_origen':
            return {
                'respuesta': f"Perfecto, te recogemos en {mensaje_usuario} ✅\n\n¿A dónde te llevamos? 🗺️",
                'accion': 'solicitar_destino',
                'datos_extraidos': {'direccion': mensaje_usuario},
                'nuevo_estado': 'esperando_destino'
            }
        
        elif estado_conversacion == 'esperando_destino':
            datos = datos_usuario.get('datos', {})
            origen = datos.get('origen', 'tu ubicación')
            return {
                'respuesta': f"¡Listo! 👍\n\n📍 Origen: {origen}\n🎯 Destino: {mensaje_usuario}\n\n¿Confirmas la carrera? Responde SÍ para continuar",
                'accion': 'confirmar_carrera',
                'datos_extraidos': {'direccion': mensaje_usuario},
                'nuevo_estado': 'confirmando_carrera'
            }
        
        elif estado_conversacion == 'confirmando_carrera':
            if any(palabra in mensaje_lower for palabra in ['sí', 'si', 'ok', 'confirmar', 'dale']):
                return {
                    'respuesta': "¡Perfecto! 🚕 Buscando taxista disponible...",
                    'accion': 'crear_carrera',
                    'datos_extraidos': {'confirmacion': True},
                    'nuevo_estado': 'carrera_activa'
                }
            else:
                return {
                    'respuesta': "Entendido. ¿Qué necesitas cambiar?",
                    'accion': 'cancelar',
                    'datos_extraidos': {'confirmacion': False},
                    'nuevo_estado': 'inicio'
                }
        
        else:
            return {
                'respuesta': "¡Hola! 👋 ¿En qué puedo ayudarte? Puedo ayudarte a solicitar un taxi 🚕",
                'accion': 'conversacion_general',
                'datos_extraidos': {},
                'nuevo_estado': 'inicio'
            }


# Instancia global del asistente inteligente
claude_ai_assistant = ClaudeAIAssistant()
