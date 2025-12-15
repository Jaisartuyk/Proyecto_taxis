"""
Script para probar que las notificaciones push funcionan correctamente
"""
import requests
import sys

BASE_URL = "https://taxis-deaquipalla.up.railway.app"

def test_vapid_keys():
    """Verifica que las claves VAPID estén configuradas"""
    print("\n🔑 Verificando claves VAPID...")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        
        # Buscar la meta tag de VAPID
        if 'vapid-public-key' in response.text:
            # Extraer el contenido
            start = response.text.find('name="vapid-public-key" content="') + 34
            end = response.text.find('"', start)
            vapid_key = response.text[start:end]
            
            if vapid_key and len(vapid_key) > 50:
                print(f"✅ Clave VAPID pública configurada")
                print(f"   Longitud: {len(vapid_key)} caracteres")
                print(f"   Primeros 20 caracteres: {vapid_key[:20]}...")
                return True
            else:
                print("❌ Clave VAPID está vacía o muy corta")
                return False
        else:
            print("❌ No se encontró la meta tag de VAPID")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_service_worker():
    """Verifica que el Service Worker esté disponible"""
    print("\n🔧 Verificando Service Worker...")
    
    try:
        response = requests.get(f"{BASE_URL}/service-worker.js")
        if response.status_code == 200:
            print(f"✅ Service Worker disponible ({len(response.text)} bytes)")
            return True
        else:
            print(f"❌ Service Worker no disponible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_notifications_js():
    """Verifica que notifications-v4.js esté disponible"""
    print("\n📱 Verificando notifications-v4.js...")
    
    try:
        response = requests.get(f"{BASE_URL}/static/js/notifications-v4.js")
        if response.status_code == 200:
            print(f"✅ notifications-v4.js disponible ({len(response.text)} bytes)")
            
            # Verificar que tenga el código correcto
            if "'/service-worker.js'" in response.text:
                print("✅ Registra Service Worker desde la ruta correcta")
                return True
            else:
                print("⚠️  Archivo encontrado pero tiene ruta incorrecta")
                return False
        else:
            print(f"❌ notifications-v4.js no disponible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_api_endpoint():
    """Verifica que el endpoint de suscripción esté disponible"""
    print("\n🌐 Verificando endpoint de API...")
    
    try:
        # Solo verificar que el endpoint responde (no hacer POST sin datos válidos)
        response = requests.get(f"{BASE_URL}/api/webpush/subscribe/")
        
        # El endpoint debería devolver 405 (Method Not Allowed) para GET
        # o requerir autenticación (401/403)
        if response.status_code in [405, 401, 403]:
            print(f"✅ Endpoint de suscripción está activo")
            return True
        elif response.status_code == 404:
            print(f"❌ Endpoint no encontrado: {response.status_code}")
            return False
        else:
            print(f"⚠️  Endpoint responde con código: {response.status_code}")
            return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    print("=" * 70)
    print("🔍 PRUEBA FINAL DE NOTIFICACIONES PUSH")
    print("=" * 70)
    
    results = []
    
    results.append(("Claves VAPID", test_vapid_keys()))
    results.append(("Service Worker", test_service_worker()))
    results.append(("Notifications JS", test_notifications_js()))
    results.append(("API Endpoint", test_api_endpoint()))
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE RESULTADOS")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ OK" if result else "❌ FALLO"
        print(f"{status:10} - {name}")
    
    all_ok = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_ok:
        print("✅ ¡SISTEMA LISTO! Las notificaciones deberían funcionar")
        print("\n📋 PRÓXIMOS PASOS:")
        print("   1. Abre la app en tu móvil")
        print("   2. Ve a /test-notifications/")
        print("   3. Haz clic en 'Solicitar Permiso'")
        print("   4. Haz clic en 'Suscribirse a Notificaciones'")
        print("   5. Haz clic en 'Enviar Notificación de Prueba'")
        print("\n   O desde el dashboard del conductor:")
        print("   - Panel de notificaciones en la parte superior")
        print("   - Botón 'Activar Notificaciones'")
        return 0
    else:
        print("❌ Hay problemas que resolver antes de usar notificaciones")
        return 1

if __name__ == "__main__":
    sys.exit(main())
