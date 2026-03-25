#!/usr/bin/env python
"""
Script para verificar organizaciones y conductores en el sistema multi-tenant
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import AppUser, Organization

print("=" * 80)
print("🏢 VERIFICACIÓN DE ORGANIZACIONES Y CONDUCTORES")
print("=" * 80)

# Listar todas las organizaciones
print("\n📋 ORGANIZACIONES:")
organizations = Organization.objects.all()
for org in organizations:
    print(f"  - {org.name} (ID: {org.id})")

# Listar todos los administradores
print("\n👔 ADMINISTRADORES:")
admins = AppUser.objects.filter(role='admin')
for admin in admins:
    org_name = admin.organization.name if admin.organization else "❌ SIN ORGANIZACIÓN"
    print(f"  - {admin.username} (ID: {admin.id}) → Org: {org_name}")

# Listar todos los conductores
print("\n🚗 CONDUCTORES:")
drivers = AppUser.objects.filter(role='driver')
for driver in drivers:
    org_name = driver.organization.name if driver.organization else "❌ SIN ORGANIZACIÓN"
    full_name = driver.get_full_name() or driver.username
    print(f"  - {full_name} (@{driver.username}, ID: {driver.id}) → Org: {org_name}")

# Verificar específicamente Tonymz y carlos
print("\n" + "=" * 80)
print("🔍 VERIFICACIÓN ESPECÍFICA:")
print("=" * 80)

try:
    tonymz = AppUser.objects.get(username='Tonymz')
    print(f"\n✅ Tonymz encontrado:")
    print(f"   - ID: {tonymz.id}")
    print(f"   - Nombre: {tonymz.get_full_name()}")
    print(f"   - Rol: {tonymz.role}")
    print(f"   - Organización: {tonymz.organization.name if tonymz.organization else '❌ SIN ORGANIZACIÓN'}")
except AppUser.DoesNotExist:
    print("\n❌ Tonymz NO encontrado en la base de datos")

try:
    carlos = AppUser.objects.get(username='carlos')
    print(f"\n✅ Carlos encontrado:")
    print(f"   - ID: {carlos.id}")
    print(f"   - Nombre: {carlos.get_full_name()}")
    print(f"   - Rol: {carlos.role}")
    print(f"   - Organización: {carlos.organization.name if carlos.organization else '❌ SIN ORGANIZACIÓN'}")
except AppUser.DoesNotExist:
    print("\n❌ Carlos NO encontrado en la base de datos")

try:
    jairo = AppUser.objects.get(id=14)
    print(f"\n✅ Usuario 14 (jairo) encontrado:")
    print(f"   - Username: {jairo.username}")
    print(f"   - Nombre: {jairo.get_full_name()}")
    print(f"   - Rol: {jairo.role}")
    print(f"   - Organización: {jairo.organization.name if jairo.organization else '❌ SIN ORGANIZACIÓN'}")
    
    # Verificar qué conductores puede ver jairo
    if jairo.is_superuser:
        visible_drivers = AppUser.objects.filter(role='driver')
        print(f"\n   📊 Como SUPERADMIN, puede ver TODOS los {visible_drivers.count()} conductores")
    elif jairo.role == 'admin' and jairo.organization:
        visible_drivers = AppUser.objects.filter(role='driver', organization=jairo.organization)
        print(f"\n   📊 Como ADMIN de '{jairo.organization.name}', puede ver {visible_drivers.count()} conductores:")
        for driver in visible_drivers:
            print(f"      - {driver.get_full_name()} (@{driver.username})")
    else:
        print(f"\n   ⚠️ No puede ver conductores (sin organización)")
        
except AppUser.DoesNotExist:
    print("\n❌ Usuario 14 NO encontrado")

print("\n" + "=" * 80)
