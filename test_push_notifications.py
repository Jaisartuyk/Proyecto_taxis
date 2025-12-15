"""
Script de prueba para las notificaciones push
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from taxis.push_notifications import send_push_notification

User = get_user_model()

def test_push_notification():
    print("🧪 Probando notificaciones push...")
    
    # Buscar un usuario con suscripciones
    from taxis.models import WebPushSubscription
    
    subscriptions = WebPushSubscription.objects.all()
    if not subscriptions.exists():
        print("❌ No hay suscripciones push disponibles para probar")
        return
    
    for subscription in subscriptions:
        user = subscription.user
        print(f"📱 Enviando notificación de prueba a {user.username}...")
        
        try:
            result = send_push_notification(
                user=user,
                title="🧪 Prueba de Notificación",
                body="Esta es una notificación de prueba para verificar que el sistema funciona correctamente",
                data={
                    "test": True,
                    "timestamp": "2025-12-13",
                    "url": "/dashboard/"
                }
            )
            
            if result > 0:
                print(f"✅ Notificación enviada exitosamente a {user.username}")
            else:
                print(f"⚠️ No se pudo enviar la notificación a {user.username}")
                
        except Exception as e:
            print(f"❌ Error enviando notificación a {user.username}: {e}")
    
    print("🏁 Prueba completada")

if __name__ == "__main__":
    test_push_notification()