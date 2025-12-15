"""
Script para verificar las suscripciones de push notifications por usuario
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

def check_user_subscriptions():
    print("🔍 Verificando suscripciones push por usuario...")
    print("=" * 60)
    
    subscriptions = WebPushSubscription.objects.all().select_related('user')
    
    if not subscriptions.exists():
        print("❌ No hay suscripciones push en la base de datos")
        return
    
    for subscription in subscriptions:
        user = subscription.user
        print(f"\n👤 Usuario: {user.username} ({user.get_full_name()})")
        print(f"   📅 Creada: {subscription.created_at}")
        print(f"   🔗 Endpoint: {subscription.subscription_info.get('endpoint', 'N/A')[:50]}...")
        
        # Verificar si la suscripción tiene los campos necesarios
        sub_info = subscription.subscription_info
        has_endpoint = 'endpoint' in sub_info
        has_keys = 'keys' in sub_info
        has_auth = has_keys and 'auth' in sub_info.get('keys', {})
        has_p256dh = has_keys and 'p256dh' in sub_info.get('keys', {})
        
        print(f"   ✅ Validación:")
        print(f"      📍 Endpoint: {'✅' if has_endpoint else '❌'}")
        print(f"      🔑 Keys: {'✅' if has_keys else '❌'}")
        print(f"      🔐 Auth: {'✅' if has_auth else '❌'}")
        print(f"      📡 P256dh: {'✅' if has_p256dh else '❌'}")
        
        is_valid = has_endpoint and has_keys and has_auth and has_p256dh
        print(f"   🎯 Estado: {'✅ VÁLIDA' if is_valid else '❌ INVÁLIDA'}")
    
    print("\n" + "=" * 60)
    print(f"📊 Total de suscripciones: {subscriptions.count()}")
    
    # Contar válidas e inválidas
    valid_count = 0
    invalid_count = 0
    
    for sub in subscriptions:
        sub_info = sub.subscription_info
        is_valid = (
            'endpoint' in sub_info and
            'keys' in sub_info and
            'auth' in sub_info.get('keys', {}) and
            'p256dh' in sub_info.get('keys', {})
        )
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
    
    print(f"✅ Suscripciones válidas: {valid_count}")
    print(f"❌ Suscripciones inválidas: {invalid_count}")

if __name__ == "__main__":
    check_user_subscriptions()