#!/usr/bin/env python3
"""
Script de despliegue para Railway
Configura automáticamente PostgreSQL y Redis
"""
import os
import subprocess
import sys

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completado")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    """Función principal de despliegue"""
    print("🚀 Iniciando despliegue para Railway...")
    
    # 1. Instalar dependencias
    if not run_command("pip install -r requirements.txt", "Instalando dependencias"):
        return False
    
    # 2. Configurar variables de entorno para Railway
    print("🔧 Configurando variables de entorno...")
    
    # Verificar si estamos en Railway
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        print("✅ Detectado entorno de Railway")
        
        # Configurar Django para usar settings_railway
        os.environ['DJANGO_SETTINGS_MODULE'] = 'taxi_project.settings_railway'
        
        # Verificar variables de entorno requeridas
        required_vars = ['DATABASE_URL', 'REDIS_URL', 'SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            print(f"⚠️ Variables de entorno faltantes: {', '.join(missing_vars)}")
            print("💡 Asegúrate de configurar estas variables en Railway")
        else:
            print("✅ Todas las variables de entorno están configuradas")
    else:
        print("⚠️ No se detectó entorno de Railway, usando configuración local")
    
    # 3. Ejecutar migraciones
    if not run_command("python manage.py makemigrations", "Creando migraciones"):
        return False
    
    if not run_command("python manage.py migrate", "Ejecutando migraciones"):
        return False
    
    # 4. Recopilar archivos estáticos
    if not run_command("python manage.py collectstatic --noinput", "Recopilando archivos estáticos"):
        return False
    
    # 5. Crear superusuario si no existe
    print("👤 Verificando superusuario...")
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            print("💡 No hay superusuario. Crea uno con: python manage.py createsuperuser")
        else:
            print("✅ Superusuario existe")
    except Exception as e:
        print(f"⚠️ No se pudo verificar superusuario: {e}")
    
    # 6. Verificar configuración de base de datos
    print("🗄️ Verificando conexión a base de datos...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Conexión a base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False
    
    # 7. Verificar configuración de Redis
    print("🔴 Verificando conexión a Redis...")
    try:
        import redis
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Conexión a Redis exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a Redis: {e}")
        return False
    
    print("🎉 ¡Despliegue completado exitosamente!")
    print("\n📋 Próximos pasos:")
    print("1. Configura las variables de entorno en Railway:")
    print("   - DATABASE_URL (PostgreSQL)")
    print("   - REDIS_URL (Redis)")
    print("   - SECRET_KEY")
    print("   - WASENDER_TOKEN")
    print("   - GOOGLE_API_KEY")
    print("   - TELEGRAM_BOT_TOKEN")
    print("2. Configura el webhook de WhatsApp en WASender")
    print("3. Prueba la aplicación en tu dominio de Railway")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
