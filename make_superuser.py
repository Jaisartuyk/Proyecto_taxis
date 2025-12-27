"""
Script para convertir un usuario en superuser
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("CONVERTIR USUARIO EN SUPERUSER")
print("=" * 60)

# Buscar el usuario admin
username = input("\nIngresa el username del usuario a convertir en superuser: ")

try:
    user = User.objects.get(username=username)
    
    print(f"\n📋 Usuario encontrado:")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Role: {user.role}")
    print(f"   Superuser: {user.is_superuser}")
    print(f"   Staff: {user.is_staff}")
    print(f"   Organización: {user.organization.name if user.organization else 'Ninguna'}")
    
    if user.is_superuser:
        print(f"\n✅ El usuario '{username}' YA ES superuser")
    else:
        print(f"\n⚠️  El usuario '{username}' NO es superuser")
        confirm = input("¿Deseas convertirlo en superuser? (s/n): ")
        
        if confirm.lower() == 's':
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            print(f"\n✅ Usuario '{username}' convertido a superuser exitosamente!")
            print("\n📋 Datos actualizados:")
            print(f"   Superuser: {user.is_superuser}")
            print(f"   Staff: {user.is_staff}")
            print("\n🚀 Ahora puedes acceder al panel en:")
            print("   https://taxis-deaquipalla.up.railway.app/admin/dashboard/")
        else:
            print("\n❌ Operación cancelada")
            
except User.DoesNotExist:
    print(f"\n❌ Usuario '{username}' no encontrado")
    print("\nUsuarios disponibles:")
    for u in User.objects.all()[:10]:
        print(f"   - {u.username} (Role: {u.role}, Superuser: {u.is_superuser})")

print("\n" + "=" * 60)
