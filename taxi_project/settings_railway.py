"""
Configuración específica para Railway con PostgreSQL y Redis
"""
from .settings import *
import os
import dj_database_url
import cloudinary

# Configuración de Railway
RAILWAY_ENVIRONMENT = os.environ.get('RAILWAY_ENVIRONMENT', False)

if RAILWAY_ENVIRONMENT:
    # Configuración de seguridad para producción
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    # Hosts permitidos para Railway
    ALLOWED_HOSTS = [
        'taxis-deaquipalla.up.railway.app',
        'taxis-django-channels-production.up.railway.app',
        '*.up.railway.app',  # Para subdominios de Railway
        'localhost',
        '127.0.0.1',
    ]
    
    # Base de datos PostgreSQL en Railway
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            conn_health_checks=True,
            default=os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3')
        )
    }
    
    # Configuración de Redis en Railway
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # Configuración de Cloudinary en Railway (desde variables de entorno)
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY', ''),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET', ''),
    }
    
    # Configurar Cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
        api_key=CLOUDINARY_STORAGE['API_KEY'],
        api_secret=CLOUDINARY_STORAGE['API_SECRET']
    )
    
    # Usar Cloudinary para almacenamiento de medios en producción
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    
    # Channels configuration - Redis optimizado para mejor rendimiento
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                # Configuración optimizada para Railway
                "capacity": 2000,        # Más capacidad para mensajes
                "expiry": 300,           # TTL de 5 minutos (más tiempo)
                "group_expiry": 3600,    # Grupos activos por 1 hora
                "channel_capacity": 500, # Capacidad por canal
                "asymmetric_expiry": 60, # Mensajes asimétricos por 1 minuto
            },
        },
    }
    
    # Debug: Confirmar configuración optimizada
    print(f"🔧 [RAILWAY] Channel Layer optimizado: {CHANNEL_LAYERS['default']['BACKEND']}")
    print(f"🔗 [RAILWAY] Redis: {REDIS_URL}")
    print(f"⚡ [RAILWAY] Capacidad: {CHANNEL_LAYERS['default']['CONFIG']['capacity']}")
    
    # Configuración de Push Notifications (NO afecta comunicación WebSocket)
    try:
        # Solo configurar si las variables VAPID están disponibles
        VAPID_PUBLIC = os.environ.get('VAPID_PUBLIC_KEY', '')
        VAPID_PRIVATE = os.environ.get('VAPID_PRIVATE_KEY', '')
        VAPID_EMAIL = os.environ.get('VAPID_ADMIN_EMAIL', 'admin@deaquipalla.com')
        
        if VAPID_PUBLIC and VAPID_PRIVATE:
            # Las claves en Railway están en formato base64 URL-safe, convertir a PEM
            import base64
            
            # Función helper para convertir base64 URL-safe a PEM
            def base64_to_pem(key_data, key_type):
                try:
                    # Agregar padding si es necesario
                    missing_padding = len(key_data) % 4
                    if missing_padding:
                        key_data += '=' * (4 - missing_padding)
                    
                    # Reemplazar caracteres URL-safe
                    key_data = key_data.replace('-', '+').replace('_', '/')
                    
                    # Decodificar base64
                    decoded = base64.b64decode(key_data)
                    
                    # Crear formato PEM
                    b64_encoded = base64.b64encode(decoded).decode('ascii')
                    
                    # Dividir en líneas de 64 caracteres
                    lines = [b64_encoded[i:i+64] for i in range(0, len(b64_encoded), 64)]
                    
                    return f"-----BEGIN {key_type} KEY-----\n" + '\n'.join(lines) + f"\n-----END {key_type} KEY-----"
                except Exception as e:
                    print(f"⚠️ Error convirtiendo clave {key_type}: {e}")
                    return None
            
            # Convertir claves
            public_pem = base64_to_pem(VAPID_PUBLIC, 'PUBLIC')
            private_pem = base64_to_pem(VAPID_PRIVATE, 'PRIVATE')
            
            if public_pem and private_pem:
                WEBPUSH_SETTINGS = {
                    "VAPID_PUBLIC_KEY": public_pem,
                    "VAPID_PRIVATE_KEY": private_pem,
                    "VAPID_ADMIN_EMAIL": VAPID_EMAIL
                }
                
                # También agregar como variables directas para compatibilidad
                globals()['VAPID_PUBLIC_KEY'] = public_pem
                globals()['VAPID_PRIVATE_KEY'] = private_pem
                globals()['VAPID_ADMIN_EMAIL'] = VAPID_EMAIL
                
                print(f"🔔 [RAILWAY] Push notifications configuradas con VAPID convertidas")
            else:
                # Fallback: usar claves como están
                WEBPUSH_SETTINGS = {
                    "VAPID_PUBLIC_KEY": VAPID_PUBLIC,
                    "VAPID_PRIVATE_KEY": VAPID_PRIVATE,
                    "VAPID_ADMIN_EMAIL": VAPID_EMAIL
                }
                
                # También agregar como variables directas para compatibilidad
                globals()['VAPID_PUBLIC_KEY'] = VAPID_PUBLIC
                globals()['VAPID_PRIVATE_KEY'] = VAPID_PRIVATE
                globals()['VAPID_ADMIN_EMAIL'] = VAPID_EMAIL
                
                print(f"🔔 [RAILWAY] Push notifications configuradas con VAPID raw")
        else:
            # Configuración por defecto (no afecta funcionamiento)
            WEBPUSH_SETTINGS = {
                "VAPID_PUBLIC_KEY": '',
                "VAPID_PRIVATE_KEY": '',
                "VAPID_ADMIN_EMAIL": 'admin@deaquipalla.com'
            }
            print(f"⚠️  [RAILWAY] Push notifications sin VAPID (opcional)")
    except Exception as e:
        print(f"⚠️  [RAILWAY] Error configurando push notifications: {e}")
        # Fallback seguro
        WEBPUSH_SETTINGS = {
            "VAPID_PUBLIC_KEY": '',
            "VAPID_PRIVATE_KEY": '',
            "VAPID_ADMIN_EMAIL": 'admin@deaquipalla.com'
        }
    
    # Configuración original de Redis restaurada
    print(f"🔧 [RAILWAY] Channel Layer: Redis")
    print(f"🔗 [RAILWAY] Redis URL: {REDIS_URL}")
    
    # Verificar que WhiteNoise esté en el middleware
    # El orden actual en settings.py es correcto (después de SecurityMiddleware)
    print("\n[MIDDLEWARE] Configurando middleware...")
    print(f"[MIDDLEWARE] MIDDLEWARE actual (primeros 5): {MIDDLEWARE[:5]}")
    
    if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
        # Si WhiteNoise no está en el middleware, agregarlo
        MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
        print("[WHITENOISE] WhiteNoiseMiddleware agregado al MIDDLEWARE")
    else:
        print("[WHITENOISE] WhiteNoiseMiddleware ya está en MIDDLEWARE")
        # Verificar posición
        whitenoise_index = MIDDLEWARE.index('whitenoise.middleware.WhiteNoiseMiddleware')
        print(f"[WHITENOISE] WhiteNoiseMiddleware está en posición {whitenoise_index} del MIDDLEWARE")
    
    # Agregar middleware de fallback ANTES de WhiteNoise
    # Este middleware servirá archivos estáticos directamente si existen
    # Debe estar ANTES de WhiteNoise para interceptar las peticiones primero
    print("[FALLBACK] Intentando agregar StaticFilesFallbackMiddleware...")
    fallback_middleware = 'taxi_project.middleware.StaticFilesFallbackMiddleware'
    if fallback_middleware not in MIDDLEWARE:
        # Encontrar la posición de WhiteNoise y agregar el fallback ANTES
        try:
            whitenoise_index = MIDDLEWARE.index('whitenoise.middleware.WhiteNoiseMiddleware')
            MIDDLEWARE.insert(whitenoise_index, fallback_middleware)
            print(f"[FALLBACK] ✅ StaticFilesFallbackMiddleware agregado ANTES de WhiteNoiseMiddleware en posición {whitenoise_index}")
        except ValueError as e:
            # Si WhiteNoise no está, agregar el fallback después de SecurityMiddleware
            MIDDLEWARE.insert(1, fallback_middleware)
            print(f"[FALLBACK] ✅ StaticFilesFallbackMiddleware agregado al MIDDLEWARE en posición 1 (WhiteNoise no encontrado: {e})")
    else:
        fallback_index = MIDDLEWARE.index(fallback_middleware)
        print(f"[FALLBACK] StaticFilesFallbackMiddleware ya está en MIDDLEWARE en posición {fallback_index}")
    
    # Debug: Mostrar el orden del middleware
    print(f"\n[MIDDLEWARE] Orden del middleware (solo relevantes):")
    for i, middleware in enumerate(MIDDLEWARE):
        if 'whitenoise' in middleware.lower() or 'staticfilesfallback' in middleware.lower() or 'security' in middleware.lower():
            print(f"  {i}: {middleware}")
    
    # Configuración de seguridad SSL para Railway
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Configuración de archivos estáticos para Railway
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    # IMPORTANTE: NO incluir taxis/static en STATICFILES_DIRS porque AppDirectoriesFinder
    # ya lo encuentra automáticamente (taxis es una app instalada)
    # Si lo incluimos en STATICFILES_DIRS, causa duplicados y "0 static files copied"
    # Redefinir explícitamente para sobrescribir el valor importado de settings.py
    STATICFILES_DIRS = []  # Vacío - AppDirectoriesFinder encontrará automáticamente los archivos en taxis/static
    # Usar solo AppDirectoriesFinder para evitar duplicados
    # AppDirectoriesFinder busca automáticamente en static/ de todas las apps instaladas
    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',  # Solo AppDirectoriesFinder
    ]
    # Usar storage simple - WhiteNoise comprimirá automáticamente al servir
    # Esto evita problemas con archivos copiados manualmente
    # Cloudinary maneja sus propios archivos estáticos y no necesitan estar en staticfiles/
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    
    # Configuración de WhiteNoise
    # IMPORTANTE: WhiteNoise sirve archivos desde STATIC_ROOT automáticamente
    # Configurar para que funcione correctamente con archivos copiados manualmente
    import os
    # Configurar WHITENOISE_ROOT explícitamente para asegurar que apunte al directorio correcto
    WHITENOISE_ROOT = STATIC_ROOT  # Configurar explícitamente el directorio raíz
    WHITENOISE_USE_FINDERS = True  # Habilitar finders como fallback adicional
    WHITENOISE_AUTOREFRESH = True  # Habilitar auto-refresh para detectar archivos nuevos
    WHITENOISE_INDEX_FILE = False  # No usar index.html automático
    WHITENOISE_MANIFEST_STRICT = False  # No ser estricto con el manifest
    
    # WhiteNoise servirá archivos desde STATIC_ROOT (configurado explícitamente)
    # Los archivos copiados manualmente en pre-deploy estarán disponibles
    # WhiteNoise comprimirá automáticamente al servir (no necesita pre-compresión)
    
    # Debug: Verificar configuración al iniciar
    print(f"\n[WHITENOISE] Configuración:")
    print(f"  STATIC_ROOT: {STATIC_ROOT}")
    print(f"  STATIC_URL: {STATIC_URL}")
    print(f"  WHITENOISE_ROOT: {WHITENOISE_ROOT}")
    print(f"  WHITENOISE_USE_FINDERS: {WHITENOISE_USE_FINDERS}")
    print(f"  WHITENOISE_AUTOREFRESH: {WHITENOISE_AUTOREFRESH}")
    
    # Verificar que STATIC_ROOT existe y tiene archivos
    if os.path.exists(STATIC_ROOT):
        file_count = sum([len(files) for r, d, files in os.walk(STATIC_ROOT)])
        print(f"  Archivos en STATIC_ROOT: {file_count}")
        
        # Verificar archivos críticos
        critical_files = ['css/floating-audio-button.css', 'js/audio-floating-button.js']
        for file_path in critical_files:
            full_path = os.path.join(STATIC_ROOT, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"  [OK] {file_path} - {size} bytes")
            else:
                print(f"  [ERROR] {file_path} NO existe en {full_path}")
    else:
        print(f"  [ERROR] STATIC_ROOT no existe: {STATIC_ROOT}")
    
    # Verificar que WHITENOISE_ROOT existe
    if os.path.exists(WHITENOISE_ROOT):
        print(f"  [OK] WHITENOISE_ROOT existe: {WHITENOISE_ROOT}")
    else:
        print(f"  [ERROR] WHITENOISE_ROOT no existe: {WHITENOISE_ROOT}")
    
    # Excluir archivos de Cloudinary del finder de staticfiles
    # Cloudinary sirve sus propios archivos estáticos desde su CDN, no necesitan estar en staticfiles/
    # NOTA: STATICFILES_FINDERS ya está definido arriba (línea 183) con solo AppDirectoriesFinder
    # No sobrescribir aquí para evitar duplicados
    
    # Configuración de logging para Railway
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'ignore_static_404': {
                '()': 'django.utils.log.CallbackFilter',
                'callback': lambda record: not (
                    record.levelname == 'WARNING' and 
                    'Not Found:' in record.getMessage() and
                    any(path in record.getMessage() for path in [
                        '/static/js/main.js',
                        '/static/css/styles.css',
                        '/offline.html',
                        '/static/imagenes/default.jpg'
                    ])
                )
            },
        },
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
                'filters': ['ignore_static_404'],
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
            'taxis': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    
    # Configuración de CORS para Railway
    CORS_ALLOWED_ORIGINS = [
        'https://taxis-deaquipalla.up.railway.app',
        'https://taxis-django-channels-production.up.railway.app',
    ]
    
    # Configuración de CSRF para Railway
    CSRF_TRUSTED_ORIGINS = [
        'https://taxis-deaquipalla.up.railway.app',
        'https://taxis-django-channels-production.up.railway.app',
    ]
    
    # Configuración de WhatsApp para Railway
    WASENDER_API_URL = os.environ.get('WASENDER_API_URL', 'https://wasenderapi.com/api/send-message')
    WASENDER_TOKEN = os.environ.get('WASENDER_TOKEN', '')
    
    # Configuración de Google Maps para Railway
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
    # Alias usado por el endpoint /api/maps-key/
    GOOGLE_MAPS_API_KEY = GOOGLE_API_KEY
    
    # Configuración de Telegram para Railway
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID_GRUPO_TAXISTAS = os.environ.get('TELEGRAM_CHAT_ID_GRUPO_TAXISTAS', '')
    
    # Configuración de Claude AI para Railway (opcional)
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
    
    # Configuración de timezone para Colombia
    TIME_ZONE = 'America/Bogota'
    USE_TZ = True
    
    # Configuración de idioma
    LANGUAGE_CODE = 'es-co'
    USE_I18N = True
    USE_L10N = True
    
    print("🚀 Configuración de Railway activada")
    print(f"📊 Base de datos: {DATABASES['default']['ENGINE']}")
    print(f"🔴 Redis URL: {REDIS_URL}")
    print(f"🌐 Hosts permitidos: {ALLOWED_HOSTS}")
