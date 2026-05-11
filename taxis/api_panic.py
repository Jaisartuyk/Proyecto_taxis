"""
API para Botón de Pánico - Sistema de Seguridad para Conductores
Endpoints:
- POST /api/panic/ → Activar alerta de pánico
- POST /api/panic/<id>/resolve/ → Resolver alerta
- GET /api/panic/active/ → Listar alertas activas
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from geopy.distance import geodesic

from .models import PanicAlert, Taxi, AppUser, Ride

logger = logging.getLogger(__name__)


def get_user_from_token(request):
    """Obtener usuario desde el token de autenticación"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.replace('Token ', '')
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return None
    # Fallback: usuario autenticado por sesión
    if request.user and request.user.is_authenticated:
        return request.user
    return None


@api_view(['POST'])
@permission_classes([])
def activate_panic(request):
    """
    🚨 Activar alerta de pánico desde la app móvil del conductor.
    
    Body:
    {
        "latitude": -0.1234,
        "longitude": -78.5678
    }
    
    Returns:
    {
        "success": true,
        "alert_id": 1,
        "message": "Alerta de pánico activada. La central ha sido notificada."
    }
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return Response(
                {'error': 'Token de autenticación requerido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Validar que sea conductor
        if user.role != 'driver':
            return Response(
                {'error': 'Solo conductores pueden activar el botón de pánico'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if latitude is None or longitude is None:
            return Response(
                {'error': 'Latitud y longitud son requeridas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lat = float(latitude)
            lng = float(longitude)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Coordenadas inválidas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar carrera activa del conductor (si tiene una)
        active_ride = Ride.objects.filter(
            driver=user,
            status__in=['accepted', 'in_progress']
        ).first()
        
        # Crear alerta de pánico
        alert = PanicAlert.objects.create(
            driver=user,
            organization=user.organization,
            latitude=lat,
            longitude=lng,
            ride=active_ride,
            status='active'
        )
        
        logger.warning(f"🚨🚨🚨 ALERTA DE PÁNICO #{alert.id} - Conductor: {user.get_full_name()} "
                       f"({user.username}) - Ubicación: ({lat}, {lng})")
        
        # ========================================
        # 1. Notificar por WebSocket a la Central
        # ========================================
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            
            # Enviar a la sala de audio/conductores (la central está aquí)
            async_to_sync(channel_layer.group_send)(
                'audio_conductores',
                {
                    'type': 'send_panic_alert',
                    'alert_id': alert.id,
                    'driver_id': user.id,
                    'driver_name': user.get_full_name(),
                    'driver_number': user.driver_number or 'N/A',
                    'latitude': lat,
                    'longitude': lng,
                    'ride_id': active_ride.id if active_ride else None,
                    'timestamp': alert.created_at.isoformat(),
                }
            )
            logger.info(f"✅ Alerta de pánico enviada por WebSocket a la central")
        except Exception as e:
            logger.error(f"❌ Error enviando alerta WebSocket: {e}")
        
        # ========================================
        # 2. Notificar a los 5 taxistas más cercanos (FCM)
        # ========================================
        try:
            nearby_drivers_notified = _notify_nearby_drivers(user, lat, lng, alert)
            logger.info(f"✅ {nearby_drivers_notified} conductores cercanos notificados por FCM")
        except Exception as e:
            logger.error(f"❌ Error notificando conductores cercanos: {e}")
        
        # ========================================
        # 3. Notificar al admin de la cooperativa (Push Web)
        # ========================================
        try:
            _notify_admin(user, alert)
            logger.info(f"✅ Admin de cooperativa notificado")
        except Exception as e:
            logger.error(f"❌ Error notificando admin: {e}")
        
        return Response({
            'success': True,
            'alert_id': alert.id,
            'message': '🚨 Alerta de pánico activada. La central y conductores cercanos han sido notificados.',
            'data': {
                'alert_id': alert.id,
                'driver_name': user.get_full_name(),
                'latitude': lat,
                'longitude': lng,
                'status': 'active',
                'created_at': alert.created_at.isoformat(),
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"❌ Error activando alerta de pánico: {e}", exc_info=True)
        return Response(
            {'error': f'Error al activar alerta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([])
def resolve_panic(request, alert_id):
    """
    ✅ Resolver/Cerrar una alerta de pánico (solo admin o superadmin).
    
    Body:
    {
        "status": "resolved",  // "resolved" o "false_alarm"
        "notes": "Se verificó que el conductor está bien."
    }
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return Response(
                {'error': 'Token de autenticación requerido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Solo admins pueden resolver alertas
        if user.role != 'admin' and not user.is_superuser:
            return Response(
                {'error': 'Solo administradores pueden resolver alertas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        alert = get_object_or_404(PanicAlert, id=alert_id)
        
        # Validar que el admin sea de la misma organización (a menos que sea superadmin)
        if not user.is_superuser and alert.organization != user.organization:
            return Response(
                {'error': 'No puedes resolver alertas de otra cooperativa'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status', 'resolved')
        notes = request.data.get('notes', '')
        
        if new_status == 'false_alarm':
            alert.mark_false_alarm(user, notes)
        else:
            alert.resolve(user, notes)
        
        logger.info(f"✅ Alerta #{alert.id} resuelta por {user.get_full_name()} - Estado: {new_status}")
        
        # Notificar al conductor que su alerta fue atendida
        try:
            from .fcm_notifications import send_fcm_notification
            send_fcm_notification(
                user=alert.driver,
                title="✅ Alerta Atendida",
                body=f"Tu alerta de emergencia fue atendida por {user.get_full_name()}.",
                data={
                    'type': 'panic_resolved',
                    'alert_id': str(alert.id),
                }
            )
        except Exception as e:
            logger.error(f"❌ Error notificando resolución al conductor: {e}")
        
        return Response({
            'success': True,
            'message': f'Alerta #{alert.id} resuelta exitosamente.',
            'data': {
                'alert_id': alert.id,
                'status': alert.status,
                'resolved_by': user.get_full_name(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error resolviendo alerta: {e}", exc_info=True)
        return Response(
            {'error': f'Error al resolver alerta: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([])
def active_alerts(request):
    """
    📋 Listar alertas de pánico activas (para la Central de Monitoreo).
    Filtradas por organización del admin.
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return Response(
                {'error': 'Token de autenticación requerido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Filtrar por organización
        if user.is_superuser:
            alerts = PanicAlert.objects.filter(status__in=['active', 'attended'])
        elif user.organization:
            alerts = PanicAlert.objects.filter(
                organization=user.organization,
                status__in=['active', 'attended']
            )
        else:
            alerts = PanicAlert.objects.none()
        
        alerts_data = []
        for alert in alerts.select_related('driver', 'ride', 'attended_by'):
            alerts_data.append({
                'id': alert.id,
                'driver': {
                    'id': alert.driver.id,
                    'name': alert.driver.get_full_name(),
                    'phone': alert.driver.phone_number or 'N/A',
                    'driver_number': alert.driver.driver_number or 'N/A',
                },
                'latitude': alert.latitude,
                'longitude': alert.longitude,
                'address': alert.address or 'Calculando...',
                'status': alert.status,
                'ride_id': alert.ride.id if alert.ride else None,
                'created_at': alert.created_at.isoformat(),
                'attended_by': alert.attended_by.get_full_name() if alert.attended_by else None,
                'notes': alert.notes,
            })
        
        return Response({
            'success': True,
            'count': len(alerts_data),
            'alerts': alerts_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"❌ Error listando alertas: {e}", exc_info=True)
        return Response(
            {'error': f'Error al listar alertas: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =====================================================
# FUNCIONES AUXILIARES
# =====================================================

def _notify_nearby_drivers(alerting_driver, lat, lng, alert, max_drivers=5):
    """Notifica por FCM a los conductores más cercanos"""
    from .fcm_notifications import send_fcm_notification
    
    origin = (lat, lng)
    
    # Buscar taxis con ubicación de la misma organización
    nearby_taxis = Taxi.objects.select_related('user').filter(
        user__role='driver',
        user__organization=alerting_driver.organization,
        latitude__isnull=False,
        longitude__isnull=False
    ).exclude(user=alerting_driver)
    
    if not nearby_taxis.exists():
        return 0
    
    # Ordenar por distancia y tomar los más cercanos
    taxis_with_distance = []
    for taxi in nearby_taxis:
        try:
            dist = geodesic(origin, (taxi.latitude, taxi.longitude)).km
            taxis_with_distance.append((taxi, dist))
        except Exception:
            continue
    
    taxis_with_distance.sort(key=lambda x: x[1])
    closest = taxis_with_distance[:max_drivers]
    
    notified = 0
    for taxi, distance in closest:
        try:
            result = send_fcm_notification(
                user=taxi.user,
                title="🚨 ¡EMERGENCIA! Compañero en peligro",
                body=f"{alerting_driver.get_full_name()} activó el botón de pánico a {distance:.1f} km de ti.",
                data={
                    'type': 'panic_alert',
                    'alert_id': str(alert.id),
                    'driver_name': alerting_driver.get_full_name(),
                    'latitude': str(lat),
                    'longitude': str(lng),
                    'distance_km': f'{distance:.1f}',
                },
                sound='alarm'
            )
            if result.get('sent', 0) > 0:
                notified += 1
        except Exception as e:
            logger.error(f"❌ Error notificando a {taxi.user.username}: {e}")
    
    return notified


def _notify_admin(driver, alert):
    """Notifica al admin de la cooperativa por push web y FCM"""
    from .push_notifications import send_push_notification
    from .fcm_notifications import send_fcm_notification
    
    if not driver.organization:
        return
    
    # Buscar admins de la organización
    admins = AppUser.objects.filter(
        organization=driver.organization,
        role='admin',
        is_active=True
    )
    
    for admin in admins:
        # Push web
        try:
            send_push_notification(
                user=admin,
                title="🚨 ¡ALERTA DE PÁNICO!",
                body=f"El conductor {driver.get_full_name()} (Unidad #{driver.driver_number or 'N/A'}) ha activado el botón de pánico.",
                data={
                    'type': 'panic_alert',
                    'alert_id': alert.id,
                    'url': '/api/panic/active/',
                }
            )
        except Exception as e:
            logger.error(f"❌ Error enviando push web al admin {admin.username}: {e}")
        
        # FCM
        try:
            send_fcm_notification(
                user=admin,
                title="🚨 ¡ALERTA DE PÁNICO!",
                body=f"Conductor {driver.get_full_name()} en emergencia.",
                data={
                    'type': 'panic_alert',
                    'alert_id': str(alert.id),
                    'driver_name': driver.get_full_name(),
                    'latitude': str(alert.latitude),
                    'longitude': str(alert.longitude),
                }
            )
        except Exception as e:
            logger.error(f"❌ Error enviando FCM al admin {admin.username}: {e}")
