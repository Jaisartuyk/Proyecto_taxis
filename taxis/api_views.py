from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from django.utils import timezone

from models import Ride, RideDestination  # Asegúrate que el import sea correcto

User = get_user_model()

# 🚕 Login para conductores
class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Se requieren usuario y contraseña."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                token, created = Token.objects.get_or_create(user=user)
                role = getattr(user, 'role', None)

                if role == 'driver':
                    return Response({
                        "message": "Inicio de sesión exitoso.",
                        "user_id": user.id,
                        "role": role,
                        "token": token.key
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Acceso denegado: Solo conductores pueden iniciar sesión.",
                        "role": role
                    }, status=status.HTTP_403_FORBIDDEN)

            except Exception as e:
                return Response(
                    {"error": f"Error al generar el token: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(
            {"error": "Usuario o contraseña incorrectos."},
            status=status.HTTP_401_UNAUTHORIZED
        )


# 📲 Solicitud de carrera desde app Android
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_request_ride(request):
    data = request.data
    origin = data.get('origin')
    price = data.get('price')
    origin_lat = data.get('origin_latitude')
    origin_lng = data.get('origin_longitude')
    destinations = data.get('destinations', [])
    destination_coords = data.get('destination_coords', [])

    if origin and origin_lat and origin_lng and destinations and destination_coords:
        try:
            ride = Ride.objects.create(
                customer=request.user,
                origin=origin,
                origin_latitude=float(origin_lat),
                origin_longitude=float(origin_lng),
                price=price or 0.0,
                status='requested',
                start_time=timezone.now()
            )

            for i, destination in enumerate(destinations):
                lat, lng = map(float, destination_coords[i].split(','))
                RideDestination.objects.create(
                    ride=ride,
                    destination=destination,
                    destination_latitude=lat,
                    destination_longitude=lng,
                    order=i
                )

            return Response({
                "success": True,
                "ride_id": ride.id,
                "message": "Carrera solicitada correctamente."
            }, status=status.HTTP_201_CREATED)

        except ValueError:
            return Response({
                "success": False,
                "message": "Error al procesar las coordenadas."
            }, status=status.HTTP_400_BAD_REQUEST)

    return Response({
        "success": False,
        "message": "Datos incompletos."
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_available_rides(request):
    if request.user.role != 'driver':
        return Response({'error': 'Acceso denegado'}, status=403)

    rides = Ride.objects.filter(status='requested').order_by('created_at')
    data = []
    for ride in rides:
        destinations = [
            {
                "destination": d.destination,
                "latitude": d.destination_latitude,
                "longitude": d.destination_longitude
            } for d in ride.destinations.all()
        ]
        data.append({
            "id": ride.id,
            "origin": ride.origin,
            "origin_latitude": ride.origin_latitude,
            "origin_longitude": ride.origin_longitude,
            "price": str(ride.price),
            "customer_id": ride.customer.id,
            "destinations": destinations,
            "created_at": ride.created_at,
        })

    return Response({"rides": data})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_accept_ride(request, ride_id):
    if request.user.role != 'driver':
        return Response({'error': 'Solo los conductores pueden aceptar carreras.'}, status=403)

    try:
        ride = Ride.objects.get(id=ride_id)

        if ride.status != 'requested':
            return Response({'error': 'La carrera ya fue aceptada o no está disponible.'}, status=400)

        ride.driver = request.user
        ride.status = 'in_progress'
        ride.start_time = timezone.now()
        ride.save()

        return Response({
            "success": True,
            "message": "Carrera aceptada.",
            "ride_id": ride.id
        })

    except Ride.DoesNotExist:
        return Response({'error': 'Carrera no encontrada.'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_update_ride_status(request, ride_id):
    new_status = request.data.get('status')

    if new_status not in ['completed', 'canceled']:
        return Response({'error': 'Estado inválido.'}, status=400)

    try:
        ride = Ride.objects.get(id=ride_id)

        if ride.driver != request.user:
            return Response({'error': 'No tienes permiso para modificar esta carrera.'}, status=403)

        if new_status == 'completed':
            ride.status = 'completed'
            ride.end_time = timezone.now()
        elif new_status == 'canceled':
            ride.status = 'canceled'

        ride.save()

        return Response({
            "success": True,
            "new_status": ride.status,
            "message": "Carrera actualizada con éxito."
        })

    except Ride.DoesNotExist:
        return Response({'error': 'Carrera no encontrada.'}, status=404)  