#!/usr/bin/env python
"""
Script para verificar suscripciones push activas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import WebPushSubscription, AppUser

print("=" * 80)
print("🔔 VERIFICACIÓN DE SUSCRIPCIONES PUSH")
print("=" * 80)

# Listar todas las suscripciones
subscriptions = WebPushSubscription.objects.all()

if not subscriptions.exists():
    print("\n❌ No hay suscripciones push registradas")
else:
    print(f"\n📱 Total de suscripciones: {subscriptions.count()}\n")
    
    for sub in subscriptions:
        user = sub.user
        endpoint = sub.subscription_info.get('endpoint', 'N/A')
        created = sub.created_at.strftime('%Y-%m-%d %H:%M:%S') if sub.created_at else 'N/A'
        
        # Extraer proveedor del endpoint
        provider = 'Unknown'
        if 'fcm.googleapis.com' in endpoint:
            provider = 'FCM (Firebase)'
        elif 'updates.push.services.mozilla.com' in endpoint:
            provider = 'Mozilla'
        elif 'web.push.apple.com' in endpoint:
            provider = 'Apple'
        
        print(f"👤 Usuario: {user.get_full_name()} (@{user.username}, ID: {user.id})")
        print(f"   📅 Creada: {created}")
        print(f"   🌐 Proveedor: {provider}")
        print(f"   🔗 Endpoint: {endpoint[:80]}...")
        print()

print("=" * 80)
print("\n💡 Para que las notificaciones funcionen:")
print("   1. El usuario debe tener una suscripción activa")
print("   2. La app móvil debe llamar a POST /api/push/ al iniciar")
print("   3. Si la suscripción expiró, debe renovarse")
print("\n🔄 Para renovar suscripción:")
print("   - Desde la app móvil, llamar a POST /api/push/ con nueva subscription")
print("=" * 80)
