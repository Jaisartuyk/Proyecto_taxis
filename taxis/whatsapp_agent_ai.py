"""
Agente de IA Mejorado con Claude para WhatsApp
Incluye conversaciones naturales y soporte para ubicaciones GPS
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import (
    Ride, AppUser, Taxi, RideDestination,
    WhatsAppConversation, WhatsAppMessage, WhatsAppStats
)
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
from datetime import date
# Importar asistente de IA (Claude si está disponible, sino simple)
from .ai_assistant_claude import claude_ai_assistant
from .ai_assistant_simple import simple_ai_assistant

# Usar Claude si está disponible, sino fallback a simple
ai_assistant = claude_ai_assistant if claude_ai_assistant.client else simple_ai_assistant

logger = logging.getLogger(__name__)

# Configuración de WASender
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"
WASENDER_TOKEN = "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6"


class WhatsAppAgentAI:
    """Agente de IA mejorado con Claude para conversaciones naturales"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="taxi_app_whatsapp")
    
    def _guardar_mensaje(self, conversation, direction, content, message_type='text', metadata=None):
        """Guarda un mensaje en la base de datos"""
        try:
            WhatsAppMessage.objects.create(
                conversation=conversation,
                direction=direction,
                message_type=message_type,
                content=content,
                metadata=metadata or {},
                delivered=True if direction == 'outgoing' else False
            )
            logger.info(f"💾 Mensaje guardado en BD: {direction} - {content[:30]}...")
        except Exception as e:
            logger.error(f"❌ Error al guardar mensaje: {str(e)}")
    
    def _actualizar_stats(self, conversation=None, ride_requested=False, ride_completed=False):
        """Actualiza las estadísticas diarias"""
        try:
            today = date.today()
            stats, created = WhatsAppStats.objects.get_or_create(date=today)
            
            if conversation:
                stats.total_messages += 1
                if conversation.messages.filter(direction='incoming').exists():
                    stats.incoming_messages += 1
                if conversation.messages.filter(direction='outgoing').exists():
                    stats.outgoing_messages += 1
            
            if ride_requested:
                stats.rides_requested += 1
            
            if ride_completed:
                stats.rides_completed += 1
            
            stats.save()
            logger.info(f"📊 Stats actualizadas: {stats.total_messages} mensajes hoy")
        except Exception as e:
            logger.error(f"❌ Error al actualizar stats: {str(e)}")
    
    def enviar_mensaje(self, numero_telefono, mensaje, botones=None):
        """Envía un mensaje de WhatsApp usando WASender API"""
        try:
            # Limpiar el número de teléfono
            numero_limpio = numero_telefono.split('@')[0] if '@' in numero_telefono else numero_telefono
            if not numero_limpio.startswith('+'):
                numero_limpio = '+' + numero_limpio
            
            headers = {
                "Authorization": f"Bearer {WASENDER_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": numero_limpio,
                "text": mensaje
            }
            
            if botones:
                payload["buttons"] = botones
            
            logger.info(f"📤 Enviando mensaje a {numero_limpio}: {mensaje[:50]}...")
            
            response = requests.post(
                WASENDER_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Mensaje enviado exitosamente")
                
                # Guardar mensaje en BD
                try:
                    conversation = WhatsAppConversation.objects.filter(
                        phone_number=numero_limpio
                    ).first()
                    if conversation:
                        self._guardar_mensaje(conversation, 'outgoing', mensaje)
                        self._actualizar_stats(conversation)
                except Exception as e:
                    logger.error(f"Error al guardar mensaje saliente: {str(e)}")
                
                return True
            else:
                logger.error(f"❌ Error al enviar: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción al enviar: {str(e)}")
            return False
    
    def procesar_mensaje_entrante(self, numero_telefono, mensaje=None, nombre_usuario=None, ubicacion=None):
        """
        Procesa un mensaje entrante de WhatsApp (texto o ubicación)
        
        Args:
            numero_telefono: Número del usuario
            mensaje: Texto del mensaje (opcional si es ubicación)
            nombre_usuario: Nombre del usuario
            ubicacion: Dict con {latitude, longitude} si es ubicación GPS
        """
        # Normalizar número de teléfono
        numero_telefono = self._normalizar_telefono(numero_telefono)
        
        # VALIDAR QUE EL USUARIO ESTÉ REGISTRADO
        # Convertir +593968192046 a 0968192046
        numero_local = numero_telefono.replace('+593', '0') if numero_telefono.startswith('+593') else numero_telefono
        
        try:
            usuario = AppUser.objects.filter(
                phone_number__in=[numero_telefono, numero_local]
            ).first()
            
            if not usuario:
                logger.warning(f"⚠️ Usuario no registrado: {numero_telefono}")
                self.enviar_mensaje(
                    numero_telefono,
                    "❌ *Lo sentimos*\n\n"
                    "Tu número no está registrado en nuestro sistema.\n\n"
                    "📱 Para usar nuestro servicio de taxis, debes registrarte primero.\n\n"
                    "👉 Visita nuestra página web o contacta con un administrador para registrarte.\n\n"
                    f"Tu número: {numero_local}"
                )
                return
                
            logger.info(f"✅ Usuario registrado: {usuario.get_full_name()} ({numero_local})")
            
        except Exception as e:
            logger.error(f"❌ Error al validar usuario: {str(e)}")
            self.enviar_mensaje(
                numero_telefono,
                "❌ Hubo un error al validar tu usuario. Por favor, intenta más tarde."
            )
            return
        
        # Obtener o crear conversación en BD
        conversation, created = WhatsAppConversation.objects.get_or_create(
            phone_number=numero_telefono,
            defaults={
                'user': usuario,
                'name': nombre_usuario or usuario.get_full_name(),
                'status': 'active',
                'state': 'inicio'
            }
        )
        
        if created:
            logger.info(f"📝 Nueva conversación creada para {numero_telefono}")
            # Actualizar stats
            today = date.today()
            stats, _ = WhatsAppStats.objects.get_or_create(date=today)
            stats.new_conversations += 1
            stats.active_conversations = WhatsAppConversation.objects.filter(
                status='active'
            ).count()
            stats.save()
        else:
            # Reactivar conversación si estaba abandonada
            if conversation.status in ['completed', 'abandoned']:
                conversation.status = 'active'
                conversation.state = 'inicio'
                conversation.save()
        
        # Guardar mensaje entrante
        if mensaje:
            self._guardar_mensaje(conversation, 'incoming', mensaje)
            self._actualizar_stats(conversation)
        elif ubicacion:
            self._guardar_mensaje(
                conversation,
                'incoming',
                f"Ubicación GPS: {ubicacion['latitude']}, {ubicacion['longitude']}",
                message_type='location',
                metadata=ubicacion
            )
            self._actualizar_stats(conversation)
        
        # Si es una ubicación GPS
        if ubicacion:
            return self._manejar_ubicacion_gps(numero_telefono, ubicacion, conversation)
        
        # Si es un mensaje de texto
        if mensaje:
            return self._manejar_mensaje_texto(numero_telefono, mensaje, conversation)
    
    def _manejar_mensaje_texto(self, numero_telefono, mensaje, conversacion):
        """Maneja mensajes de texto usando Claude AI"""
        try:
            mensaje_upper = mensaje.upper().strip()
            
            # Manejar comandos del conductor: ACEPTAR o RECHAZAR carrera
            if mensaje_upper.startswith('ACEPTAR '):
                try:
                    ride_id = int(mensaje_upper.split()[1])
                    return self._conductor_aceptar_carrera(numero_telefono, ride_id)
                except (IndexError, ValueError):
                    self.enviar_mensaje(numero_telefono, "❌ Formato incorrecto. Usa: *ACEPTAR [número]*")
                    return True
            
            if mensaje_upper.startswith('RECHAZAR '):
                try:
                    ride_id = int(mensaje_upper.split()[1])
                    return self._conductor_rechazar_carrera(numero_telefono, ride_id)
                except (IndexError, ValueError):
                    self.enviar_mensaje(numero_telefono, "❌ Formato incorrecto. Usa: *RECHAZAR [número]*")
                    return True
            
            # Obtener historial de mensajes de la BD
            mensajes_recientes = conversacion.messages.all().order_by('-created_at')[:10]
            historial = []
            for msg in reversed(mensajes_recientes):
                historial.append({
                    "role": "user" if msg.direction == 'incoming' else "assistant",
                    "content": msg.content
                })
            
            # Generar respuesta con el asistente de IA (Claude o Simple)
            resultado = ai_assistant.generar_respuesta_contextual(
                mensaje_usuario=mensaje,
                estado_conversacion=conversacion.state,
                datos_usuario={
                    'nombre': conversacion.name,
                    'datos': conversacion.data
                }
            )
            
            respuesta_texto = resultado['respuesta']
            accion = resultado['accion']
            datos_extraidos = resultado['datos_extraidos']
            
            # Ejecutar acción según lo que Claude determine
            self._ejecutar_accion(numero_telefono, accion, mensaje, conversacion, datos_extraidos)
            
            # Enviar respuesta
            self.enviar_mensaje(numero_telefono, respuesta_texto)
            
            logger.info(f"✅ Mensaje procesado. Acción: {accion}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al procesar mensaje: {str(e)}", exc_info=True)
            self.enviar_mensaje(
                numero_telefono,
                "Disculpa, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo? 😊"
            )
            return False
    
    def _manejar_ubicacion_gps(self, numero_telefono, ubicacion, conversacion):
        """Maneja ubicaciones GPS enviadas desde WhatsApp"""
        try:
            lat = ubicacion.get('latitude')
            lng = ubicacion.get('longitude')
            
            logger.info(f"📍 Ubicación recibida: {lat}, {lng}")
            
            # Geocodificación inversa para obtener dirección
            try:
                location = self.geolocator.reverse(f"{lat}, {lng}", timeout=10)
                direccion = location.address if location else f"Ubicación: {lat}, {lng}"
            except:
                direccion = f"Ubicación GPS: {lat}, {lng}"
            
            estado_actual = conversacion['estado']
            
            # Si estamos esperando origen
            if estado_actual == 'esperando_origen' or estado_actual == 'inicio':
                conversacion['datos']['origen'] = direccion
                conversacion['datos']['origen_lat'] = lat
                conversacion['datos']['origen_lng'] = lng
                conversacion['estado'] = 'esperando_destino'
                
                # Guardar ubicación en tiempo real
                self._guardar_ubicacion_tiempo_real(numero_telefono, lat, lng, 'origen')
                
                respuesta = f"""✅ Perfecto, te vamos a recoger en:
📍 {direccion}

Ahora, ¿a dónde te llevamos? Puedes escribir la dirección o enviar otra ubicación 🗺️"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            
            # Si estamos esperando destino
            elif estado_actual == 'esperando_destino':
                conversacion['datos']['destino'] = direccion
                conversacion['datos']['destino_lat'] = lat
                conversacion['datos']['destino_lng'] = lng
                
                # Guardar ubicación de destino
                self._guardar_ubicacion_tiempo_real(numero_telefono, lat, lng, 'destino')
                
                # Calcular distancia y tarifa
                return self._mostrar_resumen_carrera(numero_telefono, conversacion)
            
            else:
                # Ubicación enviada fuera de contexto
                respuesta = "Recibí tu ubicación 📍. ¿Quieres solicitar una carrera desde ahí? Responde SÍ para continuar."
                conversacion['datos']['ubicacion_temporal'] = {'lat': lat, 'lng': lng, 'direccion': direccion}
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
                
        except Exception as e:
            logger.error(f"❌ Error al procesar ubicación: {str(e)}", exc_info=True)
            self.enviar_mensaje(
                numero_telefono,
                "Hubo un problema al procesar tu ubicación. ¿Podrías enviarla de nuevo o escribir la dirección? 📍"
            )
            return False
    
    def _ejecutar_accion(self, numero_telefono, accion, mensaje, conversacion, datos_extraidos):
        """Ejecuta la acción determinada por Claude"""
        
        if accion == 'solicitar_origen':
            conversacion.state = 'esperando_origen'
            conversacion.save()
        
        elif accion == 'solicitar_destino':
            # Claude indica que debe pedir destino
            conversacion.state = 'esperando_destino'
            conversacion.save()
        
        elif accion == 'procesar_origen':
            # Intentar geocodificar la dirección
            try:
                logger.info(f"🗺️ Geocodificando origen: {mensaje}")
                # Agregar Guayaquil, Ecuador si no está en el mensaje
                direccion_completa = mensaje
                if 'guayaquil' not in mensaje.lower() and 'ecuador' not in mensaje.lower():
                    direccion_completa = f"{mensaje}, Guayaquil, Ecuador"
                    logger.info(f"📍 Dirección completa: {direccion_completa}")
                
                location = self.geolocator.geocode(direccion_completa, timeout=10)
                
                if location:
                    conversacion.data['origen'] = mensaje
                    conversacion.data['origen_lat'] = location.latitude
                    conversacion.data['origen_lng'] = location.longitude
                    conversacion.state = 'esperando_destino'
                    conversacion.save()
                    logger.info(f"✅ Origen geocodificado: {location.latitude}, {location.longitude}")
                    
                    # Confirmar y pedir destino
                    respuesta = f"✅ Perfecto, te vamos a recoger en:\n📍 {location.address}\n\n¿Y a dónde te llevamos? Escribe el destino o envía la ubicación 🗺️"
                    self.enviar_mensaje(numero_telefono, respuesta)
                else:
                    logger.warning(f"⚠️ No se pudo geocodificar el origen: {mensaje}")
                    self.enviar_mensaje(
                        numero_telefono,
                        f"🤔 No pude encontrar la dirección '{mensaje}'.\n\n¿Podrías ser más específico? Por ejemplo: 'Av. 9 de Octubre, Guayaquil' o envía tu ubicación GPS 📍"
                    )
            except Exception as e:
                logger.error(f"❌ Error al geocodificar origen: {str(e)}", exc_info=True)
                self.enviar_mensaje(
                    numero_telefono,
                    "❌ Hubo un problema al buscar la dirección. ¿Podrías intentar de nuevo o enviar tu ubicación GPS? 📍"
                )
        
        elif accion == 'procesar_destino':
            # Intentar geocodificar el destino
            try:
                logger.info(f"🗺️ Geocodificando destino: {mensaje}")
                # Agregar Guayaquil, Ecuador si no está en el mensaje
                direccion_completa = mensaje
                if 'guayaquil' not in mensaje.lower() and 'ecuador' not in mensaje.lower():
                    direccion_completa = f"{mensaje}, Guayaquil, Ecuador"
                    logger.info(f"📍 Dirección completa: {direccion_completa}")
                
                location = self.geolocator.geocode(direccion_completa, timeout=10)
                
                if location:
                    conversacion.data['destino'] = mensaje
                    conversacion.data['destino_lat'] = location.latitude
                    conversacion.data['destino_lng'] = location.longitude
                    conversacion.save()
                    logger.info(f"✅ Destino geocodificado: {location.latitude}, {location.longitude}")
                    
                    # Mostrar resumen
                    self._mostrar_resumen_carrera(numero_telefono, conversacion)
                else:
                    logger.warning(f"⚠️ No se pudo geocodificar el destino: {mensaje}")
                    self.enviar_mensaje(
                        numero_telefono,
                        f"🤔 No pude encontrar la dirección '{mensaje}'.\n\n¿Podrías ser más específico? Por ejemplo: 'Malecón 2000, Guayaquil' o envía tu ubicación GPS 📍"
                    )
            except Exception as e:
                logger.error(f"❌ Error al geocodificar destino: {str(e)}", exc_info=True)
                self.enviar_mensaje(
                    numero_telefono,
                    "❌ Hubo un problema al buscar la dirección. ¿Podrías intentar de nuevo o enviar tu ubicación GPS? 📍"
                )
        
        elif accion == 'crear_carrera':
            self._crear_carrera_confirmada(numero_telefono, conversacion)
        
        elif accion == 'cancelar_solicitud':
            conversacion.state = 'inicio'
            conversacion.data = {}
            conversacion.save()
        
        elif accion == 'consultar_estado':
            self._mostrar_estado_carrera(numero_telefono, conversacion)
        
        elif accion == 'listar_carreras':
            self._mostrar_carreras_activas(numero_telefono, conversacion)
    
    def _mostrar_resumen_carrera(self, numero_telefono, conversacion):
        """Muestra el resumen de la carrera con tarifa estimada"""
        try:
            origen = (conversacion['datos']['origen_lat'], conversacion['datos']['origen_lng'])
            destino = (conversacion['datos']['destino_lat'], conversacion['datos']['destino_lng'])
            distancia = geodesic(origen, destino).kilometers
            
            conversacion['datos']['distancia'] = distancia
            
            # Buscar taxista más cercano
            taxista = self._buscar_taxista_cercano(
                conversacion['datos']['origen_lat'],
                conversacion['datos']['origen_lng']
            )
            
            if taxista:
                conversacion['datos']['taxista_sugerido'] = taxista.id
                tarifa_estimada = self._calcular_tarifa(distancia)
                
                conversacion['estado'] = 'confirmando_carrera'
                
                respuesta = f"""✅ *Resumen de tu carrera*

📍 *Origen:* {conversacion['datos']['origen']}
🎯 *Destino:* {conversacion['datos']['destino']}
📏 *Distancia:* {distancia:.2f} km
💰 *Tarifa estimada:* ${tarifa_estimada:,.0f} COP
⏱️ *Tiempo de llegada:* 5-10 minutos
🚕 *Conductor:* {taxista.user.get_full_name()}
🚗 *Vehículo:* {taxista.vehicle_description}

¿Confirmas esta carrera? 
Responde *SÍ* para confirmar o *NO* para cancelar 😊"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            else:
                conversacion['estado'] = 'inicio'
                respuesta = """😔 Lo sentimos, no hay conductores disponibles en este momento.

Por favor, intenta más tarde o escribe *MENU* para volver al inicio."""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
                
        except Exception as e:
            logger.error(f"Error al mostrar resumen: {str(e)}")
            return False
    
    def _crear_carrera_confirmada(self, numero_telefono, conversacion):
        """Crea la carrera en la base de datos usando la función del sistema"""
        try:
            # Buscar o crear usuario
            usuario = self._obtener_o_crear_usuario(numero_telefono, conversacion.name)
            
            # Calcular precio basado en distancia
            precio_estimado = self._calcular_precio(
                conversacion.data['origen_lat'],
                conversacion.data['origen_lng'],
                conversacion.data['destino_lat'],
                conversacion.data['destino_lng']
            )
            
            # Usar la función del sistema para crear la carrera
            # Esto garantiza que se use la misma lógica que el resto del sistema
            from .views import crear_carrera_desde_whatsapp
            
            ride = crear_carrera_desde_whatsapp(
                user=usuario,
                origin=conversacion.data['origen'],
                origin_lat=conversacion.data['origen_lat'],
                origin_lng=conversacion.data['origen_lng'],
                destination=conversacion.data['destino'],
                dest_lat=conversacion.data['destino_lat'],
                dest_lng=conversacion.data['destino_lng'],
                price=precio_estimado
            )
            
            # Actualizar conversación
            conversacion.ride = ride
            conversacion.state = 'carrera_activa'
            conversacion.data['ride_id'] = ride.id
            conversacion.save()
            
            # Actualizar estadísticas
            self._actualizar_stats(conversacion, ride_requested=True)
            
            # Notificar al cliente
            respuesta = f"""✅ *¡Carrera creada!* 🎉

📱 *Número de carrera:* #{ride.id}
📍 *Origen:* {ride.origin}
🎯 *Destino:* {conversacion.data['destino']}
💰 *Precio estimado:* ${precio_estimado:.2f}

🔍 Estamos notificando a los conductores disponibles...

Te avisaremos cuando un conductor acepte tu carrera. ⏱️

Puedes seguir el estado escribiendo *ESTADO*"""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
            
        except KeyError as e:
            logger.error(f"Error: Falta información en la conversación: {str(e)}", exc_info=True)
            conversacion['estado'] = 'inicio'
            self.enviar_mensaje(
                numero_telefono,
                "❌ Falta información para crear la carrera. Por favor, intenta nuevamente escribiendo *SOLICITAR* 🚕"
            )
            return False
        except Taxi.DoesNotExist:
            logger.error(f"Error: No se encontró el taxista sugerido")
            conversacion['estado'] = 'inicio'
            self.enviar_mensaje(
                numero_telefono,
                "❌ No hay conductores disponibles en este momento. Por favor, intenta más tarde 😔"
            )
            return False
        except Exception as e:
            logger.error(f"❌ Error al crear carrera: {str(e)}", exc_info=True)
            conversacion['estado'] = 'inicio'
            
            # Mensaje de error más específico
            error_msg = str(e)
            if "taxista_sugerido" in error_msg or "driver" in error_msg:
                mensaje = "❌ No hay conductores disponibles. Intenta más tarde 😔"
            elif "origen" in error_msg or "destino" in error_msg:
                mensaje = "❌ Hubo un problema con las direcciones. Intenta nuevamente escribiendo *SOLICITAR* 📍"
            else:
                mensaje = f"❌ Hubo un error al crear la carrera: {error_msg}\n\nPor favor, intenta nuevamente escribiendo *MENU*"
            
            self.enviar_mensaje(numero_telefono, mensaje)
            return False
    
    def _guardar_ubicacion_tiempo_real(self, numero_telefono, lat, lng, tipo='tracking'):
        """
        Guarda la ubicación en tiempo real para visualización en la central
        
        Args:
            numero_telefono: Número del usuario
            lat: Latitud
            lng: Longitud
            tipo: 'origen', 'destino', 'tracking'
        """
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            # Enviar ubicación a la sala de la central
            async_to_sync(channel_layer.group_send)(
                'central_tracking',
                {
                    'type': 'location_update',
                    'data': {
                        'numero_telefono': numero_telefono,
                        'latitude': lat,
                        'longitude': lng,
                        'tipo': tipo,
                        'timestamp': timezone.now().isoformat()
                    }
                }
            )
            
            logger.info(f"📍 Ubicación enviada a central: {numero_telefono} - {tipo}")
            
        except Exception as e:
            logger.error(f"Error al enviar ubicación a central: {str(e)}")
    
    def _buscar_taxista_cercano(self, lat, lng):
        """Busca el taxista más cercano disponible"""
        try:
            taxis_disponibles = Taxi.objects.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                user__role='driver'
            )
            
            origen = (lat, lng)
            taxista_cercano = None
            distancia_minima = float('inf')
            
            for taxi in taxis_disponibles:
                taxi_pos = (taxi.latitude, taxi.longitude)
                distancia = geodesic(origen, taxi_pos).kilometers
                
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    taxista_cercano = taxi
            
            return taxista_cercano
            
        except Exception as e:
            logger.error(f"Error al buscar taxista: {str(e)}")
            return None
    
    def _calcular_tarifa(self, distancia_km):
        """Calcula la tarifa estimada"""
        tarifa_base = 5000  # COP
        tarifa_por_km = 2500  # COP
        return tarifa_base + (distancia_km * tarifa_por_km)
    
    def _obtener_o_crear_usuario(self, numero_telefono, nombre):
        """Obtiene o crea un usuario"""
        try:
            usuario = AppUser.objects.filter(phone_number=numero_telefono).first()
            
            if not usuario:
                username = f"whatsapp_{numero_telefono.replace('+', '').replace('@', '_')}"
                usuario = AppUser.objects.create(
                    username=username,
                    first_name=nombre,
                    phone_number=numero_telefono,
                    role='customer'
                )
                usuario.set_unusable_password()
                usuario.save()
            
            return usuario
            
        except Exception as e:
            logger.error(f"Error al obtener/crear usuario: {str(e)}")
            raise
    
    def _notificar_conductor(self, numero_conductor, ride):
        """Notifica al conductor sobre una nueva carrera"""
        mensaje = f"""🚕 *¡Nueva carrera asignada!*

📱 Carrera #{ride.id}
👤 Cliente: {ride.customer.get_full_name()}
📞 Teléfono: {ride.customer.phone_number or 'No disponible'}
📍 Origen: {ride.origin}
🎯 Destino: {ride.destinations.first().destination if ride.destinations.exists() else 'N/A'}

¡Dirígete al punto de recogida! 🚗💨"""
        
        self.enviar_mensaje(numero_conductor, mensaje)
    
    def _calcular_precio(self, lat1, lng1, lat2, lng2):
        """Calcula el precio estimado basado en la distancia"""
        from math import radians, sin, cos, sqrt, atan2
        
        # Calcular distancia usando fórmula de Haversine
        R = 6371  # Radio de la Tierra en km
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlon = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distancia_km = R * c
        
        # Lógica de precio igual a request_ride.html:
        # - Si distancia <= 4.44 km: $2.00 (tarifa base)
        # - Si distancia > 4.44 km: distancia * $0.45 por km
        threshold = 4.44  # Límite para tarifa base
        price_per_km = 0.45  # Precio por kilómetro
        
        if distancia_km <= threshold:
            precio = 2.00  # Tarifa base
        else:
            precio = distancia_km * price_per_km
        
        # Redondear a 2 decimales
        return round(precio, 2)
    
    def _buscar_taxista_cercano(self, lat, lng):
        """Busca el taxista disponible más cercano a las coordenadas dadas"""
        from math import radians, sin, cos, sqrt, atan2
        
        # Obtener todos los taxis que no tienen carreras activas
        taxis_con_carreras = Ride.objects.filter(
            status__in=['requested', 'accepted', 'in_progress']
        ).values_list('driver_id', flat=True)
        
        taxis_disponibles = Taxi.objects.filter(
            user__role='driver'
        ).exclude(
            user_id__in=taxis_con_carreras
        ).select_related('user')
        
        if not taxis_disponibles.exists():
            return None
        
        # Función para calcular distancia usando fórmula de Haversine
        def calcular_distancia(lat1, lon1, lat2, lon2):
            R = 6371  # Radio de la Tierra en km
            
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            return R * c
        
        # Buscar el taxi más cercano
        taxista_cercano = None
        distancia_minima = float('inf')
        
        for taxi in taxis_disponibles:
            # Por ahora usamos coordenadas fijas o las últimas conocidas
            # En producción, esto vendría de un sistema de tracking en tiempo real
            taxi_lat = -2.1709  # Coordenadas de ejemplo (Guayaquil)
            taxi_lng = -79.9224
            
            distancia = calcular_distancia(lat, lng, taxi_lat, taxi_lng)
            
            if distancia < distancia_minima:
                distancia_minima = distancia
                taxista_cercano = taxi
        
        return taxista_cercano
    
    def _notificar_conductor_nueva_carrera(self, numero_conductor, ride):
        """Notifica al conductor sobre una nueva carrera disponible para aceptar"""
        destino = ride.destinations.first().destination if ride.destinations.exists() else 'No especificado'
        
        mensaje = f"""🚕 *¡Nueva carrera disponible!*

📱 Carrera #{ride.id}
👤 Cliente: {ride.customer.get_full_name()}
📞 Teléfono: {ride.customer.phone_number or 'No disponible'}
📍 Origen: {ride.origin}
🎯 Destino: {destino}

Para ACEPTAR esta carrera, responde:
*ACEPTAR {ride.id}*

Para RECHAZAR, responde:
*RECHAZAR {ride.id}*

⏱️ Tienes 2 minutos para responder."""
        
        self.enviar_mensaje(numero_conductor, mensaje)
    
    def _conductor_aceptar_carrera(self, numero_telefono, ride_id):
        """Maneja cuando un conductor acepta una carrera"""
        try:
            # Buscar la carrera
            ride = Ride.objects.get(id=ride_id, status='requested')
            
            # Buscar el conductor
            numero_normalizado = self._normalizar_telefono(numero_telefono)
            conductor = AppUser.objects.filter(
                phone_number__in=[numero_telefono, numero_normalizado],
                role='driver'
            ).first()
            
            if not conductor:
                self.enviar_mensaje(numero_telefono, "❌ No estás registrado como conductor.")
                return True
            
            # Asignar conductor y cambiar estado
            ride.driver = conductor
            ride.status = 'accepted'
            ride.save()
            
            # Notificar al conductor
            taxi = Taxi.objects.filter(user=conductor).first()
            mensaje_conductor = f"""✅ *¡Carrera aceptada!*

📱 Carrera #{ride.id}
👤 Cliente: {ride.customer.get_full_name()}
📞 Teléfono: {ride.customer.phone_number or 'No disponible'}
📍 Origen: {ride.origin}
🎯 Destino: {ride.destinations.first().destination if ride.destinations.exists() else 'No especificado'}

Dirígete al punto de recogida. ¡Buen viaje! 🚗💨"""
            
            self.enviar_mensaje(numero_telefono, mensaje_conductor)
            
            # Notificar al cliente
            mensaje_cliente = f"""✅ *¡Conductor asignado!* 🎉

📱 Carrera #{ride.id}
🚕 Conductor: {conductor.get_full_name()}
📞 Teléfono: {conductor.phone_number or 'No disponible'}"""
            
            if taxi:
                mensaje_cliente += f"""
🚗 Vehículo: {taxi.vehicle_description}
🔢 Placa: {taxi.plate_number}"""
            
            mensaje_cliente += """

⏱️ El conductor llegará en aproximadamente 5-10 minutos.

Puedes seguir el estado escribiendo *ESTADO*

¡Buen viaje! 🚗💨"""
            
            self.enviar_mensaje(ride.customer.phone_number, mensaje_cliente)
            
            return True
            
        except Ride.DoesNotExist:
            self.enviar_mensaje(numero_telefono, f"❌ La carrera #{ride_id} no existe o ya fue asignada.")
            return True
        except Exception as e:
            logger.error(f"Error al aceptar carrera: {str(e)}", exc_info=True)
            self.enviar_mensaje(numero_telefono, "❌ Hubo un error al aceptar la carrera.")
            return True
    
    def _conductor_rechazar_carrera(self, numero_telefono, ride_id):
        """Maneja cuando un conductor rechaza una carrera"""
        try:
            # Buscar la carrera
            ride = Ride.objects.get(id=ride_id, status='requested')
            
            # Confirmar rechazo
            self.enviar_mensaje(numero_telefono, f"✅ Has rechazado la carrera #{ride_id}.")
            
            # Buscar otro conductor cercano
            taxista_alternativo = self._buscar_taxista_cercano(
                ride.origin_latitude,
                ride.origin_longitude
            )
            
            if taxista_alternativo and taxista_alternativo.user.phone_number:
                # Notificar al siguiente conductor
                self._notificar_conductor_nueva_carrera(taxista_alternativo.user.phone_number, ride)
            else:
                # No hay más conductores, cancelar carrera
                ride.status = 'canceled'
                ride.save()
                
                mensaje_cliente = f"""❌ Lo sentimos, no hay conductores disponibles en este momento.

Tu carrera #{ride.id} ha sido cancelada.

Por favor, intenta más tarde. 😔"""
                
                self.enviar_mensaje(ride.customer.phone_number, mensaje_cliente)
            
            return True
            
        except Ride.DoesNotExist:
            self.enviar_mensaje(numero_telefono, f"❌ La carrera #{ride_id} no existe o ya fue asignada.")
            return True
        except Exception as e:
            logger.error(f"Error al rechazar carrera: {str(e)}", exc_info=True)
            self.enviar_mensaje(numero_telefono, "❌ Hubo un error al procesar tu respuesta.")
            return True
    
    def _mostrar_estado_carrera(self, numero_telefono, conversacion):
        """Muestra el estado de la carrera activa"""
        try:
            ride_id = conversacion['datos'].get('ride_id')
            
            if ride_id:
                ride = Ride.objects.get(id=ride_id)
                
                estado_emoji = {
                    'requested': '⏳ Solicitada',
                    'accepted': '✅ Aceptada',
                    'in_progress': '🚗 En progreso',
                    'completed': '✅ Completada',
                    'canceled': '❌ Cancelada'
                }.get(ride.status, '❓ Desconocido')
                
                respuesta = f"""📊 *Estado de tu carrera*

🚕 Carrera #{ride.id}
📍 Estado: {estado_emoji}
🚗 Conductor: {ride.driver.get_full_name() if ride.driver else 'Sin asignar'}
📞 Teléfono: {ride.driver.phone_number if ride.driver else 'N/A'}
📍 Origen: {ride.origin}
🎯 Destino: {ride.destinations.first().destination if ride.destinations.exists() else 'N/A'}

Escribe *MENU* para más opciones 😊"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            else:
                self.enviar_mensaje(
                    numero_telefono,
                    "No tienes una carrera activa en este momento. Escribe *SOLICITAR* para pedir una 🚕"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error al mostrar estado: {str(e)}")
            return False
    
    def _mostrar_carreras_activas(self, numero_telefono, conversacion):
        """Muestra las carreras activas del usuario"""
        try:
            usuario = AppUser.objects.filter(phone_number=numero_telefono).first()
            
            if usuario:
                carreras_activas = Ride.objects.filter(
                    customer=usuario,
                    status__in=['requested', 'accepted', 'in_progress']
                ).order_by('-created_at')
                
                if carreras_activas.exists():
                    respuesta = "🚕 *Tus carreras activas:*\n\n"
                    
                    for ride in carreras_activas:
                        estado_emoji = {
                            'requested': '⏳',
                            'accepted': '✅',
                            'in_progress': '🚗'
                        }.get(ride.status, '❓')
                        
                        respuesta += f"{estado_emoji} *Carrera #{ride.id}*\n"
                        respuesta += f"Estado: {ride.get_status_display()}\n"
                        respuesta += f"Origen: {ride.origin}\n"
                        if ride.driver:
                            respuesta += f"Conductor: {ride.driver.get_full_name()}\n"
                        respuesta += "\n"
                    
                    respuesta += "Escribe *ESTADO* para ver detalles o *MENU* para más opciones 😊"
                else:
                    respuesta = "No tienes carreras activas. ¿Quieres solicitar una? Escribe *SOLICITAR* 🚕"
            else:
                respuesta = "No encontré tu perfil. Escribe *MENU* para comenzar 😊"
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
            
        except Exception as e:
            logger.error(f"Error al mostrar carreras: {str(e)}")
            return False
    
    def _normalizar_telefono(self, numero):
        """Normaliza el formato del número de teléfono"""
        numero = numero.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if '@' in numero:
            numero = numero.split('@')[0]
        
        # Convertir formato local 0XXX a internacional +593XXX
        if numero.startswith('0') and len(numero) == 10:
            numero = '+593' + numero[1:]  # Reemplazar 0 inicial con +593
        elif not numero.startswith('+'):
            numero = '+' + numero
        
        return numero


# Instancia global del agente mejorado
whatsapp_agent_ai = WhatsAppAgentAI()
