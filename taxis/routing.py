from django.urls import re_path
from taxis.consumers import AudioConsumer


websocket_urlpatterns = [

    re_path(r"ws/audio/(?P<room_name>\w+)/$", AudioConsumer.as_asgi()),  # Ruta para WebSocket
]