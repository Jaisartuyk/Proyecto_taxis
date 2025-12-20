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
    port = os.environ.get('PORT', '8080')
    os.execvp('daphne', ['daphne', '-b', '0.0.0.0', '-p', port, 'taxi_project.asgi:application'])
