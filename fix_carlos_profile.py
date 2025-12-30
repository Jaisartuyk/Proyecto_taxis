"""
Script para verificar y completar el perfil de carlos
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import AppUser, Taxi

# Obtener usuario carlos
try:
    carlos = AppUser.objects.get(username='carlos')
    print(f"✅ Usuario encontrado: {carlos.username}")
    print(f"   - Email: {carlos.email}")
    print(f"   - Teléfono: {carlos.phone_number}")
    print(f"   - Nombre: {carlos.first_name} {carlos.last_name}")
    print(f"   - Role: {carlos.role}")
    
    # Actualizar email si está vacío
    if not carlos.email:
        carlos.email = "carlos@deaquipalla.com"
        carlos.save()
        print(f"   ✅ Email actualizado: {carlos.email}")
    
    # Verificar si tiene taxi
    if carlos.role == 'driver':
        try:
            taxi = carlos.taxi
            print(f"\n✅ Taxi encontrado:")
            print(f"   - Placa: {taxi.plate_number}")
            print(f"   - Modelo: {taxi.car_model}")
            print(f"   - Color: {taxi.car_color}")
            print(f"   - Año: {taxi.car_year}")
        except Taxi.DoesNotExist:
            print(f"\n❌ No tiene taxi registrado")
            print(f"   Creando taxi para carlos...")
            
            taxi = Taxi.objects.create(
                user=carlos,
                plate_number="ABC-123",
                car_model="Toyota Corolla",
                car_color="Blanco",
                car_year=2020,
                is_active=True
            )
            print(f"   ✅ Taxi creado exitosamente")
            print(f"   - Placa: {taxi.plate_number}")
            print(f"   - Modelo: {taxi.car_model}")
            print(f"   - Color: {taxi.car_color}")
            print(f"   - Año: {taxi.car_year}")
    
    print(f"\n✅ Perfil de carlos completado exitosamente")
    
except AppUser.DoesNotExist:
    print(f"❌ Usuario 'carlos' no encontrado")
