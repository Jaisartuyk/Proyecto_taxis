import requests
import sys

# URL de tu aplicación en Railway
BASE_URL = "https://taxis-deaquipalla.up.railway.app"

def verificar_archivo(url, verificaciones):
    """Verifica que un archivo contenga o no contenga ciertas cadenas"""
    print(f"\n📄 Verificando: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ Estado: {response.status_code} {response.reason}")
        
        if response.status_code == 200:
            contenido = response.text
            print(f"📊 Tamaño: {len(contenido)} bytes")
            
            # Ejecutar todas las verificaciones
            errores = []
            for verificacion in verificaciones:
                texto_buscar = verificacion['texto']
                debe_existir = verificacion.get('debe_existir', True)
                
                existe = texto_buscar in contenido
                
                if debe_existir:
                    if existe:
                        print(f"✅ Contiene {verificacion['nombre']}")
                    else:
                        print(f"❌ NO contiene {verificacion['nombre']}")
                        errores.append(f"Falta: {verificacion['nombre']}")
                else:
                    if not existe:
                        print(f"✅ NO contiene {verificacion['nombre']} (correcto)")
                    else:
                        print(f"❌ ERROR: Aún contiene {verificacion['nombre']}")
                        errores.append(f"Todavía tiene: {verificacion['nombre']}")
            
            return len(errores) == 0, errores
        else:
            return False, [f"Error HTTP: {response.status_code}"]
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False, [str(e)]

def main():
    print("🔍 Verificación de archivos en Railway")
    print("=" * 60)
    
    archivos = [
        {
            'url': f"{BASE_URL}/service-worker.js",
            'verificaciones': [
                {'nombre': 'event listener de push', 'texto': "self.addEventListener('push'"},
                {'nombre': 'función showNotification', 'texto': 'showNotification'},
            ]
        },
        {
            'url': f"{BASE_URL}/static/js/notifications-v4.js",
            'verificaciones': [
                {'nombre': 'versión 4.0', 'texto': 'v4.0'},
                {'nombre': 'registro desde /service-worker.js', 'texto': "'/service-worker.js'"},
                {'nombre': 'scope raíz', 'texto': "scope: '/'"},
                {'nombre': 'ruta incorrecta /static/js/service-worker.js', 'texto': "'/static/js/service-worker.js'", 'debe_existir': False},
            ]
        }
    ]
    
    todos_ok = True
    for archivo in archivos:
        ok, errores = verificar_archivo(archivo['url'], archivo['verificaciones'])
        if not ok:
            todos_ok = False
            print("\n⚠️  Errores encontrados:")
            for error in errores:
                print(f"   - {error}")
    
    print("\n" + "=" * 60)
    if todos_ok:
        print("✅ ¡Todos los archivos están correctos!")
        print("\n📋 SIGUIENTE PASO:")
        print("   Actualizar las variables de entorno VAPID en Railway:")
        print("   VAPID_PUBLIC_KEY=BLeT-yBd3CYdP12b36skHIjliCXKS9iN69NPD0akxN6jkuDCSONQQUqnPvNy71IIDkaZ_XJnO-pz6TkR8VGPXUA")
        print("   VAPID_PRIVATE_KEY=MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgOT9i-uOVE15UqRodHpqQwEMR-8l65sxH8jJzhr9U2C-hRANCAAS3k_sgXdwmHT9dm9-rJByI5YglykvYjevTTw9GpMTeo5LgwkjjUEFKpz7zcu9SCA5Gmf1yZzvqc-k5EfFRj11A")
        return 0
    else:
        print("❌ Algunos archivos tienen problemas")
        print("   Espera a que Railway termine de desplegar y vuelve a ejecutar este script")
        return 1

if __name__ == "__main__":
    sys.exit(main())
