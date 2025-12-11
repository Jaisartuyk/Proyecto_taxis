#!/usr/bin/env python3
"""
Script para verificar que Railway tenga los archivos actualizados
"""

import requests

print("🔍 VERIFICACIÓN DE ARCHIVOS EN RAILWAY")
print("=" * 70)

base_url = "https://taxis-deaquipalla.up.railway.app"

# Lista de archivos a verificar
files_to_check = [
    "/service-worker.js",
    "/static/js/notifications.js?v=3.0",
]

for file_path in files_to_check:
    url = base_url + file_path
    print(f"\n📄 Verificando: {file_path}")
    print("-" * 70)
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Estado: {response.status_code} OK")
            
            # Verificar contenido relevante
            content = response.text
            
            if "service-worker.js" in file_path:
                # Verificar que tenga las funciones correctas
                if "addEventListener('push'" in content:
                    print("✅ Contiene event listener de push")
                else:
                    print("⚠️  NO contiene event listener de push")
                    
                if "showNotification" in content:
                    print("✅ Contiene función showNotification")
                else:
                    print("⚠️  NO contiene función showNotification")
                    
            elif "notifications.js" in file_path:
                # Verificar que registre desde la raíz
                if "'/service-worker.js'" in content or '"/service-worker.js"' in content:
                    print("✅ Registra Service Worker desde /service-worker.js")
                else:
                    print("❌ NO registra Service Worker desde /service-worker.js")
                    
                if "/static/js/service-worker.js" in content:
                    print("❌ ERROR: Aún contiene /static/js/service-worker.js")
                else:
                    print("✅ NO contiene /static/js/service-worker.js")
            
            print(f"📊 Tamaño: {len(content)} bytes")
            
        else:
            print(f"❌ Estado: {response.status_code}")
            print(f"   Error: {response.reason}")
            
    except Exception as e:
        print(f"❌ Error al verificar: {e}")

print("\n" + "=" * 70)
print("✅ Verificación completada")
print("\n💡 Si los archivos NO están actualizados en Railway:")
print("   1. Ve a Railway → Deployments")
print("   2. Verifica que el último despliegue haya terminado")
print("   3. Si aún no termina, espera unos minutos más")
print("   4. Si ya terminó pero los archivos están mal, fuerza un redespliegue")
