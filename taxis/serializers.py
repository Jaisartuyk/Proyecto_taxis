"""
Serializers para la API REST de la aplicación de taxis
Convierte modelos Django a JSON y viceversa
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Taxi, Ride, RideDestination, Rating, 
    ChatMessage, AppUser
)

User = get_user_model()


# =====================================================
# SERIALIZERS DE USUARIO Y PERFIL
# =====================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer básico de usuario (sin información sensible)"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone_number', 'profile_picture'
        ]
        read_only_fields = ['id', 'username']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer completo de perfil de usuario"""
    full_name = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    total_ratings = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'role', 'phone_number', 'national_id',
            'profile_picture', 'last_latitude', 'last_longitude',
            'average_rating', 'total_ratings'
        ]
        read_only_fields = ['id', 'username', 'role']
        extra_kwargs = {
            'national_id': {'write_only': True},  # No exponer cédula en GET
        }
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_average_rating(self, obj):
        """Calificación promedio del usuario"""
        ratings = Rating.objects.filter(rated=obj)
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 2)
        return None
    
    def get_total_ratings(self, obj):
        """Total de calificaciones recibidas"""
        return Rating.objects.filter(rated=obj).count()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos usuarios"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role'
        ]
    
    def validate(self, data):
        """Validar que las contraseñas coincidan"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return data
    
    def create(self, validated_data):
        """Crear usuario con contraseña encriptada"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


# =====================================================
# SERIALIZERS DE TAXI
# =====================================================

class TaxiSerializer(serializers.ModelSerializer):
    """Serializer de taxi con información del conductor"""
    driver = UserSerializer(source='user', read_only=True)
    driver_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Taxi
        fields = [
            'id', 'plate_number', 'vehicle_description',
            'latitude', 'longitude', 'updated_at',
            'direccion_origen', 'driver', 'driver_name'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def get_driver_name(self, obj):
        return obj.user.get_full_name()


# =====================================================
# SERIALIZERS DE DESTINOS
# =====================================================

class RideDestinationSerializer(serializers.ModelSerializer):
    """Serializer de destinos de una carrera"""
    
    class Meta:
        model = RideDestination
        fields = [
            'id', 'destination', 'destination_latitude',
            'destination_longitude', 'order'
        ]
        read_only_fields = ['id']


# =====================================================
# SERIALIZERS DE CARRERAS (RIDES)
# =====================================================

class RideListSerializer(serializers.ModelSerializer):
    """Serializer para listar carreras (vista resumida)"""
    customer_name = serializers.SerializerMethodField()
    driver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    destinations_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = [
            'id', 'customer_name', 'driver_name', 'origin',
            'status', 'status_display', 'price', 'created_at',
            'start_time', 'end_time', 'destinations_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_customer_name(self, obj):
        return obj.customer.get_full_name() if obj.customer else None
    
    def get_driver_name(self, obj):
        return obj.driver.get_full_name() if obj.driver else None
    
    def get_destinations_count(self, obj):
        return obj.destinations.count()


class RideDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado de carrera (incluye toda la información)"""
    customer = UserSerializer(read_only=True)
    driver = UserSerializer(read_only=True)
    destinations = RideDestinationSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    origin_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Ride
        fields = [
            'id', 'customer', 'driver', 'origin', 'origin_address',
            'origin_latitude', 'origin_longitude', 'destinations',
            'start_time', 'end_time', 'price', 'status', 'status_display',
            'created_at', 'notified'
        ]
        read_only_fields = ['id', 'created_at', 'notified']
    
    def get_origin_address(self, obj):
        """Obtener dirección de origen si está disponible"""
        try:
            return obj.get_origin_address()
        except:
            return obj.origin


class RideCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevas carreras"""
    destinations = RideDestinationSerializer(many=True, required=False)
    
    class Meta:
        model = Ride
        fields = [
            'origin', 'origin_latitude', 'origin_longitude',
            'destinations', 'price'
        ]
    
    def create(self, validated_data):
        """Crear carrera con destinos"""
        destinations_data = validated_data.pop('destinations', [])
        
        # El customer se asigna desde el request.user en la vista
        ride = Ride.objects.create(**validated_data)
        
        # Crear destinos
        for idx, dest_data in enumerate(destinations_data):
            RideDestination.objects.create(
                ride=ride,
                order=idx,
                **dest_data
            )
        
        return ride


class RideUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar carreras (solo ciertos campos)"""
    
    class Meta:
        model = Ride
        fields = ['status', 'driver', 'price', 'start_time', 'end_time']
        read_only_fields = ['driver']  # El driver se asigna en la vista


# =====================================================
# SERIALIZERS DE CALIFICACIONES
# =====================================================

class RatingSerializer(serializers.ModelSerializer):
    """Serializer de calificaciones"""
    rater_name = serializers.SerializerMethodField()
    rated_name = serializers.SerializerMethodField()
    stars_display = serializers.CharField(source='stars_display', read_only=True)
    ride_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Rating
        fields = [
            'id', 'ride', 'ride_info', 'rater', 'rater_name',
            'rated', 'rated_name', 'rating', 'stars_display',
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'rater']
    
    def get_rater_name(self, obj):
        return obj.rater.get_full_name()
    
    def get_rated_name(self, obj):
        return obj.rated.get_full_name()
    
    def get_ride_info(self, obj):
        """Información básica de la carrera"""
        return {
            'id': obj.ride.id,
            'origin': obj.ride.origin,
            'status': obj.ride.status,
            'created_at': obj.ride.created_at
        }


class RatingCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear calificaciones"""
    
    class Meta:
        model = Rating
        fields = ['ride', 'rated', 'rating', 'comment']
    
    def validate_rating(self, value):
        """Validar que la calificación esté entre 1 y 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError('La calificación debe estar entre 1 y 5')
        return value
    
    def validate(self, data):
        """Validar que no exista una calificación duplicada"""
        user = self.context['request'].user
        ride = data['ride']
        
        if Rating.objects.filter(ride=ride, rater=user).exists():
            raise serializers.ValidationError('Ya has calificado esta carrera')
        
        # Validar que el usuario sea parte de la carrera
        if user != ride.customer and user != ride.driver:
            raise serializers.ValidationError('Solo puedes calificar carreras en las que participaste')
        
        # Validar que la carrera esté completada
        if ride.status != 'completed':
            raise serializers.ValidationError('Solo puedes calificar carreras completadas')
        
        return data


# =====================================================
# SERIALIZERS DE CHAT
# =====================================================

class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer de mensajes de chat con soporte de media"""
    sender_name = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'sender', 'sender_name', 'recipient',
            'recipient_name', 'message', 'timestamp', 'is_read',
            'message_type', 'media_url', 'thumbnail_url', 'metadata'  # Campos de media
        ]
        read_only_fields = ['id', 'timestamp', 'sender']
    
    def get_sender_name(self, obj):
        return obj.sender.get_full_name()
    
    def get_recipient_name(self, obj):
        return obj.recipient.get_full_name()
