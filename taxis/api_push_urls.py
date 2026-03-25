"""
URLs para API de Push Notifications
"""
from django.urls import path
from .api_push_subscribe import subscribe_push, unsubscribe_push, get_vapid_public_key

urlpatterns = [
    path('', subscribe_push, name='api_push_subscribe'),
    path('unsubscribe/', unsubscribe_push, name='api_push_unsubscribe'),
    path('vapid-public-key/', get_vapid_public_key, name='api_vapid_public_key'),
]
