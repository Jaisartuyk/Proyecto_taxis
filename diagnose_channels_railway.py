"""
Script de diagnóstico para verificar la configuración de channels en Railway
"""
import os
import sys

# Forzar que se use el settings de railway para el diagnóstico
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
os.environ['RAILWAY_ENVIRONMENT'] = 'true'  # Forzar modo railway

import django
django.setup()

from django.conf import settings
from channels.layers import get_channel_layer

def diagnose_channels():
    print("🔍 DIAGNÓSTICO DE CHANNELS EN RAILWAY")
    print("=" * 60)
    
    # 1. Verificar variables de entorno
    print("📋 Variables de entorno:")
    redis_url = os.environ.get('REDIS_URL', 'NO_CONFIGURADA')
    railway_env = os.environ.get('RAILWAY_ENVIRONMENT', 'NO_CONFIGURADA')
    print(f"   REDIS_URL: {redis_url}")
    print(f"   RAILWAY_ENVIRONMENT: {railway_env}")
    
    # 2. Verificar configuración de Django
    print("\n⚙️ Configuración Django CHANNEL_LAYERS:")
    try:
        channel_layers_config = getattr(settings, 'CHANNEL_LAYERS', None)
        if channel_layers_config:
            print(f"   Backend: {channel_layers_config['default']['BACKEND']}")
            print(f"   Config: {channel_layers_config['default']['CONFIG']}")
        else:
            print("   ❌ CHANNEL_LAYERS no está configurado")
    except Exception as e:
        print(f"   ❌ Error accediendo CHANNEL_LAYERS: {e}")
    
    # 3. Verificar dependencias
    print("\n📦 Verificar dependencias:")
    try:
        import channels
        print(f"   ✅ channels versión: {channels.__version__}")
    except ImportError as e:
        print(f"   ❌ channels no disponible: {e}")
    
    try:
        import channels_redis
        print(f"   ✅ channels_redis versión: {channels_redis.__version__}")
    except ImportError as e:
        print(f"   ❌ channels_redis no disponible: {e}")
    
    try:
        import redis
        print(f"   ✅ redis versión: {redis.__version__}")
    except ImportError as e:
        print(f"   ❌ redis no disponible: {e}")
    
    # 4. Probar conexión directa a Redis
    print("\n🔗 Prueba conexión directa a Redis:")
    try:
        import redis as redis_client
        if redis_url and redis_url != 'NO_CONFIGURADA':
            r = redis_client.from_url(redis_url)
            r.ping()
            print(f"   ✅ Conexión Redis exitosa")
        else:
            print(f"   ❌ Redis URL no disponible")
    except Exception as e:
        print(f"   ❌ Error conectando Redis: {e}")
    
    # 5. Probar channel layer
    print("\n📡 Prueba Channel Layer:")
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            print("   ❌ Channel layer es None")
        else:
            print(f"   ✅ Channel layer disponible: {type(channel_layer)}")
            
            # Probar operación básica
            try:
                # Test básico de channel layer
                import asyncio
                async def test_channel():
                    try:
                        # Crear un canal de prueba
                        channel = channel_layer.new_channel()
                        print(f"   ✅ Canal creado: {channel}")
                        return True
                    except Exception as e:
                        print(f"   ❌ Error creando canal: {e}")
                        return False
                
                # Ejecutar test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(test_channel())
                loop.close()
                
            except Exception as e:
                print(f"   ❌ Error probando channel layer: {e}")
                
    except Exception as e:
        print(f"   ❌ Error obteniendo channel layer: {e}")
    
    print("\n" + "=" * 60)
    
    # 6. Recomendaciones
    print("💡 RECOMENDACIONES:")
    if redis_url == 'NO_CONFIGURADA':
        print("   - Verificar que REDIS_URL esté configurado en Railway")
    elif 'channel_layer es None' in str(locals()):
        print("   - Problema con inicialización de channel layer")
        print("   - Verificar dependencias channels_redis")
    else:
        print("   - Configuración parece correcta, verificar logs de Railway")

if __name__ == "__main__":
    diagnose_channels()