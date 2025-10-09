"""
Asistente de IA con Claude (Anthropic) para conversaciones naturales
"""
import anthropic
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# API Key de Claude - Configurar como variable de entorno
# Windows: $env:CLAUDE_API_KEY="tu-api-key"
# Linux/Mac: export CLAUDE_API_KEY="tu-api-key"
import os
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')


class ClaudeAssistant:
    """Asistente de IA usando Claude para conversaciones naturales"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        self.model = "claude-3-haiku-20240307"  # Claude 3 Haiku (más económico y disponible)
        
    def generar_respuesta(self, mensaje_usuario, contexto=None, historial=None):
        """
        Genera una respuesta natural usando Claude
        
        Args:
            mensaje_usuario: Mensaje del usuario
            contexto: Contexto adicional (estado de conversación, datos del usuario, etc.)
            historial: Historial de mensajes previos
            
        Returns:
            dict: {
                'respuesta': str,
                'accion': str,  # 'solicitar_origen', 'solicitar_destino', 'confirmar', etc.
                'datos_extraidos': dict
            }
        """
        try:
            # Construir el prompt del sistema
            system_prompt = self._construir_system_prompt()
            
            # Construir mensajes
            messages = []
            
            # Agregar historial si existe
            if historial:
                messages.extend(historial)
            
            # Agregar contexto si existe
            contexto_str = ""
            if contexto:
                contexto_str = f"\n\nContexto actual:\n{json.dumps(contexto, indent=2, ensure_ascii=False)}"
            
            # Agregar mensaje del usuario
            messages.append({
                "role": "user",
                "content": f"{mensaje_usuario}{contexto_str}"
            })
            
            # Llamar a Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            # Extraer respuesta
            respuesta_texto = response.content[0].text
            
            # Analizar la respuesta para extraer acciones y datos
            resultado = self._analizar_respuesta(respuesta_texto, mensaje_usuario, contexto)
            
            logger.info(f"Claude respondió: {respuesta_texto[:100]}...")
            
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error al generar respuesta con Claude: {str(e)}", exc_info=True)
            logger.error(f"📝 Mensaje del usuario: {mensaje_usuario}")
            logger.error(f"📊 Contexto: {contexto}")
            return {
                'respuesta': "Disculpa, tuve un problema al procesar tu mensaje. ¿Podrías repetirlo?",
                'accion': 'error',
                'datos_extraidos': {}
            }
    
    def _construir_system_prompt(self):
        """Construye el prompt del sistema para Claude"""
        return """Eres un asistente virtual amigable y profesional para "De Aquí Pa'llá", un servicio de taxis en Colombia. 

Tu trabajo es ayudar a los clientes a solicitar carreras de taxi de manera natural y conversacional.

PERSONALIDAD:
- Sé amigable, cálido y profesional
- Usa emojis ocasionalmente para ser más cercano (🚕 🎉 ✅ 📍)
- Habla de manera natural, como un humano
- Sé breve pero informativo
- Usa lenguaje colombiano cuando sea apropiado

CAPACIDADES:
1. Solicitar carreras de taxi
2. Consultar estado de carreras
3. Ver carreras activas
4. Cancelar carreras
5. Proporcionar ayuda

FLUJO DE SOLICITUD DE CARRERA:
1. Saludar y preguntar qué necesita
2. Solicitar dirección de origen (puede ser texto o ubicación GPS)
3. Solicitar dirección de destino
4. Mostrar resumen con tarifa estimada
5. Confirmar la carrera
6. Asignar conductor y notificar

INSTRUCCIONES IMPORTANTES:
- Si el usuario envía una ubicación GPS, confírmala y pide el destino
- Si el usuario da una dirección en texto, confírmala y geocodifícala
- Siempre confirma antes de crear una carrera
- Sé empático si hay problemas o demoras
- Si no entiendes algo, pide aclaración de manera amable

FORMATO DE RESPUESTA:
Responde SOLO con texto natural para el usuario. No uses formato JSON en tu respuesta al usuario.
Sin embargo, si necesitas indicar una acción específica, puedes usar estas palabras clave al final:
- [ACCION:solicitar_origen]
- [ACCION:solicitar_destino]
- [ACCION:confirmar_carrera]
- [ACCION:crear_carrera]
- [ACCION:consultar_estado]
- [ACCION:cancelar_carrera]

Ejemplo de buena respuesta:
"¡Hola! 👋 Claro que sí, con gusto te ayudo a solicitar un taxi. ¿Desde dónde te vamos a recoger? Puedes escribir la dirección o enviarme tu ubicación. [ACCION:solicitar_origen]"

Ejemplo de mala respuesta:
"{'accion': 'solicitar_origen', 'mensaje': 'Dime tu ubicación'}"

Recuerda: Habla como un humano amigable, no como un robot."""

    def _analizar_respuesta(self, respuesta_texto, mensaje_usuario, contexto):
        """Analiza la respuesta de Claude para extraer acciones y datos"""
        
        # Buscar acciones en la respuesta
        accion = 'ninguna'
        if '[ACCION:' in respuesta_texto:
            # Extraer la acción
            inicio = respuesta_texto.find('[ACCION:')
            fin = respuesta_texto.find(']', inicio)
            if fin > inicio:
                accion = respuesta_texto[inicio+8:fin]
                # Remover la acción del texto de respuesta
                respuesta_texto = respuesta_texto[:inicio].strip()
        
        # Intentar extraer datos del mensaje del usuario
        datos_extraidos = self._extraer_datos(mensaje_usuario, contexto)
        
        # Detectar intención si no hay acción explícita
        if accion == 'ninguna':
            accion = self._detectar_intencion(mensaje_usuario, contexto)
        
        return {
            'respuesta': respuesta_texto,
            'accion': accion,
            'datos_extraidos': datos_extraidos
        }
    
    def _extraer_datos(self, mensaje, contexto):
        """Extrae datos estructurados del mensaje"""
        datos = {}
        
        mensaje_lower = mensaje.lower()
        
        # Detectar si es una dirección
        if any(palabra in mensaje_lower for palabra in ['calle', 'carrera', 'avenida', 'av.', 'kr.', 'cl.']):
            datos['posible_direccion'] = mensaje
        
        # Detectar confirmación
        if any(palabra in mensaje_lower for palabra in ['sí', 'si', 'yes', 'ok', 'confirmar', 'dale', 'listo']):
            datos['confirmacion'] = True
        
        # Detectar negación
        if any(palabra in mensaje_lower for palabra in ['no', 'cancelar', 'cancel', 'nada']):
            datos['negacion'] = True
        
        return datos
    
    def _detectar_intencion(self, mensaje, contexto):
        """Detecta la intención del usuario basado en el mensaje y contexto"""
        mensaje_lower = mensaje.lower()
        
        # Si estamos esperando origen
        if contexto and contexto.get('estado') == 'esperando_origen':
            return 'procesar_origen'
        
        # Si estamos esperando destino
        if contexto and contexto.get('estado') == 'esperando_destino':
            return 'procesar_destino'
        
        # Si estamos esperando confirmación
        if contexto and contexto.get('estado') == 'confirmando_carrera':
            if any(palabra in mensaje_lower for palabra in ['sí', 'si', 'yes', 'ok', 'confirmar']):
                return 'crear_carrera'
            elif any(palabra in mensaje_lower for palabra in ['no', 'cancelar']):
                return 'cancelar_solicitud'
        
        # Detectar intención inicial
        if any(palabra in mensaje_lower for palabra in ['solicitar', 'pedir', 'necesito', 'quiero', 'taxi', 'carrera']):
            return 'solicitar_origen'
        
        if any(palabra in mensaje_lower for palabra in ['estado', 'cómo va', 'donde esta', 'ubicación']):
            return 'consultar_estado'
        
        if any(palabra in mensaje_lower for palabra in ['cancelar', 'anular']):
            return 'cancelar_carrera'
        
        if any(palabra in mensaje_lower for palabra in ['mis carreras', 'activas', 'viajes']):
            return 'listar_carreras'
        
        if any(palabra in mensaje_lower for palabra in ['ayuda', 'help', 'qué puedes hacer']):
            return 'mostrar_ayuda'
        
        return 'conversacion_general'
    
    def generar_respuesta_contextual(self, mensaje_usuario, estado_conversacion, datos_usuario=None):
        """
        Genera una respuesta contextual basada en el estado de la conversación
        
        Args:
            mensaje_usuario: Mensaje del usuario
            estado_conversacion: Estado actual ('inicio', 'esperando_origen', etc.)
            datos_usuario: Datos del usuario (nombre, carreras previas, etc.)
        """
        contexto = {
            'estado': estado_conversacion,
            'datos_usuario': datos_usuario or {}
        }
        
        return self.generar_respuesta(mensaje_usuario, contexto=contexto)


# Instancia global del asistente
claude_assistant = ClaudeAssistant()
