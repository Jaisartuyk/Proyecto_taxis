"""
Script de prueba para Firebase Cloud Messaging (FCM)
Ejecuta: python test_fcm.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.fcm_notifications import initialize_firebase

print("=" * 60)
print("🧪 PRUEBA DE FIREBASE CLOUD MESSAGING (FCM)")
print("=" * 60)

# Prueba 1: Inicializar Firebase
print("\n📋 Prueba 1: Inicializar Firebase")
print("-" * 60)

result = initialize_firebase()

if result:
    print("✅ Firebase inicializado correctamente")
    print("✅ Las credenciales están configuradas")
    print("✅ FCM está listo para enviar notificaciones")
else:
    print("❌ Firebase NO se pudo inicializar")
    print("⚠️  Verifica que la variable FIREBASE_CREDENTIALS_JSON esté configurada")
    print("⚠️  O que el archivo firebase-credentials.json exista")

print("\n" + "=" * 60)
print("🎯 RESULTADO FINAL")
print("=" * 60)

if result:
    print("✅ FCM está FUNCIONANDO correctamente")
    print("\n📱 Próximos pasos:")
    print("1. Configurar Firebase en tu app Flutter")
    print("2. Obtener el token FCM desde Flutter")
    print("3. Registrar el token con: POST /api/fcm/register/")
    print("4. Enviar notificación de prueba con: POST /api/fcm/test/")
else:
    print("❌ FCM NO está funcionando")
    print("\n🔧 Soluciones:")
    print("1. Verifica que FIREBASE_CREDENTIALS_JSON esté en Railway")
    print("2. O crea el archivo firebase-credentials.json localmente")
    print("3. Reinicia el servidor Django")

print("=" * 60)
