#!/usr/bin/env python
"""
Script para verificar taxis y ubicaciones de conductores
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import AppUser, Taxi

print("=" * 80)
print("🚕 VERIFICACIÓN DE TAXIS Y UBICACIONES")
print("=" * 80)

# Verificar conductores específicos
conductores = ['carlos', 'Tonymz']

for username in conductores:
    try:
        user = AppUser.objects.get(username=username)
        print(f"\n✅ {user.get_full_name()} (@{username}, ID: {user.id})")
        
        # Verificar si tiene taxi asociado
        try:
            taxi = user.taxi
            print(f"   🚗 Taxi asociado:")
            print(f"      - ID: {taxi.id}")
            print(f"      - Placa: {taxi.plate_number}")
            print(f"      - Latitud: {taxi.latitude}")
            print(f"      - Longitud: {taxi.longitude}")
            
            if taxi.latitude and taxi.longitude:
                print(f"      ✅ TIENE UBICACIÓN GUARDADA")
            else:
                print(f"      ❌ NO TIENE UBICACIÓN GUARDADA")
                
        except Taxi.DoesNotExist:
            print(f"   ❌ NO tiene taxi asociado")
            
        # Verificar ubicación en AppUser
        if hasattr(user, 'last_latitude') and hasattr(user, 'last_longitude'):
            if user.last_latitude and user.last_longitude:
                print(f"   📍 Ubicación en AppUser: ({user.last_latitude}, {user.last_longitude})")
            else:
                print(f"   ⚠️ Sin ubicación en AppUser")
                
    except AppUser.DoesNotExist:
        print(f"\n❌ {username} NO encontrado")

# Listar todos los taxis con ubicación
print("\n" + "=" * 80)
print("📍 TODOS LOS TAXIS CON UBICACIÓN:")
print("=" * 80)

taxis_with_location = Taxi.objects.exclude(latitude__isnull=True).exclude(longitude__isnull=True)
print(f"\nTotal: {taxis_with_location.count()} taxis con ubicación guardada\n")

for taxi in taxis_with_location:
    driver_name = taxi.driver.get_full_name() if taxi.driver else "Sin conductor"
    driver_username = taxi.driver.username if taxi.driver else "N/A"
    print(f"  - {driver_name} (@{driver_username})")
    print(f"    Ubicación: ({taxi.latitude}, {taxi.longitude})")
    print(f"    Placa: {taxi.plate_number}")
    print()

print("=" * 80)
