"""
Configuración específica para Railway con PostgreSQL y Redis
"""
from .settings import *
import os
import dj_database_url

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
        
        if VAPID_PUBLIC and VAPID_PRIVATE:
            # Solo actualizar si las claves están configuradas
            WEBPUSH_SETTINGS = {
                "VAPID_PUBLIC_KEY": VAPID_PUBLIC,
                "VAPID_PRIVATE_KEY": VAPID_PRIVATE,
                "VAPID_ADMIN_EMAIL": os.environ.get('VAPID_ADMIN_EMAIL', 'admin@deaquipalla.com')
            }
            print(f"🔔 [RAILWAY] Push notifications configuradas con VAPID")
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
    
    # Verificar disponibilidad de channels_redis
    try:
        import channels_redis.core
        print("✅ [RAILWAY] channels_redis disponible")
    except ImportError as e:
        print(f"❌ [RAILWAY] Error: {e}")
        # Fallback a InMemory si Redis no está disponible
        CHANNEL_LAYERS = {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            },
        }
        print("🔄 [RAILWAY] Fallback a InMemoryChannelLayer")
    
    # COMENTADO: Redis configuration que está causando problemas
    # from urllib.parse import urlparse
    # parsed_redis = urlparse(REDIS_URL)
    # 
    # CHANNEL_LAYERS = {
    #     "default": {
    #         "BACKEND": "channels_redis.core.RedisChannelLayer",
    #         "CONFIG": {
    #             "hosts": [{
    #                 "address": (parsed_redis.hostname, parsed_redis.port or 6379),
    #                 "password": parsed_redis.password,
    #                 "db": 0,
    #             }],
    #             "capacity": 1500,
    #             "expiry": 60,
    #         },
    #     },
    # }
    
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
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
        os.path.join(BASE_DIR, 'taxis', 'static'),
    ]
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
    
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
