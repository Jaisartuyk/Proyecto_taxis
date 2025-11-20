"""
Configuración de producción para el proyecto de taxis
"""
from .settings import *
import os
import dj_database_url

# Configuración de seguridad
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Hosts permitidos
ALLOWED_HOSTS = [
    'taxis-deaquipalla.up.railway.app',
    'taxis-django-channels-production.up.railway.app',
    'your-domain.com',
    'www.your-domain.com',
]

# Base de datos de producción
DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        default='sqlite:///db.sqlite3'
    )
}

# Configuración de seguridad SSL
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Configuración de archivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuración de logging
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
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'taxis': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Configuración de caché (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Configuración de sesiones
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Configuración de email (opcional)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@your-domain.com')

# Configuración de WhatsApp
WASENDER_API_URL = os.environ.get('WASENDER_API_URL', 'https://wasenderapi.com/api/send-message')
WASENDER_TOKEN = os.environ.get('WASENDER_TOKEN', '')

# Configuración de Google Maps
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')

# Configuración de Telegram
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID_GRUPO_TAXISTAS = os.environ.get('TELEGRAM_CHAT_ID_GRUPO_TAXISTAS', '')

# Configuración de Claude AI (opcional)
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')

# Configuración de rate limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Configuración de CORS
CORS_ALLOWED_ORIGINS = [
    'https://taxis-deaquipalla.up.railway.app',
    'https://taxis-django-channels-production.up.railway.app',
    'https://your-domain.com',
]

# Configuración de CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://taxis-deaquipalla.up.railway.app',
    'https://taxis-django-channels-production.up.railway.app',
    'https://your-domain.com',
]

# Configuración de archivos de media
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Configuración de timezone
TIME_ZONE = 'America/Bogota'
USE_TZ = True

# Configuración de idioma
LANGUAGE_CODE = 'es-co'
USE_I18N = True
USE_L10N = True

# Configuración de middleware adicional para producción
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Configuración de aplicaciones adicionales para producción
INSTALLED_APPS += [
    'corsheaders',
    'django_redis',
]

# Configuración de WebSockets para producción
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
            "capacity": 1500,
            "expiry": 60,
        },
    },
}

# Configuración de archivos estáticos para producción
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Configuración de compresión
COMPRESS_ENABLED = True
COMPRESS_OFFLINE = True

# Configuración de seguridad adicional
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuración de cookies
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# Configuración de archivos de log
if not os.path.exists(os.path.join(BASE_DIR, 'logs')):
    os.makedirs(os.path.join(BASE_DIR, 'logs'))

