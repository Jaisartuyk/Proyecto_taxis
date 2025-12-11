from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q, Count
from .models import Ride, ChatMessage

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_badge_count(request):
    """
    Obtiene el número de notificaciones pendientes para mostrar en el badge del ícono
    Incluye: carreras pendientes + mensajes no leídos
    """
    user = request.user
    rides_count = 0
    messages_count = 0
    
    if user.role == 'driver':
        # Contar carreras pendientes o en progreso
        rides_count = Ride.objects.filter(
            Q(driver=user, status='pending') | 
            Q(driver=user, status='accepted') |
            Q(driver=user, status='in_progress')
        ).count()
        
        # Contar mensajes no leídos recibidos
        messages_count = ChatMessage.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
    elif user.role == 'customer':
        # Contar carreras activas del cliente
        rides_count = Ride.objects.filter(
            customer=user,
            status__in=['pending', 'accepted', 'in_progress']
        ).count()
        
        # Contar mensajes no leídos recibidos
        messages_count = ChatMessage.objects.filter(
            recipient=user,
            is_read=False
        ).count()
        
    elif user.role == 'admin':
        # Para administradores: carreras sin asignar + mensajes no leídos
        rides_count = Ride.objects.filter(
            status='pending',
            driver__isnull=True
        ).count()
        
        messages_count = ChatMessage.objects.filter(
            recipient=user,
            is_read=False
        ).count()
    
    total_count = rides_count + messages_count
    
    return Response({
        'count': total_count,
        'rides': rides_count,
        'messages': messages_count,
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_messages_read(request):
    """
    Marca los mensajes de una conversación como leídos
    """
    sender_id = request.data.get('sender_id')
    
    if not sender_id:
        return Response({
            'success': False,
            'error': 'sender_id es requerido'
        }, status=400)
    
    # Marcar como leídos todos los mensajes del remitente hacia el usuario actual
    updated = ChatMessage.objects.filter(
        sender_id=sender_id,
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({
        'success': True,
        'marked': updated,
        'message': f'{updated} mensajes marcados como leídos'
    })
