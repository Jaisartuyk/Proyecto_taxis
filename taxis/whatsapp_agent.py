"""
Agente de IA para atender carreras por WhatsApp
Integración con WASender API
"""
import requests
import json
from django.conf import settings
from django.utils import timezone
from .models import Ride, AppUser, Taxi, RideDestination
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)

# Configuración de WASender
WASENDER_API_URL = "https://wasenderapi.com/api/send-message"
WASENDER_TOKEN = "e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6"

# Estados de conversación
CONVERSATION_STATES = {
    'INICIO': 'inicio',
    'ESPERANDO_ORIGEN': 'esperando_origen',
    'ESPERANDO_DESTINO': 'esperando_destino',
    'CONFIRMANDO_CARRERA': 'confirmando_carrera',
    'CARRERA_ACTIVA': 'carrera_activa',
}

# Almacenamiento temporal de conversaciones (en producción usar Redis o DB)
conversaciones = {}


class WhatsAppAgent:
    """Agente de IA para gestionar carreras por WhatsApp"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="taxi_app_whatsapp")
    
    def enviar_mensaje(self, numero_telefono, mensaje, botones=None):
        """
        Envía un mensaje de WhatsApp usando WASender API
        
        Args:
            numero_telefono: Número de teléfono con código de país (+57...)
            mensaje: Texto del mensaje
            botones: Lista de botones opcionales
        """
        try:
            # Limpiar el número de teléfono (remover @s.whatsapp.net si existe)
            numero_limpio = numero_telefono.split('@')[0] if '@' in numero_telefono else numero_telefono
            
            # Asegurar que tenga el formato correcto
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
            
            # Si hay botones, agregarlos al payload
            if botones:
                payload["buttons"] = botones
            
            logger.info(f"Enviando mensaje a {numero_limpio}: {mensaje[:50]}...")
            
            response = requests.post(
                WASENDER_API_URL,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Mensaje enviado exitosamente a {numero_limpio}")
                return True
            else:
                logger.error(f"❌ Error al enviar mensaje: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Excepción al enviar mensaje: {str(e)}")
            return False
    
    def procesar_mensaje_entrante(self, numero_telefono, mensaje, nombre_usuario=None):
        """
        Procesa un mensaje entrante de WhatsApp
        
        Args:
            numero_telefono: Número del usuario
            mensaje: Texto del mensaje
            nombre_usuario: Nombre del usuario (opcional)
        """
        # Normalizar número de teléfono
        numero_telefono = self._normalizar_telefono(numero_telefono)
        
        # Obtener o crear conversación
        if numero_telefono not in conversaciones:
            conversaciones[numero_telefono] = {
                'estado': CONVERSATION_STATES['INICIO'],
                'datos': {},
                'nombre': nombre_usuario or 'Usuario'
            }
        
        conversacion = conversaciones[numero_telefono]
        estado_actual = conversacion['estado']
        
        # Procesar según el estado
        if estado_actual == CONVERSATION_STATES['INICIO']:
            return self._manejar_inicio(numero_telefono, mensaje, conversacion)
        
        elif estado_actual == CONVERSATION_STATES['ESPERANDO_ORIGEN']:
            return self._manejar_origen(numero_telefono, mensaje, conversacion)
        
        elif estado_actual == CONVERSATION_STATES['ESPERANDO_DESTINO']:
            return self._manejar_destino(numero_telefono, mensaje, conversacion)
        
        elif estado_actual == CONVERSATION_STATES['CONFIRMANDO_CARRERA']:
            return self._manejar_confirmacion(numero_telefono, mensaje, conversacion)
        
        elif estado_actual == CONVERSATION_STATES['CARRERA_ACTIVA']:
            return self._manejar_carrera_activa(numero_telefono, mensaje, conversacion)
    
    def _manejar_inicio(self, numero_telefono, mensaje, conversacion):
        """Maneja el estado inicial de la conversación"""
        mensaje_lower = mensaje.lower().strip()
        
        # Comandos disponibles
        if mensaje_lower in ['hola', 'inicio', 'empezar', 'menu']:
            respuesta = f"""¡Hola {conversacion['nombre']}! 👋

Bienvenido al servicio de taxis *De Aquí Pa'llá* 🚕

¿Qué deseas hacer?

1️⃣ Solicitar una carrera
2️⃣ Ver mis carreras activas
3️⃣ Cancelar una carrera
4️⃣ Ayuda

Escribe el número de la opción que deseas."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
        
        elif mensaje_lower in ['1', 'solicitar', 'carrera', 'taxi']:
            conversacion['estado'] = CONVERSATION_STATES['ESPERANDO_ORIGEN']
            respuesta = """🚕 *Solicitar una carrera*

Por favor, envíame tu *dirección de origen* o comparte tu ubicación actual.

Ejemplo: "Calle 50 #25-30, Medellín"

También puedes enviar tu ubicación usando el botón de ubicación de WhatsApp 📍"""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
        
        elif mensaje_lower in ['2', 'mis carreras', 'activas']:
            return self._mostrar_carreras_activas(numero_telefono, conversacion)
        
        elif mensaje_lower in ['3', 'cancelar']:
            return self._iniciar_cancelacion(numero_telefono, conversacion)
        
        elif mensaje_lower in ['4', 'ayuda', 'help']:
            return self._mostrar_ayuda(numero_telefono)
        
        else:
            respuesta = """No entendí tu mensaje 🤔

Escribe *MENU* para ver las opciones disponibles."""
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
    
    def _manejar_origen(self, numero_telefono, mensaje, conversacion):
        """Maneja la captura del origen"""
        # Intentar geocodificar la dirección
        try:
            location = self.geolocator.geocode(mensaje, timeout=10)
            
            if location:
                conversacion['datos']['origen'] = mensaje
                conversacion['datos']['origen_lat'] = location.latitude
                conversacion['datos']['origen_lng'] = location.longitude
                conversacion['estado'] = CONVERSATION_STATES['ESPERANDO_DESTINO']
                
                respuesta = f"""✅ Origen confirmado:
📍 {mensaje}

Ahora, por favor envíame tu *dirección de destino*.

Ejemplo: "Aeropuerto José María Córdova"

También puedes compartir la ubicación de destino 📍"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            else:
                respuesta = """❌ No pude encontrar esa dirección.

Por favor, intenta con una dirección más específica o comparte tu ubicación usando el botón de WhatsApp 📍"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
                
        except Exception as e:
            logger.error(f"Error al geocodificar origen: {str(e)}")
            respuesta = """❌ Hubo un error al procesar la dirección.

Por favor, intenta nuevamente o escribe *MENU* para volver al inicio."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return False
    
    def _manejar_destino(self, numero_telefono, mensaje, conversacion):
        """Maneja la captura del destino"""
        try:
            location = self.geolocator.geocode(mensaje, timeout=10)
            
            if location:
                conversacion['datos']['destino'] = mensaje
                conversacion['datos']['destino_lat'] = location.latitude
                conversacion['datos']['destino_lng'] = location.longitude
                
                # Calcular distancia
                origen = (conversacion['datos']['origen_lat'], conversacion['datos']['origen_lng'])
                destino = (location.latitude, location.longitude)
                distancia = geodesic(origen, destino).kilometers
                
                conversacion['datos']['distancia'] = distancia
                
                # Buscar taxista más cercano
                taxista = self._buscar_taxista_cercano(
                    conversacion['datos']['origen_lat'],
                    conversacion['datos']['origen_lng']
                )
                
                if taxista:
                    conversacion['datos']['taxista_sugerido'] = taxista.id
                    tiempo_estimado = "5-10 minutos"
                    tarifa_estimada = self._calcular_tarifa(distancia)
                    
                    conversacion['estado'] = CONVERSATION_STATES['CONFIRMANDO_CARRERA']
                    
                    respuesta = f"""✅ *Resumen de tu carrera*

📍 *Origen:* {conversacion['datos']['origen']}
📍 *Destino:* {conversacion['datos']['destino']}
📏 *Distancia:* {distancia:.2f} km
💰 *Tarifa estimada:* ${tarifa_estimada:,.0f} COP
⏱️ *Tiempo de llegada:* {tiempo_estimado}
🚕 *Conductor:* {taxista.user.get_full_name()}

¿Confirmas esta carrera?

Responde *SÍ* para confirmar o *NO* para cancelar."""
                    
                    self.enviar_mensaje(numero_telefono, respuesta)
                    return True
                else:
                    conversacion['estado'] = CONVERSATION_STATES['INICIO']
                    respuesta = """😔 Lo sentimos, no hay taxistas disponibles en este momento.

Por favor, intenta más tarde o escribe *MENU* para volver al inicio."""
                    
                    self.enviar_mensaje(numero_telefono, respuesta)
                    return False
                    
            else:
                respuesta = """❌ No pude encontrar esa dirección de destino.

Por favor, intenta con una dirección más específica."""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
                
        except Exception as e:
            logger.error(f"Error al geocodificar destino: {str(e)}")
            respuesta = """❌ Hubo un error al procesar el destino.

Por favor, intenta nuevamente."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return False
    
    def _manejar_confirmacion(self, numero_telefono, mensaje, conversacion):
        """Maneja la confirmación de la carrera"""
        mensaje_lower = mensaje.lower().strip()
        
        if mensaje_lower in ['si', 'sí', 'yes', 'confirmar', 'ok']:
            # Crear la carrera en la base de datos
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
                    # created_at se crea automáticamente
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
                conversacion['estado'] = CONVERSATION_STATES['CARRERA_ACTIVA']
                
                # Notificar al conductor
                taxista = Taxi.objects.get(id=conversacion['datos']['taxista_sugerido'])
                if taxista.user.phone_number:
                    self._notificar_conductor(taxista.user.phone_number, ride)
                
                respuesta = f"""✅ *¡Carrera confirmada!* 🚕

Tu carrera ha sido asignada al conductor *{taxista.user.get_full_name()}*

📱 Número de carrera: #{ride.id}
⏱️ El conductor llegará en aproximadamente 5-10 minutos

Puedes seguir el estado de tu carrera escribiendo *ESTADO*

¡Buen viaje! 🎉"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
                
            except Exception as e:
                logger.error(f"Error al crear carrera: {str(e)}")
                conversacion['estado'] = CONVERSATION_STATES['INICIO']
                respuesta = """❌ Hubo un error al crear la carrera.

Por favor, intenta nuevamente escribiendo *MENU*"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
        
        elif mensaje_lower in ['no', 'cancelar', 'cancel']:
            conversacion['estado'] = CONVERSATION_STATES['INICIO']
            conversacion['datos'] = {}
            
            respuesta = """❌ Carrera cancelada.

Escribe *MENU* cuando quieras solicitar otra carrera."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
        
        else:
            respuesta = """Por favor, responde *SÍ* para confirmar o *NO* para cancelar."""
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
    
    def _manejar_carrera_activa(self, numero_telefono, mensaje, conversacion):
        """Maneja comandos durante una carrera activa"""
        mensaje_lower = mensaje.lower().strip()
        
        if mensaje_lower in ['estado', 'status']:
            return self._mostrar_estado_carrera(numero_telefono, conversacion)
        
        elif mensaje_lower in ['cancelar', 'cancel']:
            return self._cancelar_carrera_activa(numero_telefono, conversacion)
        
        elif mensaje_lower in ['menu', 'inicio']:
            conversacion['estado'] = CONVERSATION_STATES['INICIO']
            return self._manejar_inicio(numero_telefono, 'menu', conversacion)
        
        else:
            respuesta = """Tienes una carrera activa 🚕

Comandos disponibles:
• *ESTADO* - Ver estado de la carrera
• *CANCELAR* - Cancelar la carrera
• *MENU* - Volver al menú principal"""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
    
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
        """Calcula la tarifa estimada basada en la distancia"""
        # Tarifa base + tarifa por km
        tarifa_base = 5000  # COP
        tarifa_por_km = 2500  # COP
        
        return tarifa_base + (distancia_km * tarifa_por_km)
    
    def _obtener_o_crear_usuario(self, numero_telefono, nombre):
        """Obtiene o crea un usuario basado en el número de teléfono"""
        try:
            # Buscar usuario existente
            usuario = AppUser.objects.filter(phone_number=numero_telefono).first()
            
            if not usuario:
                # Crear nuevo usuario
                username = f"whatsapp_{numero_telefono.replace('+', '')}"
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
        mensaje = f"""🚕 *Nueva carrera asignada!*

📱 Carrera #{ride.id}
👤 Cliente: {ride.customer.get_full_name()}
📍 Origen: {ride.origin}
📍 Destino: {ride.destinations.first().destination if ride.destinations.exists() else 'N/A'}

¡Dirígete al punto de recogida!"""
        
        self.enviar_mensaje(numero_conductor, mensaje)
    
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
                    
                    respuesta += "Escribe *MENU* para más opciones"
                else:
                    respuesta = """No tienes carreras activas en este momento.

Escribe *MENU* para solicitar una nueva carrera."""
            else:
                respuesta = """No encontré tu perfil en el sistema.

Escribe *MENU* para comenzar."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
            
        except Exception as e:
            logger.error(f"Error al mostrar carreras: {str(e)}")
            return False
    
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
Estado: {estado_emoji}
Conductor: {ride.driver.get_full_name() if ride.driver else 'Sin asignar'}
Origen: {ride.origin}
Destino: {ride.destinations.first().destination if ride.destinations.exists() else 'N/A'}

Escribe *MENU* para más opciones"""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            else:
                respuesta = """No tienes una carrera activa.

Escribe *MENU* para solicitar una."""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
                
        except Exception as e:
            logger.error(f"Error al mostrar estado: {str(e)}")
            return False
    
    def _mostrar_ayuda(self, numero_telefono):
        """Muestra información de ayuda"""
        respuesta = """ℹ️ *Ayuda - Servicio de Taxis*

*Comandos disponibles:*

• *MENU* - Ver menú principal
• *SOLICITAR* - Pedir una carrera
• *MIS CARRERAS* - Ver carreras activas
• *ESTADO* - Ver estado de carrera actual
• *CANCELAR* - Cancelar una carrera
• *AYUDA* - Ver esta ayuda

*¿Cómo solicitar una carrera?*

1. Escribe *SOLICITAR*
2. Envía tu dirección de origen
3. Envía tu dirección de destino
4. Confirma la carrera

*Soporte:*
Para asistencia, contacta al: +57 XXX XXX XXXX

Escribe *MENU* para volver al inicio"""
        
        self.enviar_mensaje(numero_telefono, respuesta)
        return True
    
    def _normalizar_telefono(self, numero):
        """Normaliza el formato del número de teléfono"""
        # Eliminar espacios y caracteres especiales
        numero = numero.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Asegurar que tenga el código de país
        if not numero.startswith('+'):
            numero = '+' + numero
        
        return numero
    
    def _iniciar_cancelacion(self, numero_telefono, conversacion):
        """Inicia el proceso de cancelación"""
        try:
            usuario = AppUser.objects.filter(phone_number=numero_telefono).first()
            
            if usuario:
                carreras_activas = Ride.objects.filter(
                    customer=usuario,
                    status__in=['requested', 'accepted', 'in_progress']
                )
                
                if carreras_activas.exists():
                    respuesta = "🚕 *Carreras que puedes cancelar:*\n\n"
                    
                    for ride in carreras_activas:
                        respuesta += f"• Carrera #{ride.id} - {ride.get_status_display()}\n"
                    
                    respuesta += "\nResponde con el número de carrera que deseas cancelar.\nEjemplo: *#123*"
                    
                    conversacion['estado'] = 'esperando_id_cancelacion'
                else:
                    respuesta = """No tienes carreras activas para cancelar.

Escribe *MENU* para volver al inicio."""
            else:
                respuesta = """No encontré tu perfil.

Escribe *MENU* para comenzar."""
            
            self.enviar_mensaje(numero_telefono, respuesta)
            return True
            
        except Exception as e:
            logger.error(f"Error al iniciar cancelación: {str(e)}")
            return False
    
    def _cancelar_carrera_activa(self, numero_telefono, conversacion):
        """Cancela la carrera activa"""
        try:
            ride_id = conversacion['datos'].get('ride_id')
            
            if ride_id:
                ride = Ride.objects.get(id=ride_id)
                ride.status = 'canceled'
                ride.save()
                
                conversacion['estado'] = CONVERSATION_STATES['INICIO']
                conversacion['datos'] = {}
                
                respuesta = f"""✅ Carrera #{ride.id} cancelada exitosamente.

Escribe *MENU* cuando quieras solicitar otra carrera."""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return True
            else:
                respuesta = """No tienes una carrera activa para cancelar.

Escribe *MENU* para volver al inicio."""
                
                self.enviar_mensaje(numero_telefono, respuesta)
                return False
                
        except Exception as e:
            logger.error(f"Error al cancelar carrera: {str(e)}")
            return False


# Instancia global del agente
whatsapp_agent = WhatsAppAgent()
