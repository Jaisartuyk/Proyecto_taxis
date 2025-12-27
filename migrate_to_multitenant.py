#!/usr/bin/env python
"""
Script de migración para convertir el sistema a multi-tenant.
Crea la organización "De Aquí Pa'llá" y asigna todos los datos existentes.
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import Organization, AppUser, Ride
from django.utils import timezone

def migrate_to_multitenant():
    """
    Migra todos los datos existentes a la organización "De Aquí Pa'llá"
    """
    print("=" * 60)
    print("🚀 MIGRACIÓN A SISTEMA MULTI-TENANT")
    print("=" * 60)
    print()
    
    # Verificar si ya existe la organización
    existing_org = Organization.objects.filter(slug='de-aqui-pa-lla').first()
    if existing_org:
        print(f"⚠️  La organización '{existing_org.name}' ya existe.")
        response = input("¿Deseas continuar y reasignar los datos? (s/n): ")
        if response.lower() != 's':
            print("❌ Migración cancelada.")
            return
        deaquipalla_org = existing_org
    else:
        # Obtener el primer superusuario como owner
        super_admin = AppUser.objects.filter(is_superuser=True).first()
        
        if not super_admin:
            print("❌ ERROR: No se encontró ningún superusuario.")
            print("   Por favor, crea un superusuario primero con:")
            print("   python manage.py createsuperuser")
            return
        
        print(f"👤 Super Admin encontrado: {super_admin.get_full_name()} ({super_admin.username})")
        print()
        
        # Crear la organización "De Aquí Pa'llá"
        print("📝 Creando organización 'De Aquí Pa'llá'...")
        deaquipalla_org = Organization.objects.create(
            name="De Aquí Pa'llá",
            slug="de-aqui-pa-lla",
            description="Cooperativa de taxis De Aquí Pa'llá - Organización principal",
            
            # Colores actuales (dorado y negro)
            primary_color="#FFD700",
            secondary_color="#000000",
            
            # Contacto (ajusta estos valores)
            phone="0999999999",
            email="admin@deaquipalla.com",
            city="Guayaquil",
            country="Ecuador",
            
            # Plan especial (es tuya, no pagas)
            plan="owner",
            status="active",
            max_drivers=999999,  # Sin límite
            monthly_fee=0.00,  # No pagas
            commission_rate=0.00,  # Sin comisión
            
            # Owner
            owner=super_admin,
            
            # Fechas
            subscription_starts_at=timezone.now(),
            created_at=timezone.now()
        )
        print(f"✅ Organización creada: {deaquipalla_org.name}")
        print(f"   - Slug: {deaquipalla_org.slug}")
        print(f"   - Plan: {deaquipalla_org.get_plan_display()}")
        print(f"   - Estado: {deaquipalla_org.get_status_display()}")
        print(f"   - Owner: {deaquipalla_org.owner.get_full_name()}")
        print()
    
    # Asignar todos los usuarios existentes
    print("👥 Asignando usuarios a la organización...")
    users_without_org = AppUser.objects.filter(organization__isnull=True)
    users_count = users_without_org.count()
    
    if users_count > 0:
        users_without_org.update(organization=deaquipalla_org)
        print(f"✅ {users_count} usuarios asignados")
        
        # Mostrar desglose por rol
        customers = AppUser.objects.filter(organization=deaquipalla_org, role='customer').count()
        drivers = AppUser.objects.filter(organization=deaquipalla_org, role='driver').count()
        admins = AppUser.objects.filter(organization=deaquipalla_org, role='admin').count()
        
        print(f"   - Clientes: {customers}")
        print(f"   - Conductores: {drivers}")
        print(f"   - Administradores: {admins}")
    else:
        print("ℹ️  Todos los usuarios ya tienen organización asignada")
    print()
    
    # Aprobar todos los conductores existentes y asignar números de unidad
    print("🚗 Configurando conductores...")
    drivers = AppUser.objects.filter(
        organization=deaquipalla_org,
        role='driver',
        driver_status='pending'
    )
    
    if drivers.exists():
        for i, driver in enumerate(drivers, start=1):
            driver.driver_number = f"{i:03d}"  # 001, 002, 003...
            driver.driver_status = 'approved'
            driver.approved_at = timezone.now()
            driver.approved_by = deaquipalla_org.owner
            driver.save()
            print(f"   ✅ Conductor {driver.get_full_name()} → Unidad {driver.driver_number} (Aprobado)")
    else:
        print("ℹ️  No hay conductores pendientes de aprobación")
    print()
    
    # Asignar todas las carreras existentes
    print("🚕 Asignando carreras a la organización...")
    rides_without_org = Ride.objects.filter(organization__isnull=True)
    rides_count = rides_without_org.count()
    
    if rides_count > 0:
        rides_without_org.update(organization=deaquipalla_org)
        print(f"✅ {rides_count} carreras asignadas")
        
        # Mostrar desglose por estado
        requested = Ride.objects.filter(organization=deaquipalla_org, status='requested').count()
        accepted = Ride.objects.filter(organization=deaquipalla_org, status='accepted').count()
        in_progress = Ride.objects.filter(organization=deaquipalla_org, status='in_progress').count()
        completed = Ride.objects.filter(organization=deaquipalla_org, status='completed').count()
        canceled = Ride.objects.filter(organization=deaquipalla_org, status='canceled').count()
        
        print(f"   - Solicitadas: {requested}")
        print(f"   - Aceptadas: {accepted}")
        print(f"   - En progreso: {in_progress}")
        print(f"   - Completadas: {completed}")
        print(f"   - Canceladas: {canceled}")
    else:
        print("ℹ️  Todas las carreras ya tienen organización asignada")
    print()
    
    # Resumen final
    print("=" * 60)
    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print()
    print(f"📊 Resumen de '{deaquipalla_org.name}':")
    print(f"   - Total usuarios: {deaquipalla_org.users.count()}")
    print(f"   - Total conductores: {deaquipalla_org.get_driver_count()}")
    print(f"   - Total carreras: {deaquipalla_org.rides.count()}")
    print(f"   - Carreras activas: {deaquipalla_org.get_active_rides_count()}")
    print(f"   - Ingresos totales: ${deaquipalla_org.get_total_revenue():.2f}")
    print()
    print("🎉 Tu sistema ahora es multi-tenant!")
    print("🚀 Puedes empezar a agregar más cooperativas.")
    print()

if __name__ == '__main__':
    try:
        migrate_to_multitenant()
    except Exception as e:
        print(f"❌ ERROR durante la migración: {e}")
        import traceback
        traceback.print_exc()
