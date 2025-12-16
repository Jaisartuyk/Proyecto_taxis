from django.urls import re_path
from taxis.consumers import AudioConsumer

websocket_urlpatterns = [
    re_path(r"ws/audio/conductores/$", AudioConsumer.as_asgi()),  # Ruta directa
]