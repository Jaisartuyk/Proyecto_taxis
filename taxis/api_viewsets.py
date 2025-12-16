"""
ViewSets para la API REST de la aplicación de taxis
Maneja todas las operaciones CRUD para Flutter
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Avg, Count
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    Taxi, Ride, RideDestination, Rating,
    ChatMessage, AppUser
)
from .serializers import (
    UserSerializer, ProfileSerializer, RegisterSerializer,
    TaxiSerializer, RideListSerializer, RideDetailSerializer,
    RideCreateSerializer, RideUpdateSerializer,
    RatingSerializer, RatingCreateSerializer,
    ChatMessageSerializer
)


# =====================================================
# VIEWSET DE PERFIL Y USUARIOS
# =====================================================

class ProfileViewSet(viewsets.ViewSet):
    """
    ViewSet para gestionar el perfil del usuario autenticado
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """GET /api/profile/ - Obtener perfil del usuario actual"""
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    def update(self, request):
        """PUT/PATCH /api/profile/ - Actualizar perfil"""
        serializer = ProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def upload_picture(self, request):
        """POST /api/profile/upload_picture/ - Subir foto de perfil"""
        if 'picture' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó ninguna imagen'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        user.profile_picture = request.FILES['picture']
        user.save()
        
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """GET /api/profile/stats/ - Estadísticas del usuario"""
        user = request.user
        
        if user.role == 'driver':
            # Estadísticas de conductor
            rides = Ride.objects.filter(driver=user)
            stats = {
                'total_rides': rides.count(),
                'completed_rides': rides.filter(status='completed').count(),
                'canceled_rides': rides.filter(status='canceled').count(),
                'in_progress_rides': rides.filter(status='in_progress').count(),
                'total_earnings': sum(
                    ride.price for ride in rides.filter(status='completed') if ride.price
                ),
                'average_rating': Rating.objects.filter(rated=user).aggregate(
                    Avg('rating')
                )['rating__avg'] or 0,
                'total_ratings': Rating.objects.filter(rated=user).count(),
            }
        else:
            # Estadísticas de cliente
            rides = Ride.objects.filter(customer=user)
            stats = {
                'total_rides': rides.count(),
                'completed_rides': rides.filter(status='completed').count(),
                'canceled_rides': rides.filter(status='canceled').count(),
                'pending_rides': rides.filter(status='requested').count(),
                'total_spent': sum(
                    ride.price for ride in rides.filter(status='completed') if ride.price
                ),
            }
        
        return Response(stats)


class RegisterViewSet(viewsets.ViewSet):
    """
    ViewSet para registro de nuevos usuarios
    """
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def driver(self, request):
        """POST /api/register/driver/ - Registrar conductor"""
        data = request.data.copy()
        data['role'] = 'driver'
        
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Crear taxi asociado si se proporcionan datos
            if 'plate_number' in request.data:
                Taxi.objects.create(
                    user=user,
                    plate_number=request.data.get('plate_number', ''),
                    vehicle_description=request.data.get('vehicle_description', '')
                )
            
            return Response(
                {
                    'message': 'Conductor registrado exitosamente',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def customer(self, request):
        """POST /api/register/customer/ - Registrar cliente"""
        data = request.data.copy()
        data['role'] = 'customer'
        
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'Cliente registrado exitosamente',
                    'user': UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =====================================================
# VIEWSET DE CONDUCTORES
# =====================================================

class DriverViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar y ver conductores
    Solo lectura - los conductores se gestionan desde el admin
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TaxiSerializer
    queryset = Taxi.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'plate_number']
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """GET /api/drivers/nearby/?lat=X&lon=Y&radius=5 - Conductores cercanos"""
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = float(request.query_params.get('radius', 5))  # km
        
        if not lat or not lon:
            return Response(
                {'error': 'Se requieren parámetros lat y lon'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lat = float(lat)
        lon = float(lon)
        
        # Filtro simple por rango (para producción usar PostGIS)
        lat_range = radius / 111  # 1 grado ≈ 111 km
        lon_range = radius / (111 * abs(lat))
        
        nearby_taxis = Taxi.objects.filter(
            latitude__range=(lat - lat_range, lat + lat_range),
            longitude__range=(lon - lon_range, lon + lon_range)
        )
        
        serializer = self.get_serializer(nearby_taxis, many=True)
        return Response(serializer.data)


# =====================================================
# VIEWSET DE CARRERAS (RIDES)
# =====================================================

class RideViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para gestionar carreras
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar carreras según el rol del usuario"""
        user = self.request.user
        
        if user.role == 'driver':
            # Conductores ven carreras asignadas o disponibles
            return Ride.objects.filter(
                Q(driver=user) | Q(status='requested')
            ).order_by('-created_at')
        elif user.role == 'customer':
            # Clientes solo ven sus propias carreras
            return Ride.objects.filter(customer=user).order_by('-created_at')
        else:
            # Admins ven todas
            return Ride.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'list':
            return RideListSerializer
        elif self.action == 'create':
            return RideCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RideUpdateSerializer
        return RideDetailSerializer
    
    def perform_create(self, serializer):
        """Crear carrera asignando el customer automáticamente"""
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """POST /api/rides/{id}/accept/ - Aceptar carrera (conductor)"""
        ride = self.get_object()
        
        if request.user.role != 'driver':
            return Response(
                {'error': 'Solo los conductores pueden aceptar carreras'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ride.status != 'requested':
            return Response(
                {'error': 'Esta carrera ya no está disponible'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.driver = request.user
        ride.status = 'accepted'
        ride.save()
        
        serializer = RideDetailSerializer(ride)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """POST /api/rides/{id}/start/ - Iniciar carrera"""
        ride = self.get_object()
        
        if ride.driver != request.user:
            return Response(
                {'error': 'Solo el conductor asignado puede iniciar la carrera'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ride.status != 'accepted':
            return Response(
                {'error': 'La carrera debe estar aceptada primero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.status = 'in_progress'
        ride.start_time = timezone.now()
        ride.save()
        
        serializer = RideDetailSerializer(ride)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """POST /api/rides/{id}/complete/ - Completar carrera"""
        ride = self.get_object()
        
        if ride.driver != request.user:
            return Response(
                {'error': 'Solo el conductor asignado puede completar la carrera'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ride.status != 'in_progress':
            return Response(
                {'error': 'La carrera debe estar en progreso'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.status = 'completed'
        ride.end_time = timezone.now()
        ride.save()
        
        serializer = RideDetailSerializer(ride)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """POST /api/rides/{id}/cancel/ - Cancelar carrera"""
        ride = self.get_object()
        
        # Solo el cliente o conductor pueden cancelar
        if request.user not in [ride.customer, ride.driver]:
            return Response(
                {'error': 'No tienes permiso para cancelar esta carrera'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if ride.status == 'completed':
            return Response(
                {'error': 'No se puede cancelar una carrera completada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ride.status = 'canceled'
        ride.save()
        
        serializer = RideDetailSerializer(ride)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """GET /api/rides/available/ - Carreras disponibles para conductores"""
        if request.user.role != 'driver':
            return Response(
                {'error': 'Solo los conductores pueden ver carreras disponibles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        available_rides = Ride.objects.filter(status='requested').order_by('-created_at')
        serializer = RideListSerializer(available_rides, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """GET /api/rides/active/ - Carreras activas del usuario"""
        user = request.user
        
        if user.role == 'driver':
            active_rides = Ride.objects.filter(
                driver=user,
                status__in=['accepted', 'in_progress']
            )
        else:
            active_rides = Ride.objects.filter(
                customer=user,
                status__in=['requested', 'accepted', 'in_progress']
            )
        
        serializer = RideDetailSerializer(active_rides, many=True)
        return Response(serializer.data)


# =====================================================
# VIEWSET DE CALIFICACIONES
# =====================================================

class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar calificaciones
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar calificaciones del usuario"""
        user = self.request.user
        
        # Ver calificaciones recibidas y dadas
        return Rating.objects.filter(
            Q(rater=user) | Q(rated=user)
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        """Usar diferentes serializers según la acción"""
        if self.action == 'create':
            return RatingCreateSerializer
        return RatingSerializer
    
    def perform_create(self, serializer):
        """Crear calificación asignando el rater automáticamente"""
        serializer.save(rater=self.request.user)
    
    @action(detail=False, methods=['get'])
    def received(self, request):
        """GET /api/ratings/received/ - Calificaciones recibidas"""
        ratings = Rating.objects.filter(rated=request.user).order_by('-created_at')
        serializer = self.get_serializer(ratings, many=True)
        
        # Calcular promedio
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        
        return Response({
            'average': round(avg_rating, 2),
            'total': ratings.count(),
            'ratings': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def given(self, request):
        """GET /api/ratings/given/ - Calificaciones dadas"""
        ratings = Rating.objects.filter(rater=request.user).order_by('-created_at')
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)
