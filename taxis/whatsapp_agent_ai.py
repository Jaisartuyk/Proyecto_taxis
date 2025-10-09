"""
Agente de IA Mejorado con Claude para WhatsApp
Incluye conversaciones naturales y soporte para ubicaciones GPS
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import Ride, AppUser, Taxi, RideDestination
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging
from .ai_assistant_simple import simple_ai_assistant

logger = logging.getLogger(__name__)

# Configuración de WASender
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"
WASENDER_TOKEN = "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6"

# Almacenamiento temporal de conversaciones (en producción usar Redis o DB)
conversaciones = {}


class WhatsAppAgentAI:
    """Agente de IA mejorado con Claude para conversaciones naturales"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="taxi_app_whatsapp")
    
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
        
        # Obtener o crear conversación
        if numero_telefono not in conversaciones:
            conversaciones[numero_telefono] = {
                'estado': 'inicio',
                'datos': {},
                'nombre': nombre_usuario or 'Usuario',
                'historial': []
            }
        
        conversacion = conversaciones[numero_telefono]
        estado_actual = conversacion['estado']
        
        # Si es una ubicación GPS
        if ubicacion:
            return self._manejar_ubicacion_gps(numero_telefono, ubicacion, conversacion)
        
        # Si es un mensaje de texto
        if mensaje:
            return self._manejar_mensaje_texto(numero_telefono, mensaje, conversacion)
    
    def _manejar_mensaje_texto(self, numero_telefono, mensaje, conversacion):
        """Maneja mensajes de texto usando Claude AI"""
        try:
            # Agregar mensaje al historial
            conversacion['historial'].append({
                "role": "user",
                "content": mensaje
            })
            
            # Generar respuesta con el asistente de IA
            resultado = simple_ai_assistant.generar_respuesta_contextual(
                mensaje_usuario=mensaje,
                estado_conversacion=conversacion['estado'],
                datos_usuario={
                    'nombre': conversacion['nombre'],
                    'datos': conversacion['datos']
                }
            )
            
            respuesta_texto = resultado['respuesta']
            accion = resultado['accion']
            datos_extraidos = resultado['datos_extraidos']
            
            # Agregar respuesta al historial
            conversacion['historial'].append({
                "role": "assistant",
                "content": respuesta_texto
            })
            
            # Limitar historial a últimos 10 mensajes
            if len(conversacion['historial']) > 10:
                conversacion['historial'] = conversacion['historial'][-10:]
            
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
            conversacion['estado'] = 'esperando_origen'
        
        elif accion == 'procesar_origen':
            # Intentar geocodificar la dirección
            try:
                location = self.geolocator.geocode(mensaje, timeout=10)
                if location:
                    conversacion['datos']['origen'] = mensaje
                    conversacion['datos']['origen_lat'] = location.latitude
                    conversacion['datos']['origen_lng'] = location.longitude
                    conversacion['estado'] = 'esperando_destino'
                else:
                    # Claude ya respondió, solo actualizamos estado
                    pass
            except:
                pass
        
        elif accion == 'procesar_destino':
            # Intentar geocodificar el destino
            try:
                location = self.geolocator.geocode(mensaje, timeout=10)
                if location:
                    conversacion['datos']['destino'] = mensaje
                    conversacion['datos']['destino_lat'] = location.latitude
                    conversacion['datos']['destino_lng'] = location.longitude
                    # Mostrar resumen
                    self._mostrar_resumen_carrera(numero_telefono, conversacion)
            except:
                pass
        
        elif accion == 'crear_carrera':
            self._crear_carrera_confirmada(numero_telefono, conversacion)
        
        elif accion == 'cancelar_solicitud':
            conversacion['estado'] = 'inicio'
            conversacion['datos'] = {}
        
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
        """Crea la carrera en la base de datos"""
        try:
            # Buscar o crear usuario
            usuario = self._obtener_o_crear_usuario(numero_telefono, conversacion['nombre'])
            
            # Crear la carrera
            ride = Ride.objects.create(
                customer=usuario,
                driver_id=conversacion['datos']['taxista_sugerido'],
                origin=conversacion['datos']['origen'],
                origin_latitude=conversacion['datos']['origen_lat'],
                origin_longitude=conversacion['datos']['origen_lng'],
                status='accepted',
                requested_at=timezone.now()
            )
            
            # Crear destino
            RideDestination.objects.create(
                ride=ride,
                destination=conversacion['datos']['destino'],
                destination_latitude=conversacion['datos']['destino_lat'],
                destination_longitude=conversacion['datos']['destino_lng'],
                order=1
            )
            
            conversacion['datos']['ride_id'] = ride.id
            conversacion['estado'] = 'carrera_activa'
            
            # Notificar al conductor
            taxista = Taxi.objects.get(id=conversacion['datos']['taxista_sugerido'])
            if taxista.user.phone_number:
                self._notificar_conductor(taxista.user.phone_number, ride)
            
            respuesta = f"""✅ *¡Carrera confirmada!* 🎉

Tu carrera ha sido asignada exitosamente.

📱 *Número de carrera:* #{ride.id}
🚕 *Conductor:* {taxista.user.get_full_name()}
📞 *Teléfono:* {taxista.user.phone_number or 'No disponible'}
🚗 *Vehículo:* {taxista.vehicle_description}
🔢 *Placa:* {taxista.plate_number}

⏱️ El conductor llegará en aproximadamente 5-10 minutos.

Puedes seguir el estado escribiendo *ESTADO*

¡Buen viaje! 🚗💨"""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
            
        except Exception as e:
            logger.error(f"Error al crear carrera: {str(e)}", exc_info=True)
            conversacion['estado'] = 'inicio'
            self.enviar_mensaje(
                numero_telefono,
                "❌ Hubo un error al crear la carrera. Por favor, intenta nuevamente escribiendo *MENU*"
            )
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
                ).order_by('-requested_at')
                
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
        if not numero.startswith('+'):
            numero = '+' + numero
        return numero


# Instancia global del agente mejorado
whatsapp_agent_ai = WhatsAppAgentAI()
