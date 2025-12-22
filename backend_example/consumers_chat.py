"""Consumer de WebSocket para chat con soporte de media
Modifica tu ChatConsumer existente agregando estos cambios"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebSocketConsumer):
    """
    Consumer de WebSocket para chat con soporte de media
    
    ✅ CAMBIOS: Modificar tu ChatConsumer existente (taxis/consumers.py)
    ✅ COMPATIBILIDAD: Mantiene compatibilidad con mensajes de texto existentes
    """
    
    async def connect(self):
        # ... (código existente de connect, NO MODIFICAR) ...
        self.user = self.scope['user']
        # ... resto del código de connect ...
        pass
    
    async def disconnect(self, close_code):
        # ... (código existente de disconnect, NO MODIFICAR) ...
        pass
    
    async def receive(self, text_data):
        """
        ✅ MODIFICAR ESTA FUNCIÓN para soportar media
        
        Formato de mensaje esperado:
        {
            "type": "chat_message",
            "message": "Texto del mensaje (opcional si hay media)",
            "recipient_id": 123,
            "message_type": "text" | "image" | "video",  // NUEVO
            "media_url": "https://...",  // NUEVO
            "thumbnail_url": "https://...",  // NUEVO (opcional)
            "metadata": {...}  // NUEVO (opcional)
        }
        """
        data = json.loads(text_data)
        
        # Ignorar mensajes que no sean de chat
        message_type = data.get('type')
        if message_type and message_type != 'chat_message':
            return
        
        # =====================================================
        # CAMBIOS: Leer campos de media
        # =====================================================
        message = data.get('message', '')  # Ahora es opcional si hay media
        recipient_id = data.get('recipient_id')
        
        # Nuevos campos para media
        msg_type = data.get('message_type', 'text')  # Por defecto 'text' (compatible)
        media_url = data.get('media_url', None)
        thumbnail_url = data.get('thumbnail_url', None)
        metadata = data.get('metadata', {})
        
        # Validación: debe haber mensaje O media_url
        if not message and not media_url:
            print("Error: Faltan datos en el mensaje de chat (necesita 'message' o 'media_url')")
            return
        
        if not recipient_id:
            print("Error: Falta recipient_id")
            return
        
        # Determinar sender_id (código existente)
        if self.user.is_authenticated:
            sender_id = self.user.id
            sender_name = self.user.get_full_name() or self.user.username
        else:
            sender_id = int(self.target_user_id)
            sender_name = f"Conductor {self.target_user_id}"
        
        # =====================================================
        # CAMBIO: Guardar mensaje con campos de media
        # =====================================================
        await self.save_message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message=message,
            message_type=msg_type,  # NUEVO
            media_url=media_url,  # NUEVO
            thumbnail_url=thumbnail_url,  # NUEVO
            metadata=metadata  # NUEVO
        )
        
        # Grupo del destinatario
        recipient_group_name = f'chat_{recipient_id}'
        
        # =====================================================
        # CAMBIO: Incluir campos de media en el payload
        # =====================================================
        chat_payload = {
            'type': 'chat_message',
            'message': message,
            'sender_id': sender_id,
            'sender_name': sender_name,
            # Nuevos campos
            'message_type': msg_type,
            'media_url': media_url,
            'thumbnail_url': thumbnail_url,
            'metadata': metadata,
        }
        
        # Enviar mensaje al destinatario
        await self.channel_layer.group_send(recipient_group_name, chat_payload)
        print(f"Mensaje de {sender_id} enviado a {recipient_id} (tipo: {msg_type})")
        
        # Enviar notificación push (código existente)
        await self.send_chat_push_notification(sender_id, recipient_id, message)
        
        # Enviar mensaje de vuelta al remitente
        await self.channel_layer.group_send(self.room_group_name, chat_payload)
    
    async def chat_message(self, event):
        """
        ✅ MODIFICAR ESTA FUNCIÓN para incluir campos de media en la respuesta
        
        Esta función se llama cuando se recibe un mensaje del grupo
        """
        # Obtener badge count (código existente)
        if self.user.is_authenticated:
            badge_count = await self.get_badge_count(self.user.id)
        else:
            badge_count = 0
        
        # =====================================================
        # CAMBIO: Incluir campos de media en la respuesta
        # =====================================================
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event.get('message', ''),
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'badge_count': badge_count,
            'update_badge': True,
            # Nuevos campos (con valores por defecto para compatibilidad)
            'message_type': event.get('message_type', 'text'),
            'media_url': event.get('media_url'),
            'thumbnail_url': event.get('thumbnail_url'),
            'metadata': event.get('metadata', {}),
        }))
    
    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, message, 
                     message_type='text', media_url=None, thumbnail_url=None, metadata=None):
        """
        ✅ MODIFICAR ESTA FUNCIÓN para guardar campos de media
        
        Cambios:
        - Agregar parámetros: message_type, media_url, thumbnail_url, metadata
        - Guardar estos campos al crear ChatMessage
        """
        from .models import ChatMessage, AppUser
        try:
            sender = AppUser.objects.get(id=sender_id)
            recipient = AppUser.objects.get(id=recipient_id)
            
            # =====================================================
            # CAMBIO: Crear mensaje con campos de media
            # =====================================================
            ChatMessage.objects.create(
                sender=sender,
                recipient=recipient,
                message=message,
                message_type=message_type,  # NUEVO
                media_url=media_url,  # NUEVO
                thumbnail_url=thumbnail_url,  # NUEVO
                metadata=metadata or {},  # NUEVO
            )
            
            print(f"Mensaje guardado en BD: {sender} -> {recipient} (tipo: {message_type})")
        except Exception as e:
            print(f"Error al guardar mensaje: {e}")
    
    # ... resto de métodos existentes (get_badge_count, send_chat_push_notification, etc.) ...


# =====================================================
# INSTRUCCIONES PARA INTEGRAR
# =====================================================

"""
PASO 1: Abre tu archivo taxis/consumers.py

PASO 2: Encuentra la función async def receive(self, text_data) (línea ~308)

PASO 3: Después de leer 'message' y 'recipient_id', agrega:
    msg_type = data.get('message_type', 'text')
    media_url = data.get('media_url', None)
    thumbnail_url = data.get('thumbnail_url', None)
    metadata = data.get('metadata', {})

PASO 4: Modifica la validación para permitir mensajes sin texto si hay media:
    if not message and not media_url:
        print("Error: Faltan datos...")
        return

PASO 5: Modifica la llamada a save_message para incluir los nuevos campos:
    await self.save_message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        message=message,
        message_type=msg_type,
        media_url=media_url,
        thumbnail_url=thumbnail_url,
        metadata=metadata
    )

PASO 6: Modifica chat_payload para incluir los nuevos campos:
    chat_payload = {
        'type': 'chat_message',
        'message': message,
        'sender_id': sender_id,
        'sender_name': sender_name,
        'message_type': msg_type,
        'media_url': media_url,
        'thumbnail_url': thumbnail_url,
        'metadata': metadata,
    }

PASO 7: Modifica async def chat_message(self, event) para incluir los campos:
    await self.send(text_data=json.dumps({
        ...
        'message_type': event.get('message_type', 'text'),
        'media_url': event.get('media_url'),
        'thumbnail_url': event.get('thumbnail_url'),
        'metadata': event.get('metadata', {}),
    }))

PASO 8: Modifica @database_sync_to_async def save_message(...) para guardar los campos:
    ChatMessage.objects.create(
        sender=sender,
        recipient=recipient,
        message=message,
        message_type=message_type,
        media_url=media_url,
        thumbnail_url=thumbnail_url,
        metadata=metadata or {},
    )

✅ LISTO: El chat ahora soporta media sin romper mensajes de texto existentes
"""

