#!/usr/bin/env python
"""
Script para limpiar suscripciones push expiradas
"""
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

import django
django.setup()

from taxis.models import WebPushSubscription
from taxis.push_notifications import send_push_notification

print("=" * 80)
print("🧹 LIMPIEZA DE SUSCRIPCIONES PUSH EXPIRADAS")
print("=" * 80)

subscriptions = WebPushSubscription.objects.all()
print(f"\n📊 Total de suscripciones antes: {subscriptions.count()}")

# Probar cada suscripción
deleted_count = 0
valid_count = 0

for sub in subscriptions:
    try:
        # Intentar enviar una notificación de prueba
        result = send_push_notification(
            user=sub.user,
            title="🔔 Test de Suscripción",
            body="Esta es una notificación de prueba para verificar que tu dispositivo está suscrito correctamente.",
            data={'type': 'test'}
        )
        
        if result:
            print(f"✅ Suscripción válida: {sub.user.username}")
            valid_count += 1
        else:
            print(f"⚠️ Suscripción sin respuesta: {sub.user.username}")
            
    except Exception as e:
        if "410" in str(e) or "expired" in str(e).lower():
            print(f"❌ Suscripción expirada eliminada: {sub.user.username}")
            sub.delete()
            deleted_count += 1
        else:
            print(f"⚠️ Error en suscripción de {sub.user.username}: {e}")

print(f"\n📊 Suscripciones válidas: {valid_count}")
print(f"🗑️  Suscripciones eliminadas: {deleted_count}")
print(f"✅ Total final: {WebPushSubscription.objects.count()}")

print("\n" + "=" * 80)
print("💡 IMPORTANTE:")
print("=" * 80)
print("Los usuarios deben:")
print("1. Abrir la app en el navegador")
print("2. Aceptar el permiso de notificaciones")
print("3. La app se suscribirá automáticamente")
print("=" * 80)
