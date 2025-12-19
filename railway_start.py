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
    run_command(
        # --noinput: no pide confirmación (automático)
        # --verbosity 1: muestra información básica sin saturar logs
        "python manage.py migrate --noinput --verbosity 1",
        "Aplicando migraciones de base de datos (AUTOMATICO)"
    )
    
    # 3. Collectstatic (DESPUES de migraciones)
    # NOTA: No usamos --clear porque causa conflictos con WhiteNoise al intentar comprimir archivos eliminados
    # Django sobrescribirá automáticamente los archivos que han cambiado
    run_command(
        # IMPORTANTE (Railway): verbosity 0 para evitar rate limit de logs (500 logs/s)
        # --noinput: no pide confirmación
        # --ignore cloudinary: ignora archivos de Cloudinary (se sirven desde su CDN)
        # Sin --clear: evita conflictos con WhiteNoise durante la compresión
        "python manage.py collectstatic --noinput --verbosity 0 --ignore cloudinary",
        "Recopilando archivos estaticos (silencioso, ignorando Cloudinary)"
    )
    
    # 4. Iniciar servidor
    print("\n" + "="*60)
    print("INICIANDO SERVIDOR DAPHNE")
    print("="*60 + "\n")
    
    port = os.environ.get('PORT', '8080')
    os.execvp('daphne', ['daphne', '-b', '0.0.0.0', '-p', port, 'taxi_project.asgi:application'])
