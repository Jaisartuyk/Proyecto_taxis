"""
URLs de la API REST para la aplicación de taxis
Incluye endpoints para Flutter y otras apps móviles
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import LoginAPIView, save_webpush_subscription, UpdateLocationAPIView, test_push_notification, driver_info
from .badge_api import get_badge_count, clear_badge, mark_messages_read
from .api_viewsets import (
    ProfileViewSet, RegisterViewSet, DriverViewSet,
    RideViewSet, RatingViewSet
)
from .fcm_api_views import (
    register_fcm_token_view,
    unregister_fcm_token_view,
    test_fcm_notification_view
)

# Router para ViewSets
router = DefaultRouter()
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'rides', RideViewSet, basename='ride')
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    # =====================================================
    # AUTENTICACIÓN
    # =====================================================
    path('login/', LoginAPIView.as_view(), name='api_login'),
    
    # =====================================================
    # REGISTRO
    # =====================================================
    path('register/driver/', RegisterViewSet.as_view({'post': 'driver'}), name='api_register_driver'),
    path('register/customer/', RegisterViewSet.as_view({'post': 'customer'}), name='api_register_customer'),
    
    # =====================================================
    # PERFIL
    # =====================================================
    path('profile/', ProfileViewSet.as_view({'get': 'list', 'put': 'update', 'patch': 'update'}), name='api_profile'),
    path('profile/upload-picture/', ProfileViewSet.as_view({'post': 'upload_picture'}), name='api_profile_upload_picture'),
    path('profile/stats/', ProfileViewSet.as_view({'get': 'stats'}), name='api_profile_stats'),
    
    # =====================================================
    # UBICACIÓN
    # =====================================================
    path('update-location/', UpdateLocationAPIView.as_view(), name='api_update_location'),
    
    # =====================================================
    # INFORMACIÓN DE CONDUCTORES
    # =====================================================
    path('driver-info/<str:driver_id>/', driver_info, name='api_driver_info'),
    
    # =====================================================
    # BADGES Y NOTIFICACIONES
    # =====================================================
    path('badge-count/', get_badge_count, name='api_badge_count'),
    path('clear-badge/', clear_badge, name='api_clear_badge'),
    path('mark-messages-read/', mark_messages_read, name='api_mark_messages_read'),
    path('save-subscription/', save_webpush_subscription, name='api_save_subscription'),
    path('test-push-notification/', test_push_notification, name='api_test_push_notification'),
    
    # =====================================================
    # FIREBASE CLOUD MESSAGING (FCM)
    # =====================================================
    path('fcm/register/', register_fcm_token_view, name='api_fcm_register'),
    path('fcm/unregister/', unregister_fcm_token_view, name='api_fcm_unregister'),
    path('fcm/test/', test_fcm_notification_view, name='api_fcm_test'),
    
    # =====================================================
    # VIEWSETS (CRUD completo)
    # =====================================================
    # Incluye:
    # - GET/POST /api/drivers/ - Listar/crear conductores
    # - GET /api/drivers/{id}/ - Detalle de conductor
    # - GET /api/drivers/nearby/?lat=X&lon=Y - Conductores cercanos
    #
    # - GET/POST /api/rides/ - Listar/crear carreras
    # - GET /api/rides/{id}/ - Detalle de carrera
    # - PUT/PATCH /api/rides/{id}/ - Actualizar carrera
    # - DELETE /api/rides/{id}/ - Eliminar carrera
    # - POST /api/rides/{id}/accept/ - Aceptar carrera
    # - POST /api/rides/{id}/start/ - Iniciar carrera
    # - POST /api/rides/{id}/complete/ - Completar carrera
    # - POST /api/rides/{id}/cancel/ - Cancelar carrera
    # - GET /api/rides/available/ - Carreras disponibles
    # - GET /api/rides/active/ - Carreras activas
    #
    # - GET/POST /api/ratings/ - Listar/crear calificaciones
    # - GET /api/ratings/{id}/ - Detalle de calificación
    # - GET /api/ratings/received/ - Calificaciones recibidas
    # - GET /api/ratings/given/ - Calificaciones dadas
    path('', include(router.urls)),
]