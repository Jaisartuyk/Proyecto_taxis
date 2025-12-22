"""URLs para el chat
Agregar estas rutas a tu archivo urls.py principal o al urls.py de tu app de chat"""

from django.urls import path
from . import views  # Ajusta el import según tu estructura

# Si usas DRF (Django REST Framework):
urlpatterns = [
    path('api/chat/upload/', views.upload_chat_media, name='upload_chat_media'),
]

# Si NO usas DRF, usa esta versión:
# from .views import upload_chat_media_simple
# urlpatterns = [
#     path('api/chat/upload/', upload_chat_media_simple, name='upload_chat_media'),
# ]

# IMPORTANTE: Agregar estas rutas a tu urls.py principal (taxi_project/urls.py):
# 
# from django.urls import path, include
# from taxis import urls_chat  # O importa directamente la función
# 
# urlpatterns = [
#     # ... tus rutas existentes ...
#     path('', include('taxis.urls')),  # Si ya tienes esto, las rutas se agregarán automáticamente
#     # O directamente:
#     path('api/chat/upload/', views.upload_chat_media, name='upload_chat_media'),
# ]

