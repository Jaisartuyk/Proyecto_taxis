"""
API endpoints para gestionar destinos de carreras
Permite agregar, editar y eliminar destinos individuales
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.db.models import Q
from decimal import Decimal
import googlemaps
from django.conf import settings

from .models import Ride, RideDestination, AppUser


def calculate_route_distance_and_price(ride):
    """
    Calcula la distancia total y precio de una carrera con múltiples destinos
    usando Google Maps Distance Matrix API
    
    Args:
        ride: Objeto Ride
        
    Returns:
        dict: {'distance_km': float, 'price': Decimal}
    """
    try:
        # Obtener todos los destinos ordenados
        destinations = RideDestination.objects.filter(ride=ride).order_by('order')
        
        if not destinations.exists():
            return {'distance_km': 0.0, 'price': Decimal('0.00')}
        
        # Inicializar cliente de Google Maps
        gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
        
        # Crear lista de waypoints: [Origen, Destino1, Destino2, ...]
        waypoints = [
            (ride.origin_latitude, ride.origin_longitude)
        ]
        
        for dest in destinations:
            waypoints.append((dest.destination_latitude, dest.destination_longitude))
        
        # Calcular distancia total sumando segmentos consecutivos
        total_distance_meters = 0
        
        for i in range(len(waypoints) - 1):
            origin = waypoints[i]
            destination = waypoints[i + 1]
            
            # Llamar a Distance Matrix API
            result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode='driving'
            )
            
            if result['rows'][0]['elements'][0]['status'] == 'OK':
                distance = result['rows'][0]['elements'][0]['distance']['value']
                total_distance_meters += distance
            else:
                print(f"⚠️ No se pudo calcular distancia del segmento {i+1}")
        
        # Convertir a kilómetros
        distance_km = total_distance_meters / 1000.0
        
        # Calcular precio
        threshold = 4.44  # Límite para tarifa base
        base_price = Decimal('2.00')  # Precio base
        price_per_km = Decimal('0.25')  # Precio por kilómetro adicional
        
        price = base_price
        if distance_km > threshold:
            extra_distance = Decimal(str(distance_km - threshold))
            price += extra_distance * price_per_km
        
        print(f"📏 Distancia calculada: {distance_km:.2f} km")
        print(f"💰 Precio calculado: ${price:.2f}")
        
        return {
            'distance_km': distance_km,
            'price': price
        }
        
    except Exception as e:
        print(f"❌ Error calculando distancia y precio: {e}")
        import traceback
        traceback.print_exc()
        return {'distance_km': 0.0, 'price': Decimal('0.00')}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_destination(request, ride_id):
    """
    Agregar un nuevo destino a una carrera
    
    POST /api/rides/{ride_id}/destinations/
    Body:
    {
        "destination": "Dirección del destino",
        "latitude": -2.1234,
        "longitude": -79.5678,
        "order": 2  // Opcional, si no se proporciona se agrega al final
    }
    """
    try:
        user = request.user
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el usuario sea el cliente
        if user != ride.customer:
            return Response({
                'error': 'Solo el cliente puede modificar los destinos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la carrera no haya iniciado
        if ride.status not in ['requested', 'accepted']:
            return Response({
                'error': 'No se pueden modificar destinos de una carrera en curso o completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener datos del destino
        destination = request.data.get('destination')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        order = request.data.get('order')
        
        if not all([destination, latitude, longitude]):
            return Response({
                'error': 'Faltan datos: destination, latitude, longitude'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si no se proporciona order, agregar al final
        if order is None:
            max_order = RideDestination.objects.filter(ride=ride).count()
            order = max_order
        
        # Crear nuevo destino
        new_destination = RideDestination.objects.create(
            ride=ride,
            destination=destination,
            destination_latitude=float(latitude),
            destination_longitude=float(longitude),
            order=int(order)
        )
        
        print(f"✅ Nuevo destino agregado a carrera #{ride_id}: {destination}")
        
        # Recalcular distancia y precio
        result = calculate_route_distance_and_price(ride)
        ride.price = result['price']
        ride.save(update_fields=['price'])
        
        return Response({
            'success': True,
            'message': 'Destino agregado correctamente',
            'destination_id': new_destination.id,
            'new_price': float(ride.price),
            'new_distance_km': result['distance_km']
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"❌ Error agregando destino: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Error al agregar destino: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_destination(request, ride_id, destination_id):
    """
    Editar un destino existente
    
    PUT /api/rides/{ride_id}/destinations/{destination_id}/
    Body:
    {
        "destination": "Nueva dirección",
        "latitude": -2.1234,
        "longitude": -79.5678
    }
    """
    try:
        user = request.user
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el usuario sea el cliente
        if user != ride.customer:
            return Response({
                'error': 'Solo el cliente puede modificar los destinos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la carrera no haya iniciado
        if ride.status not in ['requested', 'accepted']:
            return Response({
                'error': 'No se pueden modificar destinos de una carrera en curso o completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el destino
        try:
            dest = RideDestination.objects.get(id=destination_id, ride=ride)
        except RideDestination.DoesNotExist:
            return Response({
                'error': 'Destino no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Actualizar datos
        if 'destination' in request.data:
            dest.destination = request.data['destination']
        if 'latitude' in request.data:
            dest.destination_latitude = float(request.data['latitude'])
        if 'longitude' in request.data:
            dest.destination_longitude = float(request.data['longitude'])
        
        dest.save()
        
        print(f"✅ Destino #{destination_id} actualizado: {dest.destination}")
        
        # Recalcular distancia y precio
        result = calculate_route_distance_and_price(ride)
        ride.price = result['price']
        ride.save(update_fields=['price'])
        
        return Response({
            'success': True,
            'message': 'Destino actualizado correctamente',
            'new_price': float(ride.price),
            'new_distance_km': result['distance_km']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error actualizando destino: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Error al actualizar destino: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_destination(request, ride_id, destination_id):
    """
    Eliminar un destino de una carrera
    
    DELETE /api/rides/{ride_id}/destinations/{destination_id}/
    """
    try:
        user = request.user
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el usuario sea el cliente
        if user != ride.customer:
            return Response({
                'error': 'Solo el cliente puede modificar los destinos'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Verificar que la carrera no haya iniciado
        if ride.status not in ['requested', 'accepted']:
            return Response({
                'error': 'No se pueden modificar destinos de una carrera en curso o completada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el destino
        try:
            dest = RideDestination.objects.get(id=destination_id, ride=ride)
        except RideDestination.DoesNotExist:
            return Response({
                'error': 'Destino no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que no sea el único destino
        total_destinations = RideDestination.objects.filter(ride=ride).count()
        if total_destinations <= 1:
            return Response({
                'error': 'No se puede eliminar el único destino de la carrera'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        destination_name = dest.destination
        dest.delete()
        
        print(f"✅ Destino eliminado de carrera #{ride_id}: {destination_name}")
        
        # Recalcular distancia y precio
        result = calculate_route_distance_and_price(ride)
        ride.price = result['price']
        ride.save(update_fields=['price'])
        
        return Response({
            'success': True,
            'message': 'Destino eliminado correctamente',
            'new_price': float(ride.price),
            'new_distance_km': result['distance_km']
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error eliminando destino: {e}")
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Error al eliminar destino: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_destinations(request, ride_id):
    """
    Listar todos los destinos de una carrera
    
    GET /api/rides/{ride_id}/destinations/
    """
    try:
        user = request.user
        
        # Obtener la carrera
        try:
            ride = Ride.objects.get(id=ride_id)
        except Ride.DoesNotExist:
            return Response({
                'error': 'Carrera no encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verificar que el usuario sea el conductor o el cliente
        if user != ride.driver and user != ride.customer:
            return Response({
                'error': 'No tienes permiso para ver esta carrera'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Obtener destinos ordenados
        destinations = RideDestination.objects.filter(ride=ride).order_by('order')
        
        destinations_data = [{
            'id': dest.id,
            'destination': dest.destination,
            'latitude': dest.destination_latitude,
            'longitude': dest.destination_longitude,
            'order': dest.order
        } for dest in destinations]
        
        return Response({
            'success': True,
            'destinations': destinations_data,
            'total': len(destinations_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error listando destinos: {e}")
        return Response({
            'error': f'Error al listar destinos: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
