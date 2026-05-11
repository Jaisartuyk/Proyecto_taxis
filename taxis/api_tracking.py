"""
API para Link de Seguimiento en Vivo
Permite a los familiares del cliente ver el taxi en tiempo real en un mapa público.

Endpoints:
- POST /api/rides/<ride_id>/share/ → Generar link de seguimiento
- GET /track/<token>/ → Página pública con mapa en tiempo real
- GET /api/track/<token>/location/ → Ubicación actual del taxi (JSON para polling)
"""

import logging
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone
from datetime import timedelta

from .models import Ride, RideTrackingLink, Taxi

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
    if request.user and request.user.is_authenticated:
        return request.user
    return None


@api_view(['POST'])
@permission_classes([])
def create_tracking_link(request, ride_id):
    """
    🔗 Generar un link de seguimiento público para una carrera activa.
    
    Solo el cliente de la carrera o el conductor pueden generar el link.
    
    Returns:
    {
        "success": true,
        "tracking_url": "https://taxis-deaquipalla.up.railway.app/track/a7h2k9l1/",
        "token": "a7h2k9l1",
        "expires_at": "2026-05-11T20:00:00Z"
    }
    """
    try:
        user = get_user_from_token(request)
        if not user:
            return Response(
                {'error': 'Token de autenticación requerido'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        ride = get_object_or_404(Ride, id=ride_id)
        
        # Verificar que el usuario sea parte de la carrera
        if user != ride.customer and user != ride.driver:
            return Response(
                {'error': 'Solo puedes compartir carreras en las que participas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verificar que la carrera esté activa
        if ride.status not in ['accepted', 'in_progress']:
            return Response(
                {'error': 'Solo puedes compartir carreras activas'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar si ya existe un link activo para esta carrera
        existing_link = RideTrackingLink.objects.filter(
            ride=ride,
            is_active=True
        ).first()
        
        if existing_link and existing_link.is_valid():
            # Retornar el link existente
            base_url = _get_base_url()
            tracking_url = f"{base_url}/track/{existing_link.token}/"
            
            return Response({
                'success': True,
                'tracking_url': tracking_url,
                'token': existing_link.token,
                'expires_at': existing_link.expires_at.isoformat() if existing_link.expires_at else None,
                'message': 'Link de seguimiento existente'
            }, status=status.HTTP_200_OK)
        
        # Crear nuevo link
        token = RideTrackingLink.generate_token()
        
        # Asegurar que el token sea único
        while RideTrackingLink.objects.filter(token=token).exists():
            token = RideTrackingLink.generate_token()
        
        tracking_link = RideTrackingLink.objects.create(
            ride=ride,
            token=token,
            is_active=True,
            expires_at=timezone.now() + timedelta(hours=4)  # Expira en 4 horas
        )
        
        base_url = _get_base_url()
        tracking_url = f"{base_url}/track/{token}/"
        
        logger.info(f"🔗 Link de seguimiento creado: {tracking_url} para carrera #{ride.id}")
        
        return Response({
            'success': True,
            'tracking_url': tracking_url,
            'token': token,
            'expires_at': tracking_link.expires_at.isoformat(),
            'message': 'Link de seguimiento creado exitosamente. Compártelo con tu familia.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"❌ Error creando link de seguimiento: {e}", exc_info=True)
        return Response(
            {'error': f'Error al crear link: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def live_tracking_page(request, token):
    """
    🗺️ Página pública con mapa en tiempo real.
    NO requiere autenticación (la familia del cliente accede con el link).
    """
    tracking_link = get_object_or_404(RideTrackingLink, token=token)
    
    # Incrementar contador de vistas
    tracking_link.increment_views()
    
    ride = tracking_link.ride
    
    # Obtener info del conductor y ubicación actual
    driver_info = {}
    current_location = None
    
    if ride.driver:
        driver_info = {
            'name': ride.driver.get_full_name(),
            'driver_number': ride.driver.driver_number or 'N/A',
            'vehicle_plate': ride.driver.vehicle_plate or 'N/A',
            'vehicle_brand': ride.driver.vehicle_brand or '',
            'vehicle_model': ride.driver.vehicle_model or '',
            'vehicle_color': ride.driver.vehicle_color or '',
        }
        
        # Obtener ubicación actual del taxi
        try:
            taxi = Taxi.objects.get(user=ride.driver)
            if taxi.latitude and taxi.longitude:
                current_location = {
                    'latitude': taxi.latitude,
                    'longitude': taxi.longitude,
                }
        except Taxi.DoesNotExist:
            pass
    
    # Obtener destinos
    destinations = []
    for dest in ride.destinations.all().order_by('order'):
        destinations.append({
            'address': dest.destination,
            'latitude': dest.destination_latitude,
            'longitude': dest.destination_longitude,
        })
    
    context = {
        'tracking_link': tracking_link,
        'ride': ride,
        'driver_info': driver_info,
        'current_location': current_location,
        'origin': {
            'address': ride.origin,
            'latitude': ride.origin_latitude,
            'longitude': ride.origin_longitude,
        },
        'destinations': destinations,
        'is_valid': tracking_link.is_valid(),
        'ride_status': ride.status,
        'ride_status_display': ride.get_status_display(),
        'token': token,
        'google_maps_key': settings.GOOGLE_API_KEY,
    }
    
    return render(request, 'live_tracking.html', context)


def get_tracking_location(request, token):
    """
    📍 Obtener ubicación actual del taxi (JSON).
    Llamado por polling desde la página pública cada 5 segundos.
    NO requiere autenticación.
    """
    try:
        tracking_link = get_object_or_404(RideTrackingLink, token=token)
        ride = tracking_link.ride
        
        # Verificar que el link siga válido
        if not tracking_link.is_valid():
            return JsonResponse({
                'success': False,
                'active': False,
                'message': 'Este link de seguimiento ya no está activo.',
                'ride_status': ride.status,
                'ride_status_display': ride.get_status_display(),
            })
        
        # Obtener ubicación del conductor
        if ride.driver:
            try:
                taxi = Taxi.objects.get(user=ride.driver)
                return JsonResponse({
                    'success': True,
                    'active': True,
                    'latitude': taxi.latitude,
                    'longitude': taxi.longitude,
                    'updated_at': taxi.updated_at.isoformat() if taxi.updated_at else None,
                    'driver_name': ride.driver.get_full_name(),
                    'ride_status': ride.status,
                    'ride_status_display': ride.get_status_display(),
                })
            except Taxi.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': False,
            'active': True,
            'message': 'Ubicación del conductor no disponible aún.',
            'ride_status': ride.status,
            'ride_status_display': ride.get_status_display(),
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo ubicación de tracking: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _get_base_url():
    """Obtener URL base del sistema"""
    import os
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        return 'https://taxis-deaquipalla.up.railway.app'
    return 'http://localhost:8000'
