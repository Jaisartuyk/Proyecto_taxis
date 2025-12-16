import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'audio_{self.room_name}'
        
        # Extraer driver_id si está en el room_name (formato: conductor_123)
        if self.room_name.startswith('conductor_'):
            self.driver_id = self.room_name.replace('conductor_', '')
            print(f"👤 Conductor conectado: ID={self.driver_id}")
        else:
            self.driver_id = None
            print(f"🔌 Conexión sin ID de conductor: room={self.room_name}")

        # FORCE channel_layer initialization si es None
        if self.channel_layer is None:
            print(f"❌ ERROR: channel_layer es None en AudioConsumer")
            print(f"🔧 INTENTANDO forzar inicialización de channel_layer...")
            
            # DEBUG: Verificar configuración detallada
            try:
                from django.conf import settings
                print(f"🔍 DEBUG Settings module: {settings.SETTINGS_MODULE}")
                
                # Verificar si CHANNEL_LAYERS existe
                if hasattr(settings, 'CHANNEL_LAYERS'):
                    channel_config = getattr(settings, 'CHANNEL_LAYERS', None)
                    print(f"🔍 DEBUG CHANNEL_LAYERS: {channel_config}")
                else:
                    print(f"❌ DEBUG: CHANNEL_LAYERS NO EXISTE en settings")
                
                # Forzar obtención del channel layer
                self.channel_layer = get_channel_layer()
                print(f"🔍 DEBUG get_channel_layer() result: {self.channel_layer}")
                
                if self.channel_layer is not None:
                    print(f"✅ Channel layer forzado exitosamente: {type(self.channel_layer)}")
                else:
                    print(f"❌ get_channel_layer() devolvió None")
                    # Intentar creación manual
                    from channels.layers import InMemoryChannelLayer
                    self.channel_layer = InMemoryChannelLayer()
                    print(f"🔧 EMERGENCY: Creado InMemoryChannelLayer manual")
                    
            except Exception as e:
                print(f"❌ Error forzando channel_layer: {e}")
                # EMERGENCY: Crear channel layer manual
                try:
                    from channels.layers import InMemoryChannelLayer
                    self.channel_layer = InMemoryChannelLayer()
                    print(f"🚨 EMERGENCY FALLBACK: InMemoryChannelLayer creado manualmente")
                except Exception as e2:
                    print(f"💀 FATAL: No se pudo crear ningún channel_layer: {e2}")
                    await self.close()
                    return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado al grupo: {self.room_group_name}")

    @database_sync_to_async
    def send_audio_push_to_drivers(self, sender_id):
        """Send push notification to all drivers when admin sends audio"""
        from taxis.push_notifications import send_push_to_all_drivers
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            sender = User.objects.get(id=sender_id)
            sender_name = sender.get_full_name() or "Central"
            
            # Datos específicos para audio walkie-talkie
            audio_data = {
                "type": "walkie_talkie_audio",
                "sender_id": str(sender_id),
                "sender_name": sender_name,
                "timestamp": int(__import__('time').time() * 1000),
                "urgent": True,
                "requires_immediate_attention": True,
                "sound": "walkie_talkie",
                "vibrate": [200, 100, 200],
                "action": "open_audio_channel"
            }
            
            # Notificación tipo walkie-talkie
            send_push_to_all_drivers(
                title=f"📻 {sender_name}",
                body="🎤 Mensaje de audio - Toca para escuchar",
                data=audio_data
            )
            print(f"📻 Push de audio walkie-talkie enviado por {sender_name}")
        except Exception as e:
            print(f"Error sending walkie-talkie push notification: {e}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name') and self.channel_layer is not None:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"WebSocket desconectado del grupo: {self.room_group_name} con código: {close_code}")
        else:
            print(f"WebSocket desconectado (sin channel_layer): código {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            message_type = data.get('type')

            print(f"Mensaje recibido en {self.room_group_name}: {data}")

            # --- Mensajes de CHAT ---
            if message_type == 'chat_message':
                driver_id = data.get('driver_id')
                message = data.get('message')
                sender = data.get('sender', 'central')

                if driver_id and message:
                    # Enviar mensaje a todos en el grupo para que lo vean en tiempo real
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_chat_to_clients',
                            'driver_id': driver_id,
                            'message': message,
                            'sender': sender,
                            'timestamp': data.get('timestamp'),
                            'sender_channel': self.channel_name,
                        }
                    )
                    print(f"💬 Mensaje de chat de {sender} para conductor {driver_id}: {message}")

            # --- Mensajes desde los taxis ---
            elif message_type == 'location_update':
                sender_id = data.get('senderId')
                latitude = data.get('latitude')
                longitude = data.get('longitude')

                if sender_id and latitude is not None and longitude is not None:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_location_to_clients',
                            'driverId': sender_id,
                            'latitude': latitude,
                            'longitude': longitude,
                        }
                    )
                    print(f"📍 Ubicación de {sender_id} retransmitida.")

            elif message_type == 'audio_message':
                # Usar driver_id de la conexión si está disponible, sino usar el del mensaje
                sender_id = getattr(self, 'driver_id', None) or data.get('senderId')
                audio_data_base64 = data.get('audio')

                if sender_id and audio_data_base64:
                    # Debug: Ver cuántos miembros hay en el grupo
                    print(f"📊 Grupo: {self.room_group_name}, Enviando audio de conductor {sender_id}")
                    
                    # 🚫 NO enviar el audio de vuelta al mismo conductor
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_audio_to_clients',
                            'senderId': sender_id,
                            'senderRole': 'Taxi',
                            'audio': audio_data_base64,
                            'sender_channel': self.channel_name,  # 🔑 Canal del remitente
                        }
                    )
                    print(f"🎤 Audio de conductor {sender_id} retransmitido. Canal: {self.channel_name}")

            # --- Mensajes desde la central ---
            elif message_type == 'central_audio_message' or message_type == 'central_audio':
                audio_data_base64 = data.get('audio_data') or data.get('audio')
                
                # Obtener ID real del usuario autenticado
                sender_id = getattr(self.scope.get('user'), 'id', None)
                if not sender_id:
                    # Fallback si no hay usuario autenticado
                    sender_id = data.get('senderId', 1)  # Usar ID 1 como fallback
                    print(f"⚠️ Usuario no autenticado, usando sender_id fallback: {sender_id}")
                
                sender_role = data.get('senderRole', 'Central')

                if audio_data_base64:
                    # 🚫 NO enviar el audio de vuelta a la central
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_audio_to_clients',
                            'senderId': sender_id,
                            'senderRole': sender_role,
                            'audio': audio_data_base64,
                            'sender_channel': self.channel_name,  # 🔑 Canal del remitente
                        }
                    )
                    print(f"🔊 Audio de la {sender_role} (ID: {sender_id}) retransmitido. Canal remitente: {self.channel_name}")
                    
                    # Enviar notificación push a todos los conductores
                    await self.send_audio_push_to_drivers(sender_id)
                else:
                    print(f"⚠️ Mensaje de audio incompleto recibido desde la web: {data}")

    async def send_location_to_clients(self, event):
        await self.send(text_data=json.dumps({
            "type": "driver_location_update",
            "driverId": event['driverId'],
            "latitude": event['latitude'],
            "longitude": event['longitude'],
        }))

    async def send_chat_to_clients(self, event):
        # Enviar mensaje de chat a todos los clientes
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "driver_id": event['driver_id'],
            "message": event['message'],
            "sender": event['sender'],
            "timestamp": event.get('timestamp'),
        }))
        print(f"💬 Mensaje de chat enviado a cliente: {event['message']}")

    async def send_audio_to_clients(self, event):
        # 🚫 NO enviar el audio de vuelta al remitente
        sender_channel = event.get('sender_channel')
        sender_id = event.get('senderId')
        
        print(f"🔍 send_audio_to_clients llamado en canal: {self.channel_name}")
        print(f"   Remitente: {sender_id}, Canal remitente: {sender_channel}")
        
        if sender_channel and sender_channel == self.channel_name:
            print(f"🔇 Audio NO enviado al remitente (canal: {self.channel_name})")
            return  # NO ENVIAR
        
        # Enviar a todos los demás
        await self.send(text_data=json.dumps({
            "type": "audio_broadcast",
            "senderId": event["senderId"],
            "senderRole": event.get("senderRole", "Desconocido"),
            "audio": event["audio"],
        }))
        print(f"✅ Audio enviado a canal: {self.channel_name} (tipo: audio_broadcast)")


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        # FORCE channel_layer initialization si es None
        if self.channel_layer is None:
            print(f"❌ ERROR: channel_layer es None en ChatConsumer")
            print(f"🔧 INTENTANDO forzar inicialización de channel_layer...")
            
            # DEBUG: Verificar configuración detallada
            try:
                from django.conf import settings
                print(f"🔍 DEBUG Settings module: {settings.SETTINGS_MODULE}")
                
                # Verificar si CHANNEL_LAYERS existe
                if hasattr(settings, 'CHANNEL_LAYERS'):
                    channel_config = getattr(settings, 'CHANNEL_LAYERS', None)
                    print(f"🔍 DEBUG CHANNEL_LAYERS: {channel_config}")
                else:
                    print(f"❌ DEBUG: CHANNEL_LAYERS NO EXISTE en settings")
                
                # Forzar obtención del channel layer
                self.channel_layer = get_channel_layer()
                print(f"🔍 DEBUG get_channel_layer() result: {self.channel_layer}")
                
                if self.channel_layer is not None:
                    print(f"✅ Channel layer forzado exitosamente: {type(self.channel_layer)}")
                else:
                    print(f"❌ get_channel_layer() devolvió None")
                    # Intentar creación manual
                    from channels.layers import InMemoryChannelLayer
                    self.channel_layer = InMemoryChannelLayer()
                    print(f"🔧 EMERGENCY: Creado InMemoryChannelLayer manual")
                    
            except Exception as e:
                print(f"❌ Error forzando channel_layer: {e}")
                # EMERGENCY: Crear channel layer manual
                try:
                    from channels.layers import InMemoryChannelLayer
                    self.channel_layer = InMemoryChannelLayer()
                    print(f"🚨 EMERGENCY FALLBACK: InMemoryChannelLayer creado manualmente")
                except Exception as e2:
                    print(f"💀 FATAL: No se pudo crear ningún channel_layer: {e2}")
                    await self.close()
                    return

        self.room_group_name = f'chat_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Usuario {self.user.username} conectado al grupo de chat {self.room_group_name}")

    async def disconnect(self, close_code):
        if self.user.is_authenticated and hasattr(self, 'room_group_name') and self.channel_layer is not None:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"Usuario {self.user.username} desconectado del grupo de chat {self.room_group_name}")
        else:
            print(f"Usuario desconectado (sin channel_layer): código {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        recipient_id = data.get('recipient_id')

        if not message or not recipient_id:
            print("Error: Faltan datos en el mensaje de chat")
            return

        # Guardar mensaje en la base de datos
        await self.save_message(self.user.id, recipient_id, message)

        # Grupo del destinatario
        recipient_group_name = f'chat_{recipient_id}'

        # Preparar el payload del mensaje
        chat_payload = {
            'type': 'chat_message',
            'message': message,
            'sender_id': self.user.id,
            'sender_name': self.user.get_full_name(),
        }

        # Enviar mensaje al destinatario
        await self.channel_layer.group_send(recipient_group_name, chat_payload)
        print(f"Mensaje de {self.user.id} enviado a {recipient_id}")
        
        # Enviar notificación push
        await self.send_chat_push_notification(self.user.id, recipient_id, message)

        # Enviar mensaje de vuelta al remitente para actualizar su UI
        await self.channel_layer.group_send(self.room_group_name, chat_payload)

    async def chat_message(self, event):
        # Obtener el conteo de badge actualizado
        badge_count = await self.get_badge_count(self.user.id)
        
        # Enviar el mensaje al cliente WebSocket con el conteo de badge
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'badge_count': badge_count,  # Agregar conteo de badge
            'update_badge': True
        }))

    @database_sync_to_async
    def save_message(self, sender_id, recipient_id, message):
        from .models import ChatMessage, AppUser
        try:
            sender = AppUser.objects.get(id=sender_id)
            recipient = AppUser.objects.get(id=recipient_id)
            ChatMessage.objects.create(sender=sender, recipient=recipient, message=message)
            print(f"Mensaje guardado en BD: {sender} -> {recipient}")
        except Exception as e:
            print(f"Error al guardar mensaje: {e}")
    
    @database_sync_to_async
    def get_badge_count(self, user_id):
        """Obtener el conteo de badge para un usuario"""
        from .models import AppUser, Ride, ChatMessage
        from django.db.models import Q
        
        try:
            user = AppUser.objects.get(id=user_id)
            rides_count = 0
            messages_count = 0
            
            if user.role == 'driver':
                rides_count = Ride.objects.filter(
                    Q(driver=user, status='pending') | 
                    Q(driver=user, status='accepted') |
                    Q(driver=user, status='in_progress')
                ).count()
                messages_count = ChatMessage.objects.filter(
                    recipient=user, is_read=False
                ).count()
            elif user.role == 'customer':
                rides_count = Ride.objects.filter(
                    customer=user,
                    status__in=['pending', 'accepted', 'in_progress']
                ).count()
                messages_count = ChatMessage.objects.filter(
                    recipient=user, is_read=False
                ).count()
            elif user.role == 'admin':
                rides_count = Ride.objects.filter(
                    status='pending', driver__isnull=True
                ).count()
                messages_count = ChatMessage.objects.filter(
                    recipient=user, is_read=False
                ).count()
            
            return rides_count + messages_count
        except Exception as e:
            print(f"Error al obtener badge count: {e}")
            return 0
    
    @database_sync_to_async
    def send_chat_push_notification(self, sender_id, recipient_id, message):
        """Enviar notificación push cuando llega un mensaje de chat"""
        from .models import AppUser
        from .push_notifications import send_chat_message_notification
        try:
            sender = AppUser.objects.get(id=sender_id)
            recipient = AppUser.objects.get(id=recipient_id)
            
            # Enviar notificación push
            send_chat_message_notification(sender, recipient, message)
            print(f"📱 Notificación push enviada: {sender.username} -> {recipient.username}")
        except Exception as e:
            print(f"❌ Error al enviar notificación push: {e}")
