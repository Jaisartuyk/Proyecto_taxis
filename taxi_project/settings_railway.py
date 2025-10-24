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
    
    # Channels configuration con Redis de Railway
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [REDIS_URL],
                "capacity": 1500,
                "expiry": 60,
            },
        },
    }
    
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
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    
    # Configuración de logging para Railway
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
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
