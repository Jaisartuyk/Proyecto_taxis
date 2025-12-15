#!/usr/bin/env python
"""
Script para verificar configuración de archivos estáticos en Railway
"""
import os
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

import django
django.setup()

from django.conf import settings
from pathlib import Path

print("=" * 80)
print("🔍 VERIFICACIÓN DE ARCHIVOS ESTÁTICOS")
print("=" * 80)

print(f"\n📂 BASE_DIR: {settings.BASE_DIR}")
print(f"📂 STATIC_ROOT: {settings.STATIC_ROOT}")
print(f"🌐 STATIC_URL: {settings.STATIC_URL}")

print(f"\n📁 STATICFILES_DIRS:")
for i, dir_path in enumerate(settings.STATICFILES_DIRS, 1):
    exists = os.path.exists(dir_path)
    status = "✅" if exists else "❌"
    print(f"  {i}. {status} {dir_path}")
    
    if exists and i == 1:  # Verificar el primer directorio (static/)
        js_dir = os.path.join(dir_path, 'js')
        if os.path.exists(js_dir):
            print(f"\n     📂 Archivos en {js_dir}:")
            for file in sorted(os.listdir(js_dir)):
                if file.endswith('.js'):
                    file_path = os.path.join(js_dir, file)
                    size = os.path.getsize(file_path)
                    print(f"        - {file} ({size} bytes)")

print(f"\n⚙️  STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")

# Verificar archivos críticos
print(f"\n🎯 VERIFICACIÓN DE ARCHIVOS CRÍTICOS:")
critical_files = [
    'static/js/notifications-v5.js',
    'static/js/badge-manager.js',
    'static/js/chat-badge.js',
    'static/js/service-worker.js',
]

for file_path in critical_files:
    full_path = os.path.join(settings.BASE_DIR, file_path)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f"  {status} {file_path}")
    if exists:
        size = os.path.getsize(full_path)
        print(f"     Tamaño: {size} bytes")

print("\n" + "=" * 80)
