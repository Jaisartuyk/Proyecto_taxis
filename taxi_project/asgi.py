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

# Asegurar que Railway use settings_railway.py
if os.environ.get('RAILWAY_ENVIRONMENT'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

# Initialize Django
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            taxis.routing.websocket_urlpatterns  # Aquí enlazamos las rutas de WebSocket de 'gestion'
        )
    ),
})

