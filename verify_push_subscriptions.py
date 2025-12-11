#!/usr/bin/env python
"""
Script para verificar suscripciones a push notifications
"""
import os
import sys
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

import django
django.setup()

from taxis.models import WebPushSubscription

print("=" * 80)
print("🔔 VERIFICACIÓN DE SUSCRIPCIONES A PUSH NOTIFICATIONS")
print("=" * 80)

subscriptions = WebPushSubscription.objects.all()

if not subscriptions.exists():
    print("\n❌ NO HAY SUSCRIPCIONES REGISTRADAS")
    print("\n💡 Esto significa que ningún usuario ha aceptado las notificaciones push.")
    print("   Para habilitar notificaciones:")
    print("   1. Abre la app en el navegador")
    print("   2. Acepta el permiso de notificaciones cuando aparezca")
    print("   3. El navegador se suscribirá automáticamente")
else:
    print(f"\n✅ Total de suscripciones: {subscriptions.count()}\n")
    
    for i, sub in enumerate(subscriptions, 1):
        user_info = f"Usuario: {sub.user.username}" if sub.user else "Usuario: Anónimo"
        print(f"{i}. {user_info}")
        
        # subscription_info puede ser string o dict
        if isinstance(sub.subscription_info, str):
            try:
                sub_data = json.loads(sub.subscription_info)
            except:
                sub_data = {}
        else:
            sub_data = sub.subscription_info
        
        endpoint = sub_data.get('endpoint', 'No disponible')
        print(f"   Endpoint: {endpoint[:60]}...")
        print(f"   Creado: {sub.created_at}")
        
        # Verificar si tiene las claves necesarias
        has_keys = 'keys' in sub_data
        has_p256dh = 'p256dh' in sub_data.get('keys', {})
        has_auth = 'auth' in sub_data.get('keys', {})
        
        if has_keys and has_p256dh and has_auth:
            print(f"   Estado: ✅ Completa (tiene todas las claves)")
        else:
            print(f"   Estado: ⚠️ Incompleta (faltan claves)")
        print()

print("=" * 80)
print("\n📋 CLAVES VAPID:")
print("=" * 80)

from django.conf import settings

if hasattr(settings, 'WEBPUSH_SETTINGS'):
    vapid_private = settings.WEBPUSH_SETTINGS.get('VAPID_PRIVATE_KEY', 'No configurada')
    vapid_public = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', 'No configurada')
    
    print(f"✅ Clave Pública: {vapid_public[:30]}...")
    print(f"✅ Clave Privada: {'***configurada***' if vapid_private != 'No configurada' else 'No configurada'}")
else:
    print("❌ WEBPUSH_SETTINGS no está configurado en settings.py")

print("\n" + "=" * 80)
