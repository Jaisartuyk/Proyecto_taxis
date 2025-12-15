"""
Script para probar envío individual de notificaciones push con debug detallado
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import WebPushSubscription
from django.contrib.auth import get_user_model
from pywebpush import webpush, WebPushException
from django.conf import settings
import json

User = get_user_model()

def test_individual_notifications():
    print("🚀 Probando envío individual de notificaciones push...")
    print("=" * 70)
    
    subscriptions = WebPushSubscription.objects.all().select_related('user')
    
    if not subscriptions.exists():
        print("❌ No hay suscripciones para probar")
        return
    
    # Preparar datos de notificación
    notification_data = {
        "title": "🚗 Prueba Individual",
        "body": "Probando envío específico",
        "icon": "/static/imagenes/icon-192x192.png",
        "badge": "/static/imagenes/icon-192x192.png",
        "tag": "test-individual",
        "requireInteraction": False,
        "data": {
            "url": "/",
            "timestamp": "2025-12-12 15:30:00"
        }
    }
    
    payload = json.dumps(notification_data)
    
    # Verificar configuración VAPID
    print("🔑 Configuración VAPID:")
    print(f"   📧 Admin Email: {settings.VAPID_ADMIN_EMAIL}")
    print(f"   🔑 Private Key disponible: {'✅' if settings.VAPID_PRIVATE_KEY else '❌'}")
    print(f"   🔑 Public Key disponible: {'✅' if settings.VAPID_PUBLIC_KEY else '❌'}")
    print()
    
    # Probar envío a cada usuario individualmente
    for subscription in subscriptions:
        user = subscription.user
        print(f"👤 Probando envío a: {user.username} ({user.get_full_name()})")
        
        try:
            # Obtener datos de suscripción
            sub_info = subscription.subscription_info
            endpoint = sub_info.get('endpoint')
            keys = sub_info.get('keys', {})
            
            print(f"   📡 Endpoint: {endpoint[:50]}...")
            print(f"   🔐 Keys Auth: {'✅' if 'auth' in keys else '❌'}")
            print(f"   📡 Keys P256dh: {'✅' if 'p256dh' in keys else '❌'}")
            
            # Intentar envío
            print("   🚀 Enviando notificación...")
            
            # Construir audience correctamente
            from urllib.parse import urlparse
            parsed_endpoint = urlparse(endpoint)
            aud = f"{parsed_endpoint.scheme}://{parsed_endpoint.netloc}"
            
            print(f"   🎯 Audience: {aud}")
            
            response = webpush(
                subscription_info=sub_info,
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={
                    "sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}",
                    "aud": aud
                }
            )
            
            print(f"   ✅ Enviado exitosamente!")
            print(f"   📊 Status code: {response.status_code}")
            print(f"   📋 Headers: {dict(response.headers)}")
            
        except WebPushException as e:
            print(f"   ❌ Error WebPush: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   📊 Status code: {e.response.status_code}")
                print(f"   📋 Response: {e.response.text}")
        except Exception as e:
            print(f"   ❌ Error general: {type(e).__name__}: {e}")
            import traceback
            print(f"   🔍 Traceback: {traceback.format_exc()}")
        
        print()
    
    print("=" * 70)

if __name__ == "__main__":
    test_individual_notifications()