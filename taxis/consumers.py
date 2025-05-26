
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # La 'room_name' debe ser la misma para todos los clientes (Android y Web)
        # para que se comuniquen en el mismo "canal de radio".
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'audio_{self.room_name}'

        # Todos los clientes (central, taxis) se unen a este grupo general.
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f"WebSocket conectado al grupo: {self.room_group_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"WebSocket desconectado del grupo: {self.room_group_name} con código: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Este método recibe mensajes de CUALQUIER cliente conectado:
        - Ubicación y audio desde la app Android (taxis).
        - Audio desde la app web (central).
        """
        if text_data:
            data = json.loads(text_data)
            # Usamos el campo 'type' para diferenciar los mensajes
            message_type = data.get('type')

            print(f"Mensaje recibido en {self.room_group_name}: {data}")

            # --- Mensajes entrantes desde la app Android (Taxis) ---
            if message_type == 'location_update':
                sender_id = data.get('senderId')
                latitude = data.get('latitude')
                longitude = data.get('longitude')

                if sender_id and latitude is not None and longitude is not None:
                    await self.channel_layer.group_send(
                        self.room_group_name, # Retransmitir a TODOS en el grupo (incluida la web)
                        {
                            'type': 'send_location_to_clients', # Método para manejar en los receptores
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
                        self.room_group_name, # Retransmitir a TODOS en el grupo (web y otros taxis)
                        {
                            'type': 'send_audio_to_clients', # Método para manejar en los receptores
                            'senderId': sender_id,
                            'audio': audio_data_base64,
                        }
                    )
                    print(f"🎤 Audio de {sender_id} retransmitido.")

            # --- NUEVO: Mensajes de Audio entrantes desde la app web (Central) ---
            elif message_type == 'central_audio_message': # Nuevo tipo para audio desde la web
                audio_data_base64 = data.get('audio')
                sender_role = data.get('senderRole', 'Central') # Por defecto 'Central'

                if audio_data_base64:
                    await self.channel_layer.group_send(
                        self.room_group_name, # Retransmitir a TODOS (todos los taxis y otras centrales)
                        {
                            'type': 'send_audio_to_clients', # Reutilizamos este método para que lo reciban todos
                            'senderId': sender_role, # El ID del emisor será 'Central'
                            'audio': audio_data_base64,
                        }
                    )
                    print(f"🔊 Audio de la {sender_role} retransmitido a los taxis.")
                else:
                    print(f"⚠️ Mensaje de audio incompleto recibido desde la web: {data}")

    # --- Métodos que el channel layer llamará para enviar mensajes a los CLIENTES (Android y Web) ---

    async def send_location_to_clients(self, event):
        """
        Envía una actualización de ubicación a los clientes (actualmente solo la web).
        """
        await self.send(text_data=json.dumps({
            "type": "driver_location_update", # Tipo que la app web reconocerá
            "driverId": event['driverId'],
            "latitude": event['latitude'],
            "longitude": event['longitude'],
        }))

    async def send_audio_to_clients(self, event):
        """
        Envía un mensaje de audio a todos los clientes (web y Android).
        """
        await self.send(text_data=json.dumps({
            "type": "audio_broadcast", # Un tipo genérico para audio (lo escucharán taxis y central)
            "senderId": event["senderId"],
            "audio": event["audio"],
        }))