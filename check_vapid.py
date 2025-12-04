"""
Script para verificar las claves VAPID que está usando Django
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.conf import settings

print("=" * 70)
print("🔐 CLAVES VAPID ACTUALES EN EL SERVIDOR")
print("=" * 70)

vapid_settings = settings.WEBPUSH_SETTINGS

print("\n📋 VAPID_PUBLIC_KEY:")
print(vapid_settings.get('VAPID_PUBLIC_KEY', 'NO CONFIGURADA')[:50] + '...')

print("\n📋 VAPID_PRIVATE_KEY:")
print(vapid_settings.get('VAPID_PRIVATE_KEY', 'NO CONFIGURADA')[:30] + '...')

print("\n📋 VAPID_ADMIN_EMAIL:")
print(vapid_settings.get('VAPID_ADMIN_EMAIL', 'NO CONFIGURADA'))

print("\n" + "=" * 70)

# Verificar si coinciden con las nuevas
expected_public = "HHFKpkNYiNsS2tlnB4kM26UAH1GCF5rs-ple0NDA8vwF42XtNAAd1SmsHfQOWbo-quzkhlCRi-nX8IM74PyYvQ0"
expected_private = "wP74TyM70vkLcVL3mpbBhIlJMwUagcL-ToY4i_gmz80"

actual_public = vapid_settings.get('VAPID_PUBLIC_KEY', '')
actual_private = vapid_settings.get('VAPID_PRIVATE_KEY', '')

print("\n🔍 VERIFICACIÓN:")
if actual_public == expected_public:
    print("✅ VAPID_PUBLIC_KEY es CORRECTA (nuevas claves)")
else:
    print("❌ VAPID_PUBLIC_KEY NO COINCIDE (claves antiguas o vacías)")
    print(f"   Esperada: {expected_public[:30]}...")
    print(f"   Actual:   {actual_public[:30]}...")

if actual_private == expected_private:
    print("✅ VAPID_PRIVATE_KEY es CORRECTA (nuevas claves)")
else:
    print("❌ VAPID_PRIVATE_KEY NO COINCIDE (claves antiguas o vacías)")
    print(f"   Esperada: {expected_private[:20]}...")
    print(f"   Actual:   {actual_private[:20]}...")

print("\n" + "=" * 70)
