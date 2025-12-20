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
# Verificar múltiples formas de detectar Railway
railway_env = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY') or os.environ.get('PORT')
print(f"[ASGI] Detectando entorno: RAILWAY_ENVIRONMENT={os.environ.get('RAILWAY_ENVIRONMENT')}, RAILWAY={os.environ.get('RAILWAY')}, PORT={os.environ.get('PORT')}")

if railway_env or os.environ.get('DATABASE_URL', '').startswith('postgres'):
    # Si estamos en Railway o tenemos DATABASE_URL de PostgreSQL, usar settings_railway
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
    print(f"[ASGI] ✅ Usando settings_railway.py")
    # Forzar RAILWAY_ENVIRONMENT si no está configurado
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        os.environ['RAILWAY_ENVIRONMENT'] = 'true'
        print(f"[ASGI] ✅ RAILWAY_ENVIRONMENT configurado como 'true'")
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
    print(f"[ASGI] Usando settings.py (desarrollo local)")

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

