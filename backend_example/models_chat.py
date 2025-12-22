"""Modelo actualizado para ChatMessage con soporte de media
Modifica tu modelo existente agregando estos campos"""

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


# =====================================================
# MODELO ACTUALIZADO (BACKWARD COMPATIBLE)
# =====================================================

class ChatMessage(models.Model):
    """Mensajes de chat interno entre usuarios (Conductores <-> Central)
    
    ✅ CAMBIOS: Agregar estos campos al modelo existente
    ✅ COMPATIBILIDAD: Todos los campos nuevos son opcionales (null=True, blank=True)
    ✅ MIGRACIÓN: Ejecutar makemigrations y migrate después de agregar los campos
    """
    
    # Campos existentes (NO MODIFICAR)
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
    
    # =====================================================
    # NUEVOS CAMPOS PARA MEDIA (AGREGAR ESTOS)
    # =====================================================
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'Archivo'),
    ]
    
    # Tipo de mensaje (por defecto 'text' para mantener compatibilidad)
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text',
        help_text="Tipo de mensaje: texto, imagen, video, etc."
    )
    
    # URL del archivo en Cloudinary (o cualquier CDN)
    media_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL del archivo multimedia (imagen, video, etc.)"
    )
    
    # URL del thumbnail (principalmente para videos)
    thumbnail_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL del thumbnail (para videos o imágenes grandes)"
    )
    
    # Metadatos adicionales (dimensiones, tamaño, duración, etc.)
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
            models.Index(fields=['message_type']),  # Para filtrar por tipo
        ]

    def __str__(self):
        msg_preview = self.message[:20] if self.message else "(sin texto)"
        media_info = f" [{self.get_message_type_display()}]" if self.message_type != 'text' else ""
        return f"De {self.sender} para {self.recipient}: {msg_preview}{media_info}..."
    
    # Métodos helper
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


# =====================================================
# INSTRUCCIONES PARA INTEGRAR
# =====================================================

"""
PASO 1: Abre tu archivo taxis/models.py

PASO 2: Encuentra la clase ChatMessage (línea ~457)

PASO 3: Agrega estos campos ANTES del class Meta:

    MESSAGE_TYPE_CHOICES = [
        ('text', 'Texto'),
        ('image', 'Imagen'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('file', 'Archivo'),
    ]
    
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

PASO 4: (Opcional) Agrega los métodos helper al final de la clase:
    def has_media(self):
        return bool(self.media_url)
    
    def is_image(self):
        return self.message_type == 'image'
    
    def is_video(self):
        return self.message_type == 'video'
    
    def get_thumbnail(self):
        return self.thumbnail_url or self.media_url

PASO 5: Ejecutar migraciones:
    python manage.py makemigrations
    python manage.py migrate

✅ LISTO: Los mensajes existentes seguirán funcionando (message_type='text' por defecto)
"""

