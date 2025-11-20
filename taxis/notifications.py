"""
Sistema de notificaciones push para la aplicación de taxis
"""
import json
import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Ride, AppUser

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Servicio centralizado para enviar notificaciones"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    def send_ride_notification(self, ride, notification_type, message, target_user=None):
        """
        Envía notificación sobre una carrera
        
        Args:
            ride: Objeto Ride
            notification_type: Tipo de notificación ('new_ride', 'accepted', 'completed', etc.)
            message: Mensaje a enviar
            target_user: Usuario específico (opcional)
        """
        try:
            # Preparar datos de la notificación
            notification_data = {
                'type': 'ride_notification',
                'ride_id': ride.id,
                'notification_type': notification_type,
                'message': message,
                'timestamp': ride.created_at.isoformat(),
                'ride_status': ride.status,
                'customer_name': ride.customer.get_full_name(),
                'driver_name': ride.driver.get_full_name() if ride.driver else None,
            }
            
            # Enviar a usuario específico si se especifica
            if target_user:
                self._send_to_user(target_user, notification_data)
            else:
                # Enviar a todos los usuarios relevantes
                self._send_to_relevant_users(ride, notification_data)
                
            logger.info(f"✅ Notificación enviada: {notification_type} para carrera {ride.id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {str(e)}")
    
    def send_location_update(self, user, latitude, longitude, location_type='tracking'):
        """
        Envía actualización de ubicación
        
        Args:
            user: Usuario que actualiza ubicación
            latitude: Latitud
            longitude: Longitud
            location_type: Tipo de ubicación ('tracking', 'pickup', 'destination')
        """
        try:
            location_data = {
                'type': 'location_update',
                'user_id': user.id,
                'user_name': user.get_full_name(),
                'user_role': user.role,
                'latitude': latitude,
                'longitude': longitude,
                'location_type': location_type,
                'timestamp': user.last_login.isoformat() if user.last_login else None,
            }
            
            # Enviar a la sala de tracking general
            async_to_sync(self.channel_layer.group_send)(
                'central_tracking',
                {
                    'type': 'location_update',
                    'data': location_data
                }
            )
            
            logger.info(f"📍 Ubicación actualizada: {user.get_full_name()} - {location_type}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando ubicación: {str(e)}")
    
    def send_system_notification(self, message, notification_type='info', target_roles=None):
        """
        Envía notificación del sistema
        
        Args:
            message: Mensaje a enviar
            notification_type: Tipo ('info', 'warning', 'error', 'success')
            target_roles: Lista de roles objetivo (opcional)
        """
        try:
            notification_data = {
                'type': 'system_notification',
                'message': message,
                'notification_type': notification_type,
                'timestamp': None,  # Se llenará automáticamente
            }
            
            if target_roles:
                # Enviar solo a usuarios con roles específicos
                for role in target_roles:
                    async_to_sync(self.channel_layer.group_send)(
                        f'role_{role}',
                        {
                            'type': 'system_notification',
                            'data': notification_data
                        }
                    )
            else:
                # Enviar a todos los usuarios conectados
                async_to_sync(self.channel_layer.group_send)(
                    'all_users',
                    {
                        'type': 'system_notification',
                        'data': notification_data
                    }
                )
            
            logger.info(f"📢 Notificación del sistema enviada: {notification_type}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación del sistema: {str(e)}")
    
    def _send_to_user(self, user, notification_data):
        """Envía notificación a un usuario específico"""
        try:
            async_to_sync(self.channel_layer.group_send)(
                f'user_{user.id}',
                {
                    'type': 'user_notification',
                    'data': notification_data
                }
            )
        except Exception as e:
            logger.error(f"❌ Error enviando a usuario {user.id}: {str(e)}")
    
    def _send_to_relevant_users(self, ride, notification_data):
        """Envía notificación a usuarios relevantes para la carrera"""
        try:
            # Enviar al cliente
            if ride.customer:
                self._send_to_user(ride.customer, notification_data)
            
            # Enviar al conductor si existe
            if ride.driver:
                self._send_to_user(ride.driver, notification_data)
            
            # Enviar a administradores
            admins = User.objects.filter(role='admin', is_active=True)
            for admin in admins:
                self._send_to_user(admin, notification_data)
                
        except Exception as e:
            logger.error(f"❌ Error enviando a usuarios relevantes: {str(e)}")
    
    def send_whatsapp_notification(self, phone_number, message):
        """
        Envía notificación por WhatsApp
        
        Args:
            phone_number: Número de teléfono
            message: Mensaje a enviar
        """
        try:
            from .whatsapp_agent_ai import whatsapp_agent_ai
            
            success = whatsapp_agent_ai.enviar_mensaje(phone_number, message)
            
            if success:
                logger.info(f"📱 Notificación WhatsApp enviada a {phone_number}")
            else:
                logger.error(f"❌ Error enviando WhatsApp a {phone_number}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error en notificación WhatsApp: {str(e)}")
            return False


# Instancia global del servicio
notification_service = NotificationService()


# Funciones de conveniencia
def notify_new_ride(ride):
    """Notifica nueva carrera disponible"""
    message = f"🚕 Nueva carrera disponible desde {ride.origin}"
    notification_service.send_ride_notification(ride, 'new_ride', message)


def notify_ride_accepted(ride):
    """Notifica que una carrera fue aceptada"""
    message = f"✅ Tu carrera fue aceptada por {ride.driver.get_full_name()}"
    notification_service.send_ride_notification(ride, 'accepted', message, ride.customer)


def notify_ride_completed(ride):
    """Notifica que una carrera fue completada"""
    message = f"🎉 Carrera completada. ¡Gracias por usar nuestros servicios!"
    notification_service.send_ride_notification(ride, 'completed', message, ride.customer)


def notify_ride_cancelled(ride):
    """Notifica que una carrera fue cancelada"""
    message = f"❌ La carrera desde {ride.origin} fue cancelada"
    notification_service.send_ride_notification(ride, 'cancelled', message)


def notify_driver_location_update(driver, lat, lng):
    """Notifica actualización de ubicación del conductor"""
    notification_service.send_location_update(driver, lat, lng, 'tracking')


def notify_system_maintenance(message):
    """Notifica mantenimiento del sistema"""
    notification_service.send_system_notification(
        f"🔧 Mantenimiento del sistema: {message}",
        'warning',
        ['driver', 'customer']
    )

