import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TaxiUpdateConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "taxi_updates"
        # Unir a un grupo específico para la actualización de los taxis
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Dejar el grupo cuando se desconecte
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Recibir mensaje desde WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        username = data['username']
        latitude = data['latitude']
        longitude = data['longitude']

        # Enviar mensaje a todos los miembros del grupo (en este caso, todos los administradores)
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'update_location',
                'message': {
                    'username': username,
                    'latitude': latitude,
                    'longitude': longitude
                }
            }
        )

    # Recibir mensaje desde el grupo
    async def update_location(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))



class RideConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        # Verificar si el usuario está autenticado y es conductor
        if user.is_authenticated and user.is_driver:
            self.group_name = "drivers"  # Solo para conductores
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()  # Rechazar conexiones de clientes normales

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def ride_update(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))



class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'audio_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            data = json.loads(text_data)

            if "audio" in data and "senderId" in data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_audio',
                        'audio': data["audio"],
                        'senderId': data["senderId"]
                    }
                )

            if "lat" in data and "lng" in data:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_location',
                        'lat': data["lat"],
                        'lng': data["lng"]
                    }
                )

    async def send_audio(self, event):
        await self.send(text_data=json.dumps({
            "audio": event["audio"],
            "senderId": event["senderId"]
        }))

    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            "lat": event["lat"],
            "lng": event["lng"]
        }))