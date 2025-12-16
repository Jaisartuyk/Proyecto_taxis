from django.urls import re_path
from taxis.consumers import AudioConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/audio/conductores/$", AudioConsumer.as_asgi()),  # Ruta directa
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),  # Chat 1:1 (central/conductores)
]