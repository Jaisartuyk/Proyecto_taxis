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

# ============================================
# MODELO DE ORGANIZACIÓN (MULTI-TENANT)
# ============================================

class Organization(models.Model):
    """
    Cooperativa o grupo de taxis.
    Cada organización tiene sus propios conductores, carreras y configuración.
    """
    PLAN_CHOICES = [
        ('owner', 'Propietario'),  # Plan especial para "De Aquí Pa'llá"
        ('basic', 'Básico'),
        ('standard', 'Estándar'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    STATUS_CHOICES = [
        ('trial', 'Prueba'),
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('canceled', 'Cancelado'),
    ]
    
    # Información básica
    name = models.CharField(
        max_length=200,
        help_text="Nombre de la cooperativa"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL única: deaquipalla.com/taxi-oro"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción de la cooperativa"
    )
    
    # Branding
    logo = CloudinaryField(
        'image',
        folder='org_logos',
        blank=True,
        null=True,
        help_text="Logo de la cooperativa"
    )
    primary_color = models.CharField(
        max_length=7,
        default='#FFD700',
        help_text="Color primario en formato hexadecimal (#FFD700)"
    )
    secondary_color = models.CharField(
        max_length=7,
        default='#000000',
        help_text="Color secundario en formato hexadecimal (#000000)"
    )
    
    # Contacto
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Ecuador')
    
    # Suscripción y facturación
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='basic'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial'
    )
    max_drivers = models.IntegerField(
        default=10,
        help_text="Número máximo de conductores permitidos"
    )
    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=29.00,
        help_text="Tarifa mensual en USD"
    )
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Porcentaje de comisión por carrera (0-100)"
    )
    
    # Fechas importantes
    trial_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de fin del período de prueba"
    )
    subscription_starts_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de inicio de la suscripción"
    )
    subscription_ends_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de fin de la suscripción"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Admin de la cooperativa (se asignará después de crear AppUser)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        null=True,  # Temporal para la migración
        blank=True
    )
    
    # ============================================
    # CAMPOS FASE 3: PANEL DE ADMINISTRACIÓN
    # ============================================
    
    # Estado y suspensión
    is_active = models.BooleanField(
        default=True,
        help_text="Si la organización está activa"
    )
    suspended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de suspensión"
    )
    suspension_reason = models.TextField(
        blank=True,
        help_text="Razón de la suspensión"
    )
    
    # Branding adicional
    welcome_message = models.TextField(
        blank=True,
        help_text="Mensaje de bienvenida personalizado"
    )
    contact_phone_display = models.CharField(
        max_length=20,
        blank=True,
        help_text="Teléfono de contacto para mostrar"
    )
    
    # Facturación
    billing_email = models.EmailField(
        blank=True,
        help_text="Email para facturación"
    )
    billing_address = models.TextField(
        blank=True,
        help_text="Dirección de facturación"
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        help_text="RUC o identificación fiscal"
    )
    
    # Estadísticas (se actualizan automáticamente)
    total_rides = models.IntegerField(
        default=0,
        help_text="Total de carreras completadas"
    )
    total_revenue = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Ingresos totales generados"
    )
    total_commission = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Comisiones totales cobradas"
    )
    
    class Meta:
        verbose_name = 'Organización'
        verbose_name_plural = 'Organizaciones'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def is_active(self):
        """Verifica si la organización está activa"""
        return self.status == 'active'
    
    def can_add_driver(self):
        """Verifica si se pueden agregar más conductores"""
        current_drivers = self.users.filter(role='driver').count()
        return current_drivers < self.max_drivers
    
    def get_driver_count(self):
        """Retorna el número de conductores activos"""
        return self.users.filter(role='driver').count()
    
    def get_active_rides_count(self):
        """Retorna el número de carreras activas"""
        return self.rides.filter(status__in=['requested', 'accepted', 'in_progress']).count()
    
    def get_total_revenue(self):
        """Retorna los ingresos totales de carreras completadas"""
        from django.db.models import Sum
        total = self.rides.filter(
            status='completed',
            price__isnull=False
        ).aggregate(total=Sum('price'))['total']
        return total or 0


class AppUser(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Cliente'),
        ('driver', 'Taxista'),
        ('admin', 'Administrador'),
    ]
    
    DRIVER_STATUS_CHOICES = [
        ('pending', 'Pendiente de Aprobación'),
        ('approved', 'Aprobado'),
        ('suspended', 'Suspendido'),
        ('rejected', 'Rechazado'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15, default='', blank=True, null=True)  # Número de celular
    national_id = models.CharField(max_length=20, default='', blank=True, null=True)  # Número de cédula
    profile_picture = CloudinaryField('image', folder='profile_pics', blank=True, null=True, transformation={'quality': 'auto', 'fetch_format': 'auto'})  # Foto de perfil en Cloudinary
    telegram_chat_id = models.CharField(max_length=255, null=True, blank=True)  # ID de Telegram para mensajes directos
    last_latitude = models.FloatField(null=True, blank=True)
    last_longitude = models.FloatField(null=True, blank=True)
    
    # ============================================
    # CAMPOS MULTI-TENANT Y GESTIÓN DE CONDUCTORES
    # ============================================
    
    # Organización a la que pertenece
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # ⚠️ IMPORTANTE: null=True para migración segura
        blank=True,
        help_text="Cooperativa a la que pertenece el usuario"
    )
    
    # Número de unidad del conductor (001, 002, 003, etc.)
    driver_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True,
        help_text="Número de unidad del conductor (ej: 001, 002, 003)"
    )
    
    # Estado de aprobación del conductor
    driver_status = models.CharField(
        max_length=20,
        choices=DRIVER_STATUS_CHOICES,
        default='pending',
        help_text="Estado de aprobación del conductor"
    )
    
    # Fecha de aprobación
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que el conductor fue aprobado"
    )
    
    # Admin que aprobó al conductor
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='drivers_approved',
        help_text="Administrador que aprobó al conductor"
    )
    
    def clean(self):
        if not self.first_name or not self.last_name:
            raise ValidationError('Los nombres completos (nombre y apellido) son obligatorios.')

    def __str__(self):
        return f'{self.get_full_name()} ({self.role})'  # Muestra el nombre completo y rol
    
    def is_active_driver(self):
        """Verifica si el conductor está aprobado y activo"""
        return self.role == 'driver' and self.driver_status == 'approved' and self.is_active
    
    def can_accept_rides(self):
        """Verifica si el conductor puede aceptar carreras"""
        return self.is_active_driver() and self.organization and self.organization.is_active()

class Taxi(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plate_number = models.CharField(max_length=10, default='')  # Número de placa
    vehicle_description = models.TextField(default='')  # Descripción del vehículo
    
    # Campos adicionales para perfil móvil
    car_model = models.CharField(max_length=100, blank=True, null=True)  # Modelo del vehículo
    car_color = models.CharField(max_length=50, blank=True, null=True)  # Color del vehículo
    car_year = models.IntegerField(blank=True, null=True)  # Año del vehículo
    is_active = models.BooleanField(default=True)  # Si el taxi está activo
    
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
    notified = models.BooleanField(default=False)
    
    # ============================================
    # CAMPOS MULTI-TENANT
    # ============================================
    
    # Organización que gestiona esta carrera
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='rides',
        null=True,  # ⚠️ IMPORTANTE: null=True para migración segura
        blank=True,
        help_text="Cooperativa que gestiona esta carrera"
    )
    
    # Comisión cobrada por la plataforma
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Comisión cobrada por la plataforma (calculada automáticamente)"
    )

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

# ============================================
# CÓDIGOS DE INVITACIÓN (MULTI-TENANT)
# ============================================

class InvitationCode(models.Model):
    """
    Códigos de invitación con QR para registrar clientes y conductores.
    Cada organización tiene sus propios códigos.
    """
    ROLE_CHOICES = [
        ('customer', 'Cliente'),
        ('driver', 'Conductor'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invitation_codes',
        help_text="Organización que genera el código"
    )
    code = models.CharField(
        max_length=12,
        unique=True,
        help_text="Código único de invitación (ej: TAXI-ABC123)"
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Rol para el que es válido este código"
    )
    
    # Límites de uso
    max_uses = models.IntegerField(
        default=0,
        help_text="Número máximo de usos (0 = ilimitado)"
    )
    current_uses = models.IntegerField(
        default=0,
        help_text="Número de veces que se ha usado"
    )
    
    # Validez temporal
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración (null = sin expiración)"
    )
    
    # Estado
    is_active = models.BooleanField(
        default=True,
        help_text="Si el código está activo"
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_invitation_codes',
        help_text="Admin que creó el código"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notas
    notes = models.TextField(
        blank=True,
        help_text="Notas internas sobre este código"
    )
    
    class Meta:
        verbose_name = 'Código de Invitación'
        verbose_name_plural = 'Códigos de Invitación'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['organization', 'role']),
        ]
    
    def __str__(self):
        return f"{self.code} ({self.organization.name} - {self.get_role_display()})"
    
    def is_valid(self):
        """Verifica si el código es válido para usar"""
        from django.utils import timezone
        
        # Verificar si está activo
        if not self.is_active:
            return False, "Código inactivo"
        
        # Verificar si expiró
        if self.expires_at and self.expires_at < timezone.now():
            return False, "Código expirado"
        
        # Verificar límite de usos
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False, "Código agotado"
        
        return True, "Código válido"
    
    def use(self):
        """Incrementa el contador de usos"""
        self.current_uses += 1
        self.save(update_fields=['current_uses', 'updated_at'])
    
    def get_qr_url(self):
        """Retorna la URL para el QR code"""
        from django.conf import settings
        base_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://taxis-deaquipalla.up.railway.app'
        return f"{base_url}/register/?code={self.code}"


# ============================================
# APLICACIÓN MÓVIL PARA CONDUCTORES
# ============================================

class DriverApp(models.Model):
    """
    Modelo para gestionar las versiones del APK de la aplicación Android para conductores.
    Solo el super admin puede subir nuevas versiones.
    """
    version = models.CharField(
        max_length=20,
        unique=True,
        help_text="Versión del APK (ej: 1.0.0, 1.1.0)"
    )
    
    apk_file = models.FileField(
        upload_to='driver_apps/',
        help_text="Archivo APK de la aplicación"
    )
    
    release_notes = models.TextField(
        blank=True,
        help_text="Notas de la versión (qué hay de nuevo)"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Si esta versión está activa para descarga"
    )
    
    is_latest = models.BooleanField(
        default=False,
        help_text="Si es la versión más reciente"
    )
    
    min_android_version = models.CharField(
        max_length=10,
        default="5.0",
        help_text="Versión mínima de Android requerida"
    )
    
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="Tamaño del archivo en bytes"
    )
    
    downloads_count = models.IntegerField(
        default=0,
        help_text="Número de descargas"
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_apps'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Aplicación de Conductor'
        verbose_name_plural = 'Aplicaciones de Conductor'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Driver App v{self.version} {'(Activa)' if self.is_latest else ''}"
    
    def save(self, *args, **kwargs):
        # Si esta versión se marca como latest, desmarcar las demás
        if self.is_latest:
            DriverApp.objects.exclude(pk=self.pk).update(is_latest=False)
        
        # Calcular tamaño del archivo si no está establecido
        if self.apk_file and not self.file_size:
            self.file_size = self.apk_file.size
        
        super().save(*args, **kwargs)
    
    def get_file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def increment_downloads(self):
        """Incrementa el contador de descargas"""
        self.downloads_count += 1
        self.save(update_fields=['downloads_count'])


# ============================================
# NEGOCIACIÓN DE PRECIOS
# ============================================

class PriceNegotiation(models.Model):
    """
    Negociación de precio entre cliente y central ANTES de crear la carrera.
    Similar a InDriver: cliente propone precio, central acepta/rechaza/contraoferta.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),           # Esperando respuesta de central
        ('accepted', 'Aceptada'),           # Central aceptó precio del cliente
        ('rejected', 'Rechazada'),          # Central rechazó
        ('counter_offered', 'Contraoferta'), # Central hizo contraoferta
        ('client_accepted', 'Cliente Aceptó'), # Cliente aceptó contraoferta
        ('client_rejected', 'Cliente Rechazó'), # Cliente rechazó contraoferta
        ('expired', 'Expirada'),            # Expiró sin respuesta
        ('ride_created', 'Carrera Creada'), # Se creó la carrera
    ]
    
    # Información del cliente
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='price_negotiations',
        limit_choices_to={'role': 'customer'}
    )
    
    # Organización (multi-tenant)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='price_negotiations',
        help_text="Cooperativa que gestiona esta negociación"
    )
    
    # Detalles del viaje
    origin = models.CharField(max_length=255, help_text="Dirección de origen")
    origin_latitude = models.FloatField(null=True, blank=True)
    origin_longitude = models.FloatField(null=True, blank=True)
    
    destination = models.CharField(max_length=255, help_text="Dirección de destino")
    destination_latitude = models.FloatField(null=True, blank=True)
    destination_longitude = models.FloatField(null=True, blank=True)
    
    # Precios
    suggested_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio sugerido por el sistema"
    )
    
    proposed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio propuesto por el cliente"
    )
    
    counter_offer_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Contraoferta de la central"
    )
    
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Precio final acordado"
    )
    
    # Estado y seguimiento
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Respuesta de la central
    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='price_negotiations_responded',
        help_text="Admin/Central que respondió"
    )
    
    response_message = models.TextField(
        blank=True,
        null=True,
        help_text="Mensaje de la central al cliente"
    )
    
    # Carrera creada (si se acepta)
    ride = models.OneToOneField(
        'Ride',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='negotiation',
        help_text="Carrera creada después de aceptar"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        help_text="Fecha de expiración (15 minutos después de crear)"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Negociación de Precio'
        verbose_name_plural = 'Negociaciones de Precio'
    
    def __str__(self):
        return f"Negociación #{self.id} - {self.customer.get_full_name()} - ${self.proposed_price}"
    
    def is_expired(self):
        """Verifica si la negociación expiró"""
        from django.utils import timezone
        return timezone.now() > self.expires_at and self.status == 'pending'
    
    def can_respond(self):
        """Verifica si la central puede responder"""
        return self.status in ['pending', 'counter_offered']
    
    def accept(self, admin_user, message=''):
        """Central acepta el precio propuesto por el cliente"""
        self.status = 'accepted'
        self.final_price = self.proposed_price
        self.responded_by = admin_user
        self.response_message = message or 'Precio aceptado. Creando carrera...'
        self.save()
    
    def reject(self, admin_user, message=''):
        """Central rechaza la propuesta"""
        self.status = 'rejected'
        self.responded_by = admin_user
        self.response_message = message or 'Lo sentimos, no podemos aceptar ese precio.'
        self.save()
    
    def counter_offer(self, admin_user, new_price, message=''):
        """Central hace una contraoferta"""
        self.status = 'counter_offered'
        self.counter_offer_price = new_price
        self.responded_by = admin_user
        self.response_message = message or f'Te ofrecemos ${new_price}'
        self.save()
    
    def client_accept_counter(self):
        """Cliente acepta la contraoferta"""
        self.status = 'client_accepted'
        self.final_price = self.counter_offer_price
        self.save()
    
    def client_reject_counter(self):
        """Cliente rechaza la contraoferta"""
        self.status = 'client_rejected'
        self.save()


# ============================================
# MODELO DE FACTURACIÓN (FASE 3)
# ============================================

class Invoice(models.Model):
    """Facturas mensuales para organizaciones"""
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Cooperativa facturada"
    )
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Número de factura único (ej: INV-2025-001)"
    )
    
    # Período facturado
    period_start = models.DateField(
        help_text="Inicio del período facturado"
    )
    period_end = models.DateField(
        help_text="Fin del período facturado"
    )
    
    # Montos
    subscription_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Tarifa de suscripción mensual"
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Comisiones cobradas en el período"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total a pagar"
    )
    
    # Estado y fechas
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de emisión"
    )
    due_date = models.DateField(
        help_text="Fecha de vencimiento"
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de pago"
    )
    
    # Archivo PDF
    pdf_file = models.FileField(
        upload_to='invoices/',
        null=True,
        blank=True,
        help_text="Archivo PDF de la factura"
    )
    
    # Notas
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales"
    )
    
    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.invoice_number} - {self.organization.name}"
    
    def is_overdue(self):
        """Verifica si la factura está vencida"""
        from django.utils import timezone
        if self.status == 'pending' and self.due_date < timezone.now().date():
            return True
        return False
    
    def mark_as_paid(self):
        """Marca la factura como pagada"""
        from django.utils import timezone
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.save()

