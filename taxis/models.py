from django.db import models
#from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField


#from django.utils.timezone import now

class AppUser(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Cliente'),
        ('driver', 'Taxista'),
        ('admin', 'Administrador'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, default='', blank=True, null=True)  # Número de celular
    national_id = models.CharField(max_length=20, default='', blank=True, null=True)  # Número de cédula
    profile_picture = CloudinaryField('image', folder='profile_pics', blank=True, null=True, transformation={'quality': 'auto', 'fetch_format': 'auto'})  # Foto de perfil en Cloudinary
    telegram_chat_id = models.CharField(max_length=255, null=True, blank=True)  # ID de Telegram para mensajes directos
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    def clean(self):
        if not self.first_name or not self.last_name:
            raise ValidationError('Los nombres completos (nombre y apellido) son obligatorios.')

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'  # Muestra el nombre completo y rol

class Taxi(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=10, default='')  # Número de placa
    vehicle_description = models.TextField(default='')  # Descripción del vehículo
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    direccion_origen = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.plate_number} - {self.user.get_full_name()}"

    def clean(self):
        # Validar que solo los usuarios con rol "driver" puedan tener un taxi asociado
        if self.user.role != 'driver':
            raise ValidationError('Solo un usuario con rol "Taxista" puede estar asociado a un taxi.')

    def save(self, *args, **kwargs):
        if self.direccion_origen and (self.latitude is None or self.longitude is None):
            geolocator = Nominatim(user_agent="mi_aplicacion")
            try:
                location = geolocator.geocode(self.direccion_origen, timeout=10)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
            except GeocoderTimedOut:
                print("Error: Tiempo de espera agotado al obtener la ubicación.")
        super().save(*args, **kwargs)


class TaxiRoute(models.Model):
    taxi = models.OneToOneField('Taxi', on_delete=models.CASCADE)
    is_available = models.BooleanField(default=False)  # Si el taxista está disponible
    passenger_1 = models.CharField(max_length=100, blank=True, null=True)
    passenger_2 = models.CharField(max_length=100, blank=True, null=True)
    passenger_3 = models.CharField(max_length=100, blank=True, null=True)
    passenger_4 = models.CharField(max_length=100, blank=True, null=True)
    estimated_arrival_time = models.DateTimeField(null=True, blank=True)  # Hora estimada de llegada

    @property
    def passengers(self):
        return [self.passenger_1, self.passenger_2, self.passenger_3, self.passenger_4]

class Ride(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Solicitada'),
        ('accepted', 'Aceptada'),
        ('in_progress', 'En progreso'),
        ('completed', 'Completada'),
        ('canceled', 'Cancelada'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rides_as_customer',
        limit_choices_to={'role': 'customer'},
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='rides_as_driver',
        null=True,
        blank=True,
        limit_choices_to={'role': 'driver'},
    )
    origin = models.CharField(max_length=255)
    origin_latitude = models.FloatField(null=True, blank=True)
    origin_longitude = models.FloatField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='requested')
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)  # <-- Nuevo campo

    def __str__(self):
        return f'Carrera de {self.customer.username} desde {self.origin} ({self.get_status_display()})'

    def get_origin_address(self):
        return self._get_address(self.origin_latitude, self.origin_longitude)

    @staticmethod
    def _get_address(lat, lon):
        if lat is None or lon is None:
            return "Dirección desconocida"
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'jsonv2'
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('display_name', 'Dirección desconocida')
        except requests.RequestException as e:
            print(f"Error en la solicitud: {e}")
            return "Dirección desconocida"

class RideDestination(models.Model):
    ride = models.ForeignKey(
        'Ride',
        on_delete=models.CASCADE,
        related_name='destinations'
    )
    destination = models.CharField(max_length=255)
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)  # Para mantener el orden de los destinos

    class Meta:
        ordering = ['order']  # Asegura que los destinos se recuperen en el orden correcto

    def __str__(self):
        return f'{self.destination} ({self.destination_latitude}, {self.destination_longitude})'
User = get_user_model()

class ConexionWebSocket(models.Model):
    ROLE_CHOICES = [
        ('driver', 'Conductor'),
        ('customer', 'Cliente'),
        ('central', 'Central'),
    ]

    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ws_conexiones'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES
    )
    channel_name = models.CharField(
        max_length=255, 
        unique=True,
        help_text="Identificador interno del canal WebSocket"
    )
    room_name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        help_text="Nombre del grupo WebSocket (ej. carrera_23)"
    )
    conectado = models.BooleanField(
        default=True,
        help_text="Si la conexión está activa o no"
    )
    ultima_conexion = models.DateTimeField(
        auto_now=True,
        help_text="Última vez que se conectó"
    )

    class Meta:
        verbose_name = "Conexión WebSocket"
        verbose_name_plural = "Conexiones WebSocket"
        ordering = ['-ultima_conexion']

    def __str__(self):
        return f"{self.user.username} ({self.role}) – Canal: {self.channel_name[:20]} – Activo: {self.conectado}"
    
class ConversacionTelegram(models.Model):
    chat_id = models.CharField(max_length=50, unique=True)
    paso_actual = models.CharField(max_length=50, default='inicio')
    datos = models.JSONField(default=dict)
    usuario = models.ForeignKey(AppUser, null=True, blank=True, on_delete=models.SET_NULL)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.chat_id} - {self.paso_actual}"


class Rating(models.Model):
    """Sistema de calificaciones para conductores y pasajeros"""
    RATING_CHOICES = [
        (1, '1 estrella'),
        (2, '2 estrellas'),
        (3, '3 estrellas'),
        (4, '4 estrellas'),
        (5, '5 estrellas'),
    ]
    
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='ratings_given')
    rated = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name='ratings_received')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['ride', 'rater', 'rated']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.rater.get_full_name()} calificó a {self.rated.get_full_name()} con {self.rating} estrellas"
    
    @property
    def stars_display(self):
        return '★' * self.rating + '☆' * (5 - self.rating)


class WebPushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='webpush_subscriptions'
    )
    subscription_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Suscripción de {self.user.username}"


# ============================================
# FIREBASE CLOUD MESSAGING (FCM)
# ============================================

class FCMToken(models.Model):
    """
    Almacena tokens FCM de dispositivos móviles
    Un usuario puede tener múltiples dispositivos
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fcm_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token FCM del dispositivo"
    )
    device_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID único del dispositivo (opcional)"
    )
    platform = models.CharField(
        max_length=20,
        choices=[
            ('android', 'Android'),
            ('ios', 'iOS'),
            ('web', 'Web'),
        ],
        default='android'
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Si el token está activo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Token FCM"
        verbose_name_plural = "Tokens FCM"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} - {self.token[:20]}..."


# ============================================
# MODELOS DE WHATSAPP
# ============================================

class WhatsAppConversation(models.Model):
    """Conversaciones de WhatsApp con usuarios"""
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('waiting', 'Esperando respuesta'),
        ('completed', 'Completada'),
        ('abandoned', 'Abandonada'),
    ]
    
    STATE_CHOICES = [
        ('inicio', 'Inicio'),
        ('esperando_origen', 'Esperando origen'),
        ('esperando_destino', 'Esperando destino'),
        ('confirmando_carrera', 'Confirmando carrera'),
        ('carrera_activa', 'Carrera activa'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whatsapp_conversations',
        null=True,
        blank=True,
        help_text="Usuario registrado (si existe)"
    )
    phone_number = models.CharField(
        max_length=20,
        help_text="Número de teléfono con código de país (+593...)"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nombre del contacto"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    state = models.CharField(
        max_length=30,
        choices=STATE_CHOICES,
        default='inicio',
        help_text="Estado actual de la conversación"
    )
    data = models.JSONField(
        default=dict,
        help_text="Datos temporales de la conversación (origen, destino, etc.)"
    )
    ride = models.ForeignKey(
        'Ride',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_conversations',
        help_text="Carrera asociada (si existe)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at']
        verbose_name = 'Conversación de WhatsApp'
        verbose_name_plural = 'Conversaciones de WhatsApp'
    
    def __str__(self):
        return f"{self.phone_number} - {self.name or 'Sin nombre'} ({self.get_status_display()})"


class WhatsAppMessage(models.Model):
    """Mensajes individuales de WhatsApp"""
    
    DIRECTION_CHOICES = [
        ('incoming', 'Entrante'),
        ('outgoing', 'Saliente'),
    ]
    
    TYPE_CHOICES = [
        ('text', 'Texto'),
        ('location', 'Ubicación'),
        ('image', 'Imagen'),
        ('audio', 'Audio'),
        ('document', 'Documento'),
    ]
    
    conversation = models.ForeignKey(
        WhatsAppConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES
    )
    message_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='text'
    )
    content = models.TextField(
        help_text="Contenido del mensaje"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadatos adicionales (coordenadas, URLs, etc.)"
    )
    message_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="ID del mensaje de WASender"
    )
    delivered = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Mensaje de WhatsApp'
        verbose_name_plural = 'Mensajes de WhatsApp'
    
    def __str__(self):
        direction_icon = '📥' if self.direction == 'incoming' else '📤'
        return f"{direction_icon} {self.conversation.phone_number} - {self.content[:50]}"


class WhatsAppStats(models.Model):
    """Estadísticas diarias de WhatsApp"""
    
    date = models.DateField(unique=True)
    total_messages = models.IntegerField(default=0)
    incoming_messages = models.IntegerField(default=0)
    outgoing_messages = models.IntegerField(default=0)
    new_conversations = models.IntegerField(default=0)
    active_conversations = models.IntegerField(default=0)
    completed_conversations = models.IntegerField(default=0)
    rides_requested = models.IntegerField(default=0)
    rides_completed = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Estadística de WhatsApp'
        verbose_name_plural = 'Estadísticas de WhatsApp'
    
    def __str__(self):
        return f"Stats {self.date}: {self.total_messages} mensajes"


class ChatMessage(models.Model):
    """Mensajes de chat interno entre usuarios (Conductores <-> Central)"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'Archivo'),
    ]
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_chat_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_chat_messages'
    )
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Campos para soporte de media (imágenes, videos)
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        help_text="Tipo de mensaje: texto, imagen, video, etc."
    )
    media_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL del archivo multimedia (imagen, video, etc.)"
    )
    thumbnail_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL del thumbnail (para videos o imágenes grandes)"
    )
    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Metadatos adicionales: {width, height, size, duration, format, etc.}"
    )

    class Meta:
        ordering = ['timestamp']
        verbose_name = 'Mensaje de Chat Interno'
        verbose_name_plural = 'Mensajes de Chat Interno'
        indexes = [
            models.Index(fields=['sender', 'recipient', 'timestamp']),
            models.Index(fields=['message_type']),
        ]

    def __str__(self):
        msg_preview = self.message[:20] if self.message else "(sin texto)"
        media_info = f" [{self.get_message_type_display()}]" if self.message_type != 'text' else ""
        return f"De {self.sender} para {self.recipient}: {msg_preview}{media_info}..."
    
    def has_media(self):
        """Verificar si el mensaje tiene archivo multimedia"""
        return bool(self.media_url)
    
    def is_image(self):
        """Verificar si es una imagen"""
        return self.message_type == 'image'
    
    def is_video(self):
        """Verificar si es un video"""
        return self.message_type == 'video'
    
    def get_thumbnail(self):
        """Obtener URL del thumbnail (o media_url si no hay thumbnail)"""
        return self.thumbnail_url or self.media_url