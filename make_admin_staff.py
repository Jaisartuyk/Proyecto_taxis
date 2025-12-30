"""
Script para marcar a un usuario como staff (puede acceder a /admin/)
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import AppUser

# Nombre del usuario a actualizar
username = 'jairo'

try:
    user = AppUser.objects.get(username=username)
    
    print(f"\n📋 Usuario encontrado: {user.username}")
    print(f"   Role: {user.role}")
    print(f"   Organization: {user.organization}")
    print(f"   is_staff (antes): {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    
    # Marcar como staff
    user.is_staff = True
    user.save()
    
    print(f"\n✅ Usuario actualizado exitosamente!")
    print(f"   is_staff (después): {user.is_staff}")
    print(f"\n🎉 {username} ahora puede acceder a /admin/")
    
except AppUser.DoesNotExist:
    print(f"\n❌ Error: Usuario '{username}' no encontrado")
    print("\nUsuarios disponibles:")
    for u in AppUser.objects.all():
        print(f"  - {u.username} (role={u.role}, org={u.organization})")
