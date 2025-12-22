#!/usr/bin/env python
"""Script temporal para ejecutar migraciones"""
import os
import sys
import subprocess

# Cambiar al directorio del proyecto
project_dir = r'C:\Users\H P\OneDrive\Imágenes\virtual\proyecto_completo'
os.chdir(project_dir)

print(f"Directorio actual: {os.getcwd()}")
print(f"manage.py existe: {os.path.exists('manage.py')}")

# Ejecutar makemigrations
print("\n=== Ejecutando makemigrations ===")
result1 = subprocess.run([sys.executable, 'manage.py', 'makemigrations'], 
                        capture_output=True, text=True, encoding='utf-8')
print(result1.stdout)
if result1.stderr:
    print("Errores:", result1.stderr)
print(f"Código de salida: {result1.returncode}")

# Ejecutar migrate
if result1.returncode == 0:
    print("\n=== Ejecutando migrate ===")
    result2 = subprocess.run([sys.executable, 'manage.py', 'migrate'], 
                            capture_output=True, text=True, encoding='utf-8')
    print(result2.stdout)
    if result2.stderr:
        print("Errores:", result2.stderr)
    print(f"Código de salida: {result2.returncode}")

