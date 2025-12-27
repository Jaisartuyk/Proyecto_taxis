"""
Script para crear o verificar superusuario para el panel de administración
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("GESTIÓN DE SUPERUSUARIOS")
print("=" * 60)

# Verificar superusuarios existentes
print("\n1. Verificando superusuarios existentes...")
superusers = User.objects.filter(is_superuser=True)

if superusers.exists():
    print(f"\n✅ Encontrados {superusers.count()} superusuario(s):")
    for user in superusers:
        print(f"   - Username: {user.username}")
        print(f"     Email: {user.email}")
        print(f"     Superuser: {user.is_superuser}")
        print(f"     Staff: {user.is_staff}")
        print(f"     Activo: {user.is_active}")
        print()
else:
    print("\n⚠️  No hay superusuarios creados")

# Preguntar si quiere crear uno nuevo
print("\n2. ¿Deseas crear un nuevo superusuario? (s/n): ", end='')
respuesta = input().lower()

if respuesta == 's':
    print("\n📝 Ingresa los datos del nuevo superusuario:")
    
    username = input("Username: ")
    email = input("Email: ")
    password = input("Password: ")
    
    try:
        # Verificar si el username ya existe
        if User.objects.filter(username=username).exists():
            print(f"\n⚠️  El usuario '{username}' ya existe.")
            print("¿Deseas convertirlo en superusuario? (s/n): ", end='')
            convertir = input().lower()
            
            if convertir == 's':
                user = User.objects.get(username=username)
                user.is_superuser = True
                user.is_staff = True
                user.is_active = True
                if email:
                    user.email = email
                if password:
                    user.set_password(password)
                user.save()
                print(f"\n✅ Usuario '{username}' convertido a superusuario exitosamente!")
        else:
            # Crear nuevo usuario
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            print(f"\n✅ Superusuario '{username}' creado exitosamente!")
        
        print("\n📋 Datos del superusuario:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Activo: {user.is_active}")
        
    except Exception as e:
        print(f"\n❌ Error al crear superusuario: {e}")

# Preguntar si quiere hacer superuser a un usuario existente
print("\n3. ¿Deseas convertir un usuario existente en superusuario? (s/n): ", end='')
respuesta = input().lower()

if respuesta == 's':
    username = input("Username del usuario a convertir: ")
    
    try:
        user = User.objects.get(username=username)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print(f"\n✅ Usuario '{username}' convertido a superusuario exitosamente!")
        print("\n📋 Datos del usuario:")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Superuser: {user.is_superuser}")
        print(f"   Staff: {user.is_staff}")
        print(f"   Activo: {user.is_active}")
        
    except User.DoesNotExist:
        print(f"\n❌ Usuario '{username}' no encontrado")
    except Exception as e:
        print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("RESUMEN FINAL")
print("=" * 60)

# Mostrar todos los superusuarios
superusers = User.objects.filter(is_superuser=True)
if superusers.exists():
    print(f"\n✅ Total de superusuarios: {superusers.count()}")
    for user in superusers:
        print(f"   - {user.username} ({user.email})")
    
    print("\n🚀 Ahora puedes acceder al panel de administración:")
    print("   1. Ve a: https://taxis-deaquipalla.up.railway.app/login/")
    print("   2. Inicia sesión con uno de los superusuarios")
    print("   3. Accede a: https://taxis-deaquipalla.up.railway.app/admin/dashboard/")
else:
    print("\n⚠️  No hay superusuarios creados")
    print("   Ejecuta este script nuevamente y crea uno")

print("\n" + "=" * 60)
