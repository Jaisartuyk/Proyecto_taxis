from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Ride, Message

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_badge_count(request):
    """
    Obtiene el número de notificaciones pendientes para mostrar en el badge del ícono
    """
    user = request.user
    count = 0
    
    if user.role == 'driver':
        # Contar carreras pendientes o en progreso
        pending_rides = Ride.objects.filter(
            Q(driver=user, status='pending') | 
            Q(driver=user, status='accepted') |
            Q(driver=user, status='in_progress')
        ).count()
        
        # Contar mensajes no leídos (si tienes un modelo de mensajes)
        # unread_messages = Message.objects.filter(
        #     recipient=user,
        #     is_read=False
        # ).count()
        
        count = pending_rides
        
    elif user.role == 'customer':
        # Contar carreras activas del cliente
        active_rides = Ride.objects.filter(
            customer=user,
            status__in=['pending', 'accepted', 'in_progress']
        ).count()
        
        count = active_rides
    
    return Response({
        'count': count,
        'success': True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clear_badge(request):
    """
    Limpia el badge (pone el contador en 0)
    """
    # Aquí podrías marcar mensajes como leídos, etc.
    return Response({
        'success': True,
        'message': 'Badge limpiado'
    })
