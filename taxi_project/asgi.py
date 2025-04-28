"""
ASGI config for taxi_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import taxis.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            taxis.routing.websocket_urlpatterns  # Aquí enlazamos las rutas de WebSocket de 'gestion'
        )
    ),
})

