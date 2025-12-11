#!/usr/bin/env python
"""
Script para verificar que los archivos estáticos se sirven correctamente en Railway
"""
import requests
import sys

BASE_URL = "https://taxis-deaquipalla.up.railway.app"

# Archivos críticos que deben estar disponibles
CRITICAL_FILES = [
    '/static/js/notifications-v5.js',
    '/static/js/badge-manager.js',
    '/static/js/chat-badge.js',
    '/static/js/service-worker.js',
    '/static/js/app.js',
    '/static/manifest.json',
]

print("=" * 80)
print("🔍 VERIFICANDO ARCHIVOS ESTÁTICOS EN RAILWAY")
print("=" * 80)
print(f"🌐 URL Base: {BASE_URL}\n")

all_ok = True
for file_path in CRITICAL_FILES:
    url = BASE_URL + file_path
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            # Intentar obtener el tamaño del archivo
            size = response.headers.get('Content-Length', 'desconocido')
            encoding = response.headers.get('Content-Encoding', '')
            encoding_info = f" ({encoding})" if encoding else ""
            print(f"✅ {file_path}")
            print(f"   Status: {response.status_code} | Tamaño: {size} bytes{encoding_info}")
        else:
            print(f"❌ {file_path}")
            print(f"   Status: {response.status_code}")
            all_ok = False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {file_path}")
        print(f"   Error: {str(e)}")
        all_ok = False
    
    print()

print("=" * 80)
if all_ok:
    print("✅ TODOS LOS ARCHIVOS ESTÁN DISPONIBLES")
else:
    print("❌ ALGUNOS ARCHIVOS NO ESTÁN DISPONIBLES")
print("=" * 80)

sys.exit(0 if all_ok else 1)
