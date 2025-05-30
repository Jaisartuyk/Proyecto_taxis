import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'audio_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado al grupo: {self.room_group_name}")

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
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_audio_to_clients',
                            'senderId': sender_id,
                            'senderRole': 'Taxi',  # 👈 Añadido explícitamente
                            'audio': audio_data_base64,
                        }
                    )
                    print(f"🎤 Audio de {sender_id} retransmitido (Taxi).")

            # --- Mensajes desde la central ---
            elif message_type == 'central_audio_message':
                audio_data_base64 = data.get('audio')
                sender_role = data.get('senderRole', 'Central')

                if audio_data_base64:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_audio_to_clients',
                            'senderId': sender_role,
                            'senderRole': sender_role,  # 👈 También incluido
                            'audio': audio_data_base64,
                        }
                    )
                    print(f"🔊 Audio de la {sender_role} retransmitido a los taxis.")
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
        await self.send(text_data=json.dumps({
            "type": "audio_broadcast",
            "senderId": event["senderId"],
            "senderRole": event.get("senderRole", "Desconocido"),  # 👈 Incluido en el mensaje enviado
            "audio": event["audio"],
        }))
