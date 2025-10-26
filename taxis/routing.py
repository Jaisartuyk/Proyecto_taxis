from django.urls import re_path
from taxis.consumers import AudioConsumer, ChatConsumer


websocket_urlpatterns = [

    re_path(r"ws/audio/(?P<room_name>\w+)/$", AudioConsumer.as_asgi()),  # Ruta para WebSocket de audio
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),  # Ruta para WebSocket de chat privado
]