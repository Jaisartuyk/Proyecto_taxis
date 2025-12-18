from django.urls import re_path
from taxis.consumers import AudioConsumer, ChatConsumer

websocket_urlpatterns = [
    re_path(r"ws/audio/conductores/$", AudioConsumer.as_asgi()),  # Audio + Ubicación
    re_path(r"ws/chat/(?P<user_id>\w+)/$", ChatConsumer.as_asgi()),  # Chat con user_id (Android)
    re_path(r"ws/chat/$", ChatConsumer.as_asgi()),  # Chat sin user_id (Web con sesión)
]