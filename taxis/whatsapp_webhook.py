"""
Webhook handler para recibir mensajes de WhatsApp desde WASender
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .whatsapp_agent_ai import whatsapp_agent_ai

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def whatsapp_webhook(request):
    """
    Endpoint para recibir webhooks de WASender
    
    Formatos soportados:
    1. Test webhook:
    {
        "event": "webhook.test",
        "timestamp": "1757318059855",
        "session_id": 8359,
        "data": {
            "message": "This is a test webhook from WASender",
            "test": true
        }
    }
    
    2. Mensaje recibido:
    {
        "event": "messages.upsert",
        "timestamp": "1757318059855",
        "session_id": 8359,
        "data": {
            "messages": {
                "key": {
                    "remoteJid": "593968192046@s.whatsapp.net",
                    "fromMe": false
                },
                "message": {
                    "conversation": "Hola"
                },
                "pushName": "Juan Pérez"
            }
        }
    }
    """
    
    # Verificación GET para configuración del webhook
    if request.method == 'GET':
        return JsonResponse({
            'status': 'ok',
            'message': 'WhatsApp Webhook is active',
            'service': 'De Aquí Pa\'llá - Taxi Service',
            'endpoint': '/webhook/whatsapp/'
        })
    
    try:
        # Verificar firma del webhook (seguridad)
        webhook_signature = request.headers.get('X-Webhook-Signature', '')
        if webhook_signature:
            logger.info(f"🔐 Webhook signature recibida: {webhook_signature[:20]}...")
        
        # Parsear el cuerpo de la solicitud
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
        
        logger.info(f"📥 Webhook recibido: {json.dumps(payload, indent=2)}")
        
        # Extraer información del webhook
        event_type = payload.get('event', '')
        data = payload.get('data', {})
        
        # Manejar webhook de prueba
        if event_type == 'webhook.test':
            logger.info("✅ Webhook test recibido correctamente")
            return JsonResponse({
                'status': 'success',
                'message': 'Test webhook received successfully',
                'timestamp': payload.get('timestamp'),
                'session_id': payload.get('session_id')
            })
        
        # Procesar mensajes recibidos (formato WASender: messages.upsert)
        if event_type == 'messages.upsert':
            # Extraer datos del formato WASender
            messages_data = data.get('messages', {})
            
            # Obtener el número de teléfono
            key = messages_data.get('key', {})
            remote_jid = key.get('remoteJid', '')
            from_me = key.get('fromMe', False)
            
            # Solo procesar mensajes que NO son enviados por nosotros
            if from_me:
                logger.info("Mensaje enviado por nosotros, ignorando")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message from bot, ignored'
                })
            
            # Extraer número de teléfono (formato: 593968192046@s.whatsapp.net)
            numero_telefono = remote_jid.split('@')[0] if '@' in remote_jid else remote_jid
            # Agregar código de país si no lo tiene
            if not numero_telefono.startswith('+'):
                numero_telefono = '+' + numero_telefono
            
            # Extraer mensaje
            message_content = messages_data.get('message', {})
            mensaje_texto = message_content.get('conversation', '')
            
            # Verificar si es una ubicación GPS
            ubicacion_gps = message_content.get('locationMessage')
            
            # Extraer nombre
            nombre_usuario = messages_data.get('pushName', 'Usuario')
            
            # Si es una ubicación GPS
            if ubicacion_gps:
                lat = ubicacion_gps.get('degreesLatitude')
                lng = ubicacion_gps.get('degreesLongitude')
                
                logger.info(f"📍 Ubicación GPS recibida de {numero_telefono}: {lat}, {lng}")
                
                try:
                    whatsapp_agent_ai.procesar_mensaje_entrante(
                        numero_telefono=numero_telefono,
                        nombre_usuario=nombre_usuario,
                        ubicacion={'latitude': lat, 'longitude': lng}
                    )
                    
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Location processed successfully'
                    })
                    
                except Exception as e:
                    logger.error(f"Error al procesar ubicación: {str(e)}", exc_info=True)
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Error processing location: {str(e)}'
                    }, status=500)
            
            # Si es un mensaje de texto
            if not mensaje_texto:
                logger.warning(f"Webhook sin mensaje de texto ni ubicación: {payload}")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No text or location found'
                }, status=400)
            
            logger.info(f"💬 Procesando mensaje de {numero_telefono}: {mensaje_texto}")
            
            # Procesar el mensaje con el agente de IA mejorado
            try:
                whatsapp_agent_ai.procesar_mensaje_entrante(
                    numero_telefono=numero_telefono,
                    mensaje=mensaje_texto,
                    nombre_usuario=nombre_usuario
                )
                
                logger.info(f"✅ Mensaje procesado exitosamente")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message processed successfully'
                })
                
            except Exception as e:
                logger.error(f"❌ Error al procesar mensaje: {str(e)}", exc_info=True)
                
                # Enviar mensaje de error al usuario
                try:
                    whatsapp_agent_ai.enviar_mensaje(
                        numero_telefono,
                        "Disculpa, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo? 😊"
                    )
                except:
                    pass
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing message: {str(e)}'
                }, status=500)
        
        # Formato antiguo (message.received) - mantener compatibilidad
        elif event_type == 'message.received':
            numero_telefono = data.get('from', '')
            mensaje_texto = data.get('text', '')
            nombre_usuario = data.get('name', 'Usuario')
            
            # Validar datos requeridos
            if not numero_telefono or not mensaje_texto:
                logger.warning("Webhook sin datos completos")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required fields: from or text'
                }, status=400)
            
            # Procesar el mensaje con el agente de IA
            try:
                whatsapp_agent.procesar_mensaje_entrante(
                    numero_telefono=numero_telefono,
                    mensaje=mensaje_texto,
                    nombre_usuario=nombre_usuario
                )
                
                logger.info(f"Mensaje procesado exitosamente de {numero_telefono}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message processed successfully'
                })
                
            except Exception as e:
                logger.error(f"Error al procesar mensaje: {str(e)}", exc_info=True)
                
                # Enviar mensaje de error al usuario
                whatsapp_agent.enviar_mensaje(
                    numero_telefono,
                    "❌ Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta nuevamente."
                )
                
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing message: {str(e)}'
                }, status=500)
        
        # Webhook de prueba
        elif event_type == 'webhook.test':
            logger.info("Webhook de prueba recibido")
            return JsonResponse({
                'status': 'success',
                'message': 'Test webhook received successfully'
            })
        
        # Otros tipos de eventos
        else:
            logger.info(f"Evento no procesado: {event_type}")
            return JsonResponse({
                'status': 'success',
                'message': f'Event {event_type} acknowledged but not processed'
            })
    
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON payload'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Error inesperado en webhook: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_status_webhook(request):
    """
    Endpoint para recibir actualizaciones de estado de mensajes
    
    Formato esperado:
    {
        "event": "message.status",
        "data": {
            "message_id": "ABC123",
            "status": "delivered|read|failed",
            "timestamp": "1757318059855"
        }
    }
    """
    try:
        payload = json.loads(request.body.decode('utf-8'))
        logger.info(f"Estado de mensaje recibido: {payload}")
        
        # Aquí puedes actualizar el estado de los mensajes en tu base de datos
        # Por ahora solo lo registramos
        
        return JsonResponse({
            'status': 'success',
            'message': 'Status update received'
        })
        
    except Exception as e:
        logger.error(f"Error en status webhook: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def whatsapp_send_notification(request):
    """
    Endpoint interno para enviar notificaciones de WhatsApp
    Usado por otros componentes de la aplicación
    
    POST data:
    {
        "phone_number": "+573001234567",
        "message": "Tu carrera ha sido aceptada"
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        phone_number = data.get('phone_number')
        message = data.get('message')
        
        if not phone_number or not message:
            return JsonResponse({
                'status': 'error',
                'message': 'phone_number and message are required'
            }, status=400)
        
        # Enviar mensaje
        success = whatsapp_agent.enviar_mensaje(phone_number, message)
        
        if success:
            return JsonResponse({
                'status': 'success',
                'message': 'Notification sent successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send notification'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error al enviar notificación: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
