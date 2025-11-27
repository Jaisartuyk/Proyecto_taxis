import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'audio_{self.room_name}'

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
            send_push_to_all_drivers(
                title=f"🎤 Mensaje de Audio de {sender_name}",
                body="Toca para escuchar",
                data={"type": "audio_message", "sender_id": str(sender_id)}
            )
        except Exception as e:
            print(f"Error sending push notification: {e}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"WebSocket desconectado del grupo: {self.room_group_name} con código: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)
            message_type = data.get('type')

            print(f"Mensaje recibido en {self.room_group_name}: {data}")

            # --- Mensajes desde los taxis ---
            if message_type == 'location_update':
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
                sender_id = data.get('senderId')
                audio_data_base64 = data.get('audio')

                if sender_id and audio_data_base64:
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
                    print(f"🎤 Audio de {sender_id} retransmitido (Taxi). Canal remitente: {self.channel_name}")

            # --- Mensajes desde la central ---
            elif message_type == 'central_audio_message':
                audio_data_base64 = data.get('audio')
                sender_id = data.get('senderId', 'Central')  # ID real del admin
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

    async def send_audio_to_clients(self, event):
        # 🚫 NO enviar el audio de vuelta al remitente
        sender_channel = event.get('sender_channel')
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
        print(f"✅ Audio enviado a canal: {self.channel_name}")


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group_name = f'chat_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"Usuario {self.user.username} conectado al grupo de chat {self.room_group_name}")

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"Usuario {self.user.username} desconectado del grupo de chat {self.room_group_name}")

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
        # Enviar el mensaje al cliente WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
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
