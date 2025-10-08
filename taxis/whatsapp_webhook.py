"""
Webhook handler para recibir mensajes de WhatsApp desde WASender
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .whatsapp_agent import whatsapp_agent

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST", "GET"])
def whatsapp_webhook(request):
    """
    Endpoint para recibir webhooks de WASender
    
    Formato esperado:
    {
        "event": "message.received",
        "timestamp": "1757318059855",
        "session_id": 8359,
        "data": {
            "from": "+1234567890",
            "text": "Hola",
            "name": "Juan Pérez",
            "message_id": "ABC123"
        }
    }
    """
    
    # Verificación GET para configuración del webhook
    if request.method == 'GET':
        return JsonResponse({
            'status': 'ok',
            'message': 'WhatsApp Webhook is active',
            'service': 'De Aquí Pa\'llá - Taxi Service'
        })
    
    try:
        # Parsear el cuerpo de la solicitud
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
        
        logger.info(f"Webhook recibido: {payload}")
        
        # Extraer información del webhook
        event_type = payload.get('event', '')
        data = payload.get('data', {})
        
        # Procesar solo mensajes recibidos
        if event_type == 'message.received':
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
