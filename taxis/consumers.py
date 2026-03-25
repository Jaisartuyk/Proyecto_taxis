
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AudioConsumer(AsyncWebsocketConsumer):
    # Diccionario para rastrear quién está transmitiendo (por sala)
    active_transmissions = {}
    # Diccionario para mapear channel_name a user info
    user_info = {}
    
    async def connect(self):
        # La URL /ws/audio/conductores/ no tiene parámetros, usar valor fijo
        self.room_name = self.scope['url_route']['kwargs'].get('room_name', 'conductores')
        self.room_group_name = f'audio_{self.room_name}'
        
        # Obtener información del usuario de la sesión
        self.user = self.scope.get('user')
        self.driver_id = None
        self.driver_name = 'Usuario'
        
        if self.user and self.user.is_authenticated:
            self.driver_id = str(self.user.id)
            self.driver_name = self.user.username or f'Usuario {self.user.id}'
        
        # Guardar info del usuario
        AudioConsumer.user_info[self.channel_name] = {
            'driver_id': self.driver_id,
            'driver_name': self.driver_name
        }

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        print(f'✅ {self.driver_name} conectado a {self.room_name}')

    async def disconnect(self, close_code):
        # Si este usuario estaba transmitiendo, liberar la transmisión
        if self.room_group_name in AudioConsumer.active_transmissions:
            if AudioConsumer.active_transmissions[self.room_group_name] == self.channel_name:
                # Notificar a todos que terminó la transmisión
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'transmission_status',
                        'isTransmitting': False,
                        'speakerId': self.driver_id,
                        'speakerName': self.driver_name
                    }
                )
                del AudioConsumer.active_transmissions[self.room_group_name]
        
        # Limpiar info del usuario
        if self.channel_name in AudioConsumer.user_info:
            del AudioConsumer.user_info[self.channel_name]
        
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f'🔴 {self.driver_name} desconectado de {self.room_name}')

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            try:
                data = json.loads(text_data)
                msg_type = data.get('type')
                
                # INICIO DE TRANSMISIÓN
                if msg_type == 'transmission_start':
                    driver_id = data.get('driver_id', self.driver_id)
                    driver_name = data.get('driver_name', self.driver_name)
                    
                    # Verificar si alguien más está transmitiendo
                    if self.room_group_name in AudioConsumer.active_transmissions:
                        current_speaker = AudioConsumer.active_transmissions[self.room_group_name]
                        # Rechazar si no es el mismo usuario
                        if current_speaker != self.channel_name:
                            await self.send(text_data=json.dumps({
                                'type': 'error',
                                'message': 'Alguien más está transmitiendo'
                            }))
                            return
                    
                    # Registrar transmisión
                    AudioConsumer.active_transmissions[self.room_group_name] = self.channel_name
                    
                    # Broadcast a TODOS
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'transmission_status',
                            'isTransmitting': True,
                            'speakerId': driver_id,
                            'speakerName': driver_name
                        }
                    )
                    print(f'🎤 {driver_name} inició transmisión en {self.room_name}')
                
                # FIN DE TRANSMISIÓN
                elif msg_type == 'transmission_stop':
                    driver_id = data.get('driver_id', self.driver_id)
                    driver_name = data.get('driver_name', self.driver_name)
                    
                    # Liberar transmisión
                    if self.room_group_name in AudioConsumer.active_transmissions:
                        if AudioConsumer.active_transmissions[self.room_group_name] == self.channel_name:
                            del AudioConsumer.active_transmissions[self.room_group_name]
                    
                    # Broadcast a TODOS
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'transmission_status',
                            'isTransmitting': False,
                            'speakerId': driver_id,
                            'speakerName': driver_name
                        }
                    )
                    print(f'⏹️ {driver_name} terminó transmisión en {self.room_name}')
                
                # UBICACIÓN CON TYPE='location' (desde app Flutter)
                elif msg_type == 'location':
                    lat = data.get('latitude') or data.get('lat')
                    lng = data.get('longitude') or data.get('lng')
                    driver_id = data.get('driver_id', self.driver_id)
                    
                    print(f'📍 Ubicación (type=location) recibida: lat={lat}, lng={lng}, driver_id={driver_id}')
                    
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_location',
                            'lat': lat,
                            'lng': lng,
                            'driver_id': driver_id
                        }
                    )
                
                # AUDIO
                elif "audio" in data:
                    driver_id = data.get('driver_id', self.driver_id)
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_audio',
                            'audio': data["audio"],
                            'driver_id': driver_id,
                            'senderId': data.get("senderId", driver_id),
                            'sender_channel': self.channel_name,
                        }
                    )
                
                # UBICACIÓN SIN TYPE (legacy)
                elif "lat" in data and "lng" in data:
                    print(f'📍 Ubicación recibida: lat={data["lat"]}, lng={data["lng"]}, driver_id={data.get("driver_id", self.driver_id)}')
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'send_location',
                            'lat': data["lat"],
                            'lng': data["lng"],
                            'driver_id': data.get('driver_id', self.driver_id)
                        }
                    )
                
                # MENSAJE SIN TYPE (legacy o formato antiguo)
                else:
                    # Si no tiene type pero tiene lat/lng, es ubicación
                    if "lat" in data and "lng" in data:
                        print(f'📍 Ubicación (sin type) recibida: lat={data["lat"]}, lng={data["lng"]}')
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'send_location',
                                'lat': data["lat"],
                                'lng': data["lng"],
                                'driver_id': data.get('driver_id', self.driver_id)
                            }
                        )
                    # Si tiene audio, procesarlo
                    elif "audio" in data:
                        driver_id = data.get('driver_id', self.driver_id)
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'send_audio',
                                'audio': data["audio"],
                                'driver_id': driver_id,
                                'senderId': data.get("senderId", driver_id),
                                'sender_channel': self.channel_name,
                            }
                        )
                    
            except json.JSONDecodeError:
                print('❌ Error al decodificar JSON')
        
        # Manejar datos binarios (si la app envía ubicación como bytes)
        elif bytes_data:
            print(f'📦 Bytes recibidos: {len(bytes_data)} bytes')
            # Si son bytes de audio, reenviar
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_audio_bytes',
                    'audio_bytes': bytes_data
                }
            )

    async def transmission_status(self, event):
        """Enviar estado de transmisión a todos los clientes"""
        await self.send(text_data=json.dumps({
            'type': 'transmission_status',
            'isTransmitting': event['isTransmitting'],
            'speakerId': event['speakerId'],
            'speakerName': event['speakerName']
        }))
    
    async def send_audio(self, event):
        # No reenviar el audio al mismo canal que lo envió (evitar eco)
        if event.get('sender_channel') == self.channel_name:
            return
        await self.send(text_data=json.dumps({
            "type": "audio_broadcast",
            "audio": event["audio"],
            "driver_id": event.get("driver_id"),
            "senderId": event.get("senderId")
        }))

    async def send_location(self, event):
        await self.send(text_data=json.dumps({
            "type": "driver_location_update",
            "lat": event["lat"],
            "lng": event["lng"],
            "driver_id": event.get("driver_id")
        }))
    
    async def send_audio_bytes(self, event):
        """Enviar audio como bytes binarios"""
        await self.send(bytes_data=event['audio_bytes'])


class ChatConsumer(AsyncWebsocketConsumer):
    """Consumer para chat en tiempo real"""
    
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs'].get('user_id', 'web')
        self.room_group_name = f'chat_{self.user_id}'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f'✅ Chat conectado: {self.user_id}')
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f'🔴 Chat desconectado: {self.user_id}')
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type', 'chat_message')
        
        # Ignorar pings
        if msg_type in ('ping', 'pong'):
            return

        message = data.get('message', '')
        sender_id = str(data.get('sender_id', self.user_id))
        recipient_id = str(data.get('recipient_id', ''))
        
        print(f'💬 Mensaje de {sender_id} para {recipient_id}: {message[:50]}')

        payload = {
            'type': 'chat_message',
            'message': message,
            'sender_id': sender_id,
            'sender_name': data.get('sender_name', f'Conductor {sender_id}'),
            'recipient_id': recipient_id,
            'message_type': data.get('message_type', 'text'),
            'media_url': data.get('media_url', ''),
            'thumbnail_url': data.get('thumbnail_url', ''),
        }

        # 1. Enviar al grupo del remitente (para confirmar en su propia pantalla)
        await self.channel_layer.group_send(self.room_group_name, payload)

        # 2. Enviar al grupo del destinatario (para que lo reciba en su chat)
        if recipient_id and recipient_id != self.user_id:
            recipient_group = f'chat_{recipient_id}'
            await self.channel_layer.group_send(recipient_group, payload)
            print(f'📨 Mensaje reenviado al grupo del destinatario: {recipient_group}')
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event.get('message', ''),
            'sender_id': event.get('sender_id', ''),
            'sender_name': event.get('sender_name', ''),
            'recipient_id': event.get('recipient_id', ''),
            'message_type': event.get('message_type', 'text'),
            'media_url': event.get('media_url', ''),
            'thumbnail_url': event.get('thumbnail_url', ''),
        }))


class RidesConsumer(AsyncWebsocketConsumer):
    """Consumer para actualizaciones de carreras en tiempo real"""
    
    async def connect(self):
        self.room_group_name = 'rides_updates'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        print(f'✅ Rides conectado')
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f'🔴 Rides desconectado')
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Broadcast actualización de carrera
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'ride_update',
                'ride_id': data.get('ride_id'),
                'status': data.get('status'),
                'data': data.get('data', {})
            }
        )
    
    async def ride_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ride_update',
            'ride_id': event.get('ride_id'),
            'status': event.get('status'),
            'data': event.get('data', {})
        }))
