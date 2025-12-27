"""
ASGI config for taxi_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import sys

# CRÍTICO: Configurar DJANGO_SETTINGS_MODULE ANTES de importar cualquier cosa de Django
# Esto debe hacerse ANTES de get_asgi_application() para que Django use el settings correcto

# Verificar múltiples formas de detectar Railway
railway_env = os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('RAILWAY')
database_url = os.environ.get('DATABASE_URL', '')
port = os.environ.get('PORT')

print("\n" + "="*60)
print("[ASGI] Inicializando ASGI application...")
print("="*60)
print(f"[ASGI] Detectando entorno:")
print(f"  RAILWAY_ENVIRONMENT={os.environ.get('RAILWAY_ENVIRONMENT')}")
print(f"  RAILWAY={os.environ.get('RAILWAY')}")
print(f"  PORT={port}")
print(f"  DATABASE_URL empieza con 'postgres': {database_url.startswith('postgres')}")
print(f"  DJANGO_SETTINGS_MODULE actual: {os.environ.get('DJANGO_SETTINGS_MODULE', 'NO CONFIGURADO')}")

# Detectar Railway
is_railway = railway_env or database_url.startswith('postgres') or port

if is_railway:
    # Si estamos en Railway, usar settings_railway
    os.environ['DJANGO_SETTINGS_MODULE'] = 'taxi_project.settings_railway'
    if not os.environ.get('RAILWAY_ENVIRONMENT'):
        os.environ['RAILWAY_ENVIRONMENT'] = 'true'
    print(f"[ASGI] ✅ Detectado Railway - Configurando DJANGO_SETTINGS_MODULE=taxi_project.settings_railway")
    print(f"[ASGI] ✅ RAILWAY_ENVIRONMENT configurado como 'true'")
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
    print(f"[ASGI] Usando settings.py (desarrollo local)")

print(f"[ASGI] DJANGO_SETTINGS_MODULE final: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print("="*60 + "\n")

# Ahora importar Django después de configurar DJANGO_SETTINGS_MODULE
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from taxis.middleware import TokenAuthMiddlewareStack  # ✅ Middleware personalizado para tokens
import taxis.routing

# Initialize Django (esto cargará el settings configurado arriba)
print("[ASGI] Inicializando Django application...")
django_asgi_app = get_asgi_application()
print("[ASGI] ✅ Django application inicializado")

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": TokenAuthMiddlewareStack(  # ✅ Usar TokenAuthMiddlewareStack en lugar de AuthMiddlewareStack
        URLRouter(
            taxis.routing.websocket_urlpatterns  # Aquí enlazamos las rutas de WebSocket de 'gestion'
        )
    ),
})

