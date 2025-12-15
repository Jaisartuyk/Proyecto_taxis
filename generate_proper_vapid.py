"""
Generar claves VAPID válidas para Web Push usando cryptography
"""
import os
import base64
import json

def generate_vapid_keys_proper():
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import serialization
        
        # Generar clave privada EC
        private_key = ec.generate_private_key(ec.SECP256R1())
        
        # Generar clave pública
        public_key = private_key.public_key()
        
        # Serializar clave privada en formato PEM
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('ascii')
        
        # Serializar clave pública en formato PEM
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('ascii')
        
        # También generar en formato raw para frontend
        public_raw = public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.UncompressedPoint
        )
        
        # Convertir a base64 URL-safe para el frontend
        public_b64 = base64.urlsafe_b64encode(public_raw).decode('ascii').rstrip('=')
        
        vapid_config = {
            "private_key_pem": private_pem,
            "public_key_pem": public_pem,
            "public_key_b64": public_b64,
            "admin_email": "admin@deaquipalla.com"
        }
        
        # Guardar en archivo
        with open('vapid_keys_proper.json', 'w') as f:
            json.dump(vapid_config, f, indent=2)
        
        print("✅ Claves VAPID válidas generadas:")
        print(f"   📁 Guardadas en: vapid_keys_proper.json")
        print(f"   🔑 Public Key (B64): {public_b64[:50]}...")
        print(f"   🔐 Private Key: {private_pem.split()[2][:30]}...")
        
        return vapid_config
        
    except ImportError as e:
        print(f"❌ cryptography no está instalada: {e}")
        return None
    except Exception as e:
        print(f"❌ Error generando claves VAPID: {e}")
        return None

if __name__ == "__main__":
    generate_vapid_keys_proper()