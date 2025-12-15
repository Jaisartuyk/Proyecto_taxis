"""
Generar nuevas claves VAPID válidas usando pywebpush
"""
import json

def generate_vapid_keys():
    try:
        from pywebpush import generate_vapid_keys
        vapid_keys = generate_vapid_keys()
        
        vapid_config = {
            "public_key": vapid_keys['public_key'],
            "private_key": vapid_keys['private_key'],
            "admin_email": "admin@deaquipalla.com"
        }
        
        # Guardar en archivo JSON
        with open('vapid_keys_new.json', 'w') as f:
            json.dump(vapid_config, f, indent=2)
        
        print("✅ Nuevas claves VAPID generadas:")
        print(f"   📁 Guardadas en: vapid_keys_new.json")
        print(f"   🔑 Public Key: {vapid_keys['public_key'][:50]}...")
        print(f"   🔐 Private Key: {vapid_keys['private_key'][:30]}...")
        
        return vapid_config
        
    except ImportError:
        print("❌ pywebpush no está instalado")
        return None
    except Exception as e:
        print(f"❌ Error generando claves VAPID: {e}")
        return None

if __name__ == "__main__":
    generate_vapid_keys()