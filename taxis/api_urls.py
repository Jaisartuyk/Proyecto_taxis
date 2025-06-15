# taxis/api_urls.py (crea este nuevo archivo en tu app 'taxis')

from django.urls import path
from .api_views import LoginAPIView, api_request_ride # Importa tu nueva vista de API

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('api/solicitar-carrera/', api_request_ride, name='api_solicitar_carrera'),
    # Puedes añadir más URLs de API aquí en el futuro:
    # path('drivers/', DriverLocationAPIView.as_view(), name='api_drivers_location'),
]