"""
Script de prueba para envío de notificaciones push cuando tengas nuevas suscripciones
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.push_notifications import send_push_notification
from django.contrib.auth import get_user_model
from taxis.models import WebPushSubscription

User = get_user_model()

def test_new_subscriptions():
    print("🚀 Probando notificaciones push con nuevas suscripciones...")
    print("=" * 60)
    
    # Verificar si hay suscripciones
    subscriptions = WebPushSubscription.objects.all()
    print(f"📊 Suscripciones activas: {subscriptions.count()}")
    
    if subscriptions.count() == 0:
        print("\n❌ No hay suscripciones disponibles")
        print("📋 Para crear nuevas suscripciones:")
        print("   1. Abre la aplicación en tu navegador")
        print("   2. Ve a la sección donde se solicitan permisos de notificación")
        print("   3. Permite las notificaciones push")
        print("   4. Ejecuta este script nuevamente")
        return
    
    # Mostrar suscripciones disponibles
    print("\n👥 Suscripciones disponibles:")
    for sub in subscriptions:
        print(f"   - {sub.user.username} ({sub.user.get_full_name()}) - {sub.created_at}")
    
    # Probar envío
    print("\n🚀 Enviando notificación de prueba...")
    
    try:
        # Obtener todos los usuarios con suscripciones
        users_with_subs = User.objects.filter(webpushsubscription__isnull=False).distinct()
        
        result = send_push_notification(
            users=users_with_subs,
            title="🎉 ¡Notificaciones funcionando!",
            body="Las notificaciones push ya están configuradas correctamente",
            icon="/static/imagenes/icon-192x192.png",
            data={
                "url": "/",
                "action": "test_success"
            }
        )
        
        if result:
            print(f"✅ Notificación enviada exitosamente a {len(users_with_subs)} usuarios")
        else:
            print("❌ Error enviando la notificación")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_new_subscriptions()