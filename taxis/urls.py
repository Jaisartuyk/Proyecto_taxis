from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from . import views
from . import api_views
from . import admin_views  # Panel de administración Fase 3
from .whatsapp_webhook import whatsapp_webhook, whatsapp_status_webhook, whatsapp_send_notification
from .views import get_google_maps_key



urlpatterns = [
    path('', views.home, name='home'),
    path('offline/', views.offline_view, name='offline'),
    path('debug-notifications/', views.debug_notifications, name='debug_notifications'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    #path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('revision/', views.revision, name='revision'),
    path('map-view', views.map_view, name='map'),
    path('update-location/', views.update_location, name='update_location'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('register/customer/', views.register_customer, name='register_customer'),
    path('driver-dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('customer-dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('taxi-route/', views.taxi_route_view, name='taxi_route_view'),
    path('taxi-routes/', views.taxi_route_list_view, name='taxi_route_list'),
    path('rutas-disponibles/', views.available_routes_list_view, name='available_routes_list'),
    path('unirse-a-ruta/<int:route_id>/', views.join_taxi_route_view, name='join_taxi_route'),
    path('request-ride/', views.request_ride, name='request_ride'),
    path('available-rides/', views.available_rides, name='available_rides'),
    path('active-rides/', views.active_rides, name='active_rides'),
    path('update-ride-status/<int:ride_id>/', views.update_ride_status, name='update_ride_status'),
    path('ride_status/<int:ride_id>/', views.ride_status, name='ride_status'),
    path('ride/<int:ride_id>/', views.ride_detail, name='ride_detail'),
    path('ride/<int:ride_id>/cancel/', views.cancel_ride, name='ride_cancel'),
    path('ride/<int:ride_id>/complete/', views.complete_ride, name='ride_complete'),
    path('api/driver-location/<int:driver_id>/', views.driver_location_api, name='driver_location_api'),
    path('chat/<str:room_name>/', views.chat_room, name='chat_room'),
    path('customer/rides/', views.customer_rides, name='customer_rides'),
    path('driver/in-progress/', views.driver_in_progress_rides, name='driver_in_progress_rides'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/check_new_rides/', views.check_new_rides, name='check_new_rides'),
    path('admin_users/', views.admin_users, name='admin_users'),
    path("api/taxis_ubicacion/", views.taxis_ubicacion, name="taxis_ubicacion"),
    path('conductores/', views.list_drivers, name='list_drivers'),
    path('eliminar_conductor/<int:user_id>/', views.delete_driver, name='delete_driver'),
    path('comunicacion/', views.comunicacion_conductores, name='comunicacion_conductores'),
    path("api/actualizar_ubicacion/", views.actualizar_ubicacion, name="actualizar_ubicacion"),
    path('api/chat_history/<int:user_id>/', views.get_chat_history, name='get_chat_history'),
    re_path(r'^api/driver/chat_history/(?P<driver_id>[\w-]+)/$', views.get_driver_chat_history, name='get_driver_chat_history'),
    path('api/register-fcm-token/', views.register_fcm_token_view, name='register_fcm_token'),
    path('ubicaciones_taxis/', views.ubicaciones_taxis, name='ubicaciones_taxis'),
    path('api/ubicaciones_taxis/', views.ubicaciones_taxis, name='api_ubicaciones_taxis'),
    path('actualizar_ubicacion_taxi/', views.actualizar_ubicacion_taxi, name='actualizar_ubicacion_taxi'),
    path('webhook/telegram/', views.telegram_webhook, name='telegram_webhook'),
    
    # WhatsApp Webhook endpoints
    path('webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    path('webhook/whatsapp/status/', whatsapp_status_webhook, name='whatsapp_status_webhook'),
    path('api/whatsapp/send-notification/', whatsapp_send_notification, name='whatsapp_send_notification'),
    
    # Sistema de calificaciones
    path('ride/<int:ride_id>/rate/', views.rate_ride, name='rate_ride'),
    path('user/<int:user_id>/ratings/', views.user_ratings, name='user_ratings'),

    # Chat Central
    path('central-comunicacion/', views.chat_central, name='chat_central'),
    path('api/maps-key/', get_google_maps_key, name='get_maps_key'),
    
    # Chat Media Upload
    path('api/chat/upload/', views.upload_chat_media, name='upload_chat_media'),
    
    # FCM - Firebase Cloud Messaging
    path('api/fcm/register/', api_views.register_fcm_token_view, name='register_fcm_token'),
    
    # API para App Móvil - Conductor
    path('api/driver/stats/', api_views.driver_stats_view, name='driver_stats'),
    path('api/rides/history/', api_views.ride_history_view, name='ride_history'),
    path('api/rides/available/', api_views.available_rides_view, name='api_available_rides'),
    path('api/rides/active/', api_views.driver_active_rides_view, name='driver_active_rides'),
    path('api/rides/<int:ride_id>/', api_views.ride_detail_api_view, name='ride_detail_api'),
    path('api/rides/<int:ride_id>/accept/', api_views.accept_ride_view, name='accept_ride'),
    path('api/rides/<int:ride_id>/start/', api_views.start_ride_view, name='start_ride'),
    path('api/rides/<int:ride_id>/complete/', api_views.complete_ride_view, name='complete_ride'),
    path('api/rides/<int:ride_id>/cancel/', api_views.cancel_ride_view, name='cancel_ride'),
    
    # Panel de WhatsApp
    path('whatsapp/panel/', views.whatsapp_panel, name='whatsapp_panel'),
    path('whatsapp/conversation/<int:conversation_id>/', views.whatsapp_conversation_detail, name='whatsapp_conversation_detail'),
    path('whatsapp/send-message/', views.whatsapp_send_message, name='whatsapp_send_message'),
    path('api/whatsapp/stats/', views.whatsapp_stats_api, name='whatsapp_stats_api'),
    
    # Service Worker (Root Scope)
    path('service-worker.js', views.service_worker, name='service_worker'),
    
    # Prueba de Notificaciones
    path('test-notifications/', views.test_notifications, name='test_notifications'),
    
    # Limpiar Caché
    path('clear-cache/', views.clear_cache, name='clear_cache'),
    
    # ============================================
    # PANEL DE ADMINISTRACIÓN (FASE 3)
    # ============================================
    # Super Admin (gestiona todas las cooperativas)
    path('superadmin/dashboard/', admin_views.SuperAdminDashboardView.as_view(), name='superadmin_dashboard'),
    
    # Admin de Cooperativa (gestiona su propia cooperativa)
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Cooperativas
    path('admin/organizations/', admin_views.OrganizationListView.as_view(), name='admin_organizations'),
    path('admin/organizations/create/', admin_views.OrganizationCreateView.as_view(), name='admin_organization_create'),
    path('admin/organizations/<int:pk>/edit/', admin_views.OrganizationUpdateView.as_view(), name='admin_organization_edit'),
    path('admin/organizations/<int:pk>/', admin_views.OrganizationDetailView.as_view(), name='admin_organization_detail'),
    path('admin/organizations/<int:pk>/suspend/', admin_views.OrganizationSuspendView.as_view(), name='admin_organization_suspend'),
    
    # Conductores
    path('admin/drivers/pending/', admin_views.DriverApprovalListView.as_view(), name='admin_drivers_pending'),
    path('admin/drivers/<int:pk>/approve/', admin_views.DriverApproveView.as_view(), name='admin_driver_approve'),
    path('admin/drivers/<int:pk>/reject/', admin_views.DriverRejectView.as_view(), name='admin_driver_reject'),
    
    # Reportes
    path('admin/reports/financial/', admin_views.FinancialReportsView.as_view(), name='admin_reports_financial'),
    
    # Facturas (DESHABILITADO - Invoice no existe)
    # path('admin/invoices/', admin_views.InvoiceListView.as_view(), name='admin_invoices'),
    # path('admin/invoices/create/', admin_views.InvoiceCreateView.as_view(), name='admin_invoice_create'),
    # path('admin/invoices/<int:pk>/mark-paid/', admin_views.InvoiceMarkPaidView.as_view(), name='admin_invoice_mark_paid'),
]

