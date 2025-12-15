"""
Script para limpiar suscripciones expiradas y preparar para nuevas suscripciones
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import WebPushSubscription
from django.contrib.auth import get_user_model

User = get_user_model()

def clean_expired_subscriptions():
    print("🧹 Limpiando suscripciones expiradas...")
    print("=" * 50)
    
    subscriptions = WebPushSubscription.objects.all()
    
    print(f"📊 Suscripciones antes de limpieza: {subscriptions.count()}")
    
    # Eliminar todas las suscripciones actuales ya que fueron creadas con claves VAPID diferentes
    deleted_count = 0
    for sub in subscriptions:
        print(f"🗑️ Eliminando suscripción de {sub.user.username} (creada: {sub.created_at})")
        sub.delete()
        deleted_count += 1
    
    print(f"\n✅ Eliminadas {deleted_count} suscripciones")
    print("📋 Para recibir notificaciones push, cada usuario debe:")
    print("   1. Abrir la aplicación en su navegador")
    print("   2. Permitir notificaciones cuando se le solicite")
    print("   3. La nueva suscripción usará las claves VAPID correctas")
    
    # Mostrar usuarios disponibles
    users = User.objects.all()
    print(f"\n👥 Usuarios disponibles para nuevas suscripciones:")
    for user in users:
        print(f"   - {user.username} ({user.get_full_name()})")
    
    print("\n🔑 Claves VAPID actuales configuradas para nuevas suscripciones")
    print("✨ Las próximas suscripciones funcionarán correctamente")

if __name__ == "__main__":
    clean_expired_subscriptions()