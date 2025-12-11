#!/usr/bin/env python
"""
Script de diagnóstico para ejecutar EN Railway
Verifica la estructura de archivos estáticos después de collectstatic
"""
import os
import sys
from pathlib import Path

print("=" * 80)
print("🔍 DIAGNÓSTICO DE ARCHIVOS ESTÁTICOS EN RAILWAY")
print("=" * 80)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')

try:
    import django
    django.setup()
    from django.conf import settings
    
    print(f"\n✅ Django configurado correctamente")
    print(f"📂 BASE_DIR: {settings.BASE_DIR}")
    print(f"📂 STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"🌐 STATIC_URL: {settings.STATIC_URL}")
    print(f"⚙️  STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    print(f"\n📁 STATICFILES_DIRS:")
    for i, dir_path in enumerate(settings.STATICFILES_DIRS, 1):
        exists = "✅" if os.path.exists(dir_path) else "❌"
        print(f"  {i}. {exists} {dir_path}")
    
    # Verificar archivos en STATIC_ROOT (donde collectstatic copia los archivos)
    print(f"\n📂 ARCHIVOS EN STATIC_ROOT/js/:")
    static_root_js = Path(settings.STATIC_ROOT) / 'js'
    if static_root_js.exists():
        js_files = sorted(static_root_js.glob('*.js'))
        if js_files:
            for js_file in js_files:
                size = js_file.stat().st_size
                print(f"  ✅ {js_file.name} ({size} bytes)")
        else:
            print(f"  ❌ No hay archivos .js en {static_root_js}")
    else:
        print(f"  ❌ El directorio {static_root_js} no existe")
    
    # Verificar archivos en source (antes de collectstatic)
    print(f"\n📂 ARCHIVOS EN static/js/ (SOURCE):")
    source_js = Path(settings.BASE_DIR) / 'static' / 'js'
    if source_js.exists():
        js_files = sorted(source_js.glob('*.js'))
        if js_files:
            for js_file in js_files:
                size = js_file.stat().st_size
                print(f"  ✅ {js_file.name} ({size} bytes)")
        else:
            print(f"  ❌ No hay archivos .js en {source_js}")
    else:
        print(f"  ❌ El directorio {source_js} no existe")
    
    # Verificar archivos críticos
    print(f"\n🎯 ARCHIVOS CRÍTICOS:")
    critical_files = [
        'static/js/notifications-v5.js',
        'static/js/badge-manager.js',
        'static/js/chat-badge.js',
    ]
    
    for file_path in critical_files:
        # Verificar en source
        source_path = Path(settings.BASE_DIR) / file_path
        source_exists = "✅" if source_path.exists() else "❌"
        
        # Verificar en STATIC_ROOT
        dest_path = Path(settings.STATIC_ROOT) / file_path.replace('static/', '')
        dest_exists = "✅" if dest_path.exists() else "❌"
        
        print(f"  {file_path}")
        print(f"    Source: {source_exists} | Collected: {dest_exists}")
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
