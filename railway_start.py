#!/usr/bin/env python
"""
Script de despliegue para Railway
Ejecuta collectstatic con logging visible y luego inicia el servidor
"""
import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"[EJECUTANDO] {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(command, shell=True, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n[ERROR] Fallo en: {description}")
        sys.exit(result.returncode)
    else:
        print(f"\n[OK] {description} - Completado")
    
    return result.returncode

if __name__ == "__main__":
    print("\n" + "="*60)
    print("INICIANDO DESPLIEGUE EN RAILWAY")
    print("="*60 + "\n")
    
    # 1. Mostrar migraciones pendientes (solo visualización, no bloquea)
    print("\n" + "="*60)
    print("VERIFICANDO MIGRACIONES PENDIENTES")
    print("="*60 + "\n")
    try:
        subprocess.run(
            "python manage.py showmigrations --list | grep '\\[ \\]' || echo 'No hay migraciones pendientes'",
            shell=True,
            capture_output=False,
            text=True
        )
    except Exception as e:
        print(f"Nota: No se pudieron listar migraciones pendientes: {e}")
    
    # 2. Migraciones (PRIMERO, antes de collectstatic)
    # Esto asegura que la base de datos esté actualizada antes de servir archivos estáticos
    print("\n" + "="*60)
    print("APLICANDO MIGRACIONES DE BASE DE DATOS")
    print("="*60 + "\n")
    print("[INFO] Este paso actualiza la estructura de la base de datos")
    print("[INFO] Se ejecuta automáticamente en cada despliegue\n")
    
    run_command(
        # --noinput: no pide confirmación (automático)
        # --verbosity 1: muestra información básica sin saturar logs
        "python manage.py migrate --noinput --verbosity 1",
        "Aplicando migraciones de base de datos (AUTOMATICO)"
    )
    
    # Verificar estado de migraciones después de aplicarlas
    print("\n" + "="*60)
    print("VERIFICANDO ESTADO DE MIGRACIONES")
    print("="*60 + "\n")
    try:
        result = subprocess.run(
            "python manage.py showmigrations --list",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(result.stdout)
            # Contar migraciones aplicadas
            applied = result.stdout.count('[X]')
            pending = result.stdout.count('[ ]')
            print(f"\n[INFO] Migraciones aplicadas: {applied}")
            if pending > 0:
                print(f"[WARNING] Migraciones pendientes: {pending}")
            else:
                print(f"[OK] Todas las migraciones están aplicadas")
        else:
            print(f"[WARNING] Error ejecutando showmigrations: {result.stderr}")
        print("\n[OK] Verificación de migraciones completada")
    except Exception as e:
        print(f"[WARNING] No se pudo verificar migraciones: {e}")
    
    # 3. Verificar archivos estáticos y configuración de WhiteNoise
    # NOTA: collectstatic ya se ejecuta en el Pre-deploy Command (railway_pre_deploy.py)
    # No es necesario ejecutarlo aquí para evitar duplicación
    import os
    from django.conf import settings
    
    staticfiles_dir = settings.STATIC_ROOT
    print(f"\n[INFO] Verificando archivos estáticos en: {staticfiles_dir}")
    print(f"[INFO] STATIC_URL: {settings.STATIC_URL}")
    print(f"[INFO] STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    # Verificar configuración de WhiteNoise
    if hasattr(settings, 'WHITENOISE_ROOT'):
        print(f"[INFO] WHITENOISE_ROOT: {settings.WHITENOISE_ROOT}")
    if hasattr(settings, 'WHITENOISE_USE_FINDERS'):
        print(f"[INFO] WHITENOISE_USE_FINDERS: {settings.WHITENOISE_USE_FINDERS}")
    
    if os.path.exists(staticfiles_dir) and os.listdir(staticfiles_dir):
        print(f"[INFO] Directorio staticfiles existe y tiene contenido")
        
        # Verificar que los archivos críticos estén presentes
        critical_files = [
            'css/floating-audio-button.css',
            'js/audio-floating-button.js',
        ]
        all_ok = True
        for file_path in critical_files:
            full_path = os.path.join(staticfiles_dir, file_path)
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"  [OK] {file_path} - {size} bytes")
            else:
                print(f"  [ERROR] {file_path} - NO ENCONTRADO en {full_path}")
                all_ok = False
        
        # Listar algunos archivos en staticfiles para verificar
        print(f"\n[INFO] Archivos en staticfiles (primeros 10):")
        count = 0
        for root, dirs, files in os.walk(staticfiles_dir):
            for file in files[:10]:
                rel_path = os.path.relpath(os.path.join(root, file), staticfiles_dir)
                print(f"  - {rel_path}")
                count += 1
                if count >= 10:
                    break
            if count >= 10:
                break
        
        if all_ok:
            print(f"\n[INFO] Archivos críticos verificados")
            print(f"[INFO] WhiteNoise debería servir desde: {staticfiles_dir}")
        else:
            print(f"\n[WARNING] Algunos archivos críticos faltan")
    else:
        print(f"\n[WARNING] Directorio staticfiles no existe o está vacío")
        print(f"[INFO] Ejecutando collectstatic...")
        run_command(
            "python manage.py collectstatic --noinput --verbosity 0 --ignore cloudinary",
            "Recopilando archivos estaticos (silencioso, ignorando Cloudinary)"
        )
    
    # 4. Iniciar servidor
    print("\n" + "="*60)
    print("INICIANDO SERVIDOR DAPHNE")
    print("="*60 + "\n")
    
    port = os.environ.get('PORT', '8080')
    os.execvp('daphne', ['daphne', '-b', '0.0.0.0', '-p', port, 'taxi_project.asgi:application'])
