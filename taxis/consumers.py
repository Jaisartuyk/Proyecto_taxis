
import json
from channels.generic.websocket import AsyncWebsocketConsumer

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
