#!/usr/bin/env python
"""
Script de pre-deploy para Railway
Ejecuta collectstatic de forma segura sin causar conflictos con WhiteNoise
"""
import os
import sys
import subprocess

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRE-DEPLOY: COLECTANDO ARCHIVOS ESTATICOS")
    print("="*60 + "\n")
    
    # Ejecutar collectstatic SIN --clear para evitar conflictos con WhiteNoise
    # Django sobrescribirá automáticamente los archivos que han cambiado
    result = subprocess.run(
        [
            "python", "manage.py", "collectstatic",
            "--noinput",
            "--verbosity", "0",
            "--ignore", "cloudinary"
        ],
        capture_output=False,
        text=True
    )
    
    if result.returncode != 0:
        print(f"\n[ERROR] collectstatic fallo con codigo {result.returncode}")
        sys.exit(result.returncode)
    else:
        print("\n[OK] Archivos estaticos recolectados correctamente")
        sys.exit(0)

