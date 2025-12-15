"""
Script para limpiar y corregir las suscripciones de Web Push existentes
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import WebPushSubscription

def fix_subscriptions():
    print("🔧 Corrigiendo suscripciones Web Push...")
    
    subscriptions = WebPushSubscription.objects.all()
    fixed_count = 0
    deleted_count = 0
    
    for subscription in subscriptions:
        try:
            # Si subscription_info es string, convertir a dict
            if isinstance(subscription.subscription_info, str):
                try:
                    subscription_data = json.loads(subscription.subscription_info)
                    subscription.subscription_info = subscription_data
                    subscription.save()
                    fixed_count += 1
                    print(f"✅ Corregida suscripción para {subscription.user.username}")
                except json.JSONDecodeError:
                    print(f"❌ Eliminando suscripción inválida para {subscription.user.username}")
                    subscription.delete()
                    deleted_count += 1
            else:
                # Verificar que tenga las claves necesarias
                if not isinstance(subscription.subscription_info, dict):
                    print(f"❌ Eliminando suscripción con tipo inválido para {subscription.user.username}")
                    subscription.delete()
                    deleted_count += 1
                elif not all(key in subscription.subscription_info for key in ['endpoint', 'keys']):
                    print(f"❌ Eliminando suscripción incompleta para {subscription.user.username}")
                    subscription.delete()
                    deleted_count += 1
                    
        except Exception as e:
            print(f"❌ Error procesando suscripción de {subscription.user.username}: {e}")
            subscription.delete()
            deleted_count += 1
    
    print(f"\n📊 Resumen:")
    print(f"   ✅ Suscripciones corregidas: {fixed_count}")
    print(f"   ❌ Suscripciones eliminadas: {deleted_count}")
    print(f"   📱 Suscripciones válidas restantes: {WebPushSubscription.objects.count()}")

if __name__ == "__main__":
    fix_subscriptions()