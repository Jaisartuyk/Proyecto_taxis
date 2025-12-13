# taxis/api_urls.py (crea este nuevo archivo en tu app 'taxis')

from django.urls import path
from .api_views import LoginAPIView, save_webpush_subscription, UpdateLocationAPIView, test_push_notification
from .badge_api import get_badge_count, clear_badge, mark_messages_read

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('save-subscription/', save_webpush_subscription, name='api_save_subscription'),
    path('update-location/', UpdateLocationAPIView.as_view(), name='api_update_location'),
    path('badge-count/', get_badge_count, name='api_badge_count'),
    path('clear-badge/', clear_badge, name='api_clear_badge'),
    path('mark-messages-read/', mark_messages_read, name='api_mark_messages_read'),
    
    # 🧪 Vista de prueba para notificaciones push
    path('test-push-notification/', test_push_notification, name='api_test_push_notification'),
    
    # Puedes añadir más URLs de API aquí en el futuro:
    # path('drivers/', DriverLocationAPIView.as_view(), name='api_drivers_location'),
]