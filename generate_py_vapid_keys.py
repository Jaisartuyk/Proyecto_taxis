"""
Generador de claves VAPID en el formato correcto para py_vapid
"""
import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def generate_vapid_keys_py_vapid_format():
    print("🔐 Generando claves VAPID en formato py_vapid...")
    
    # Generar clave privada EC P-256
    private_key = ec.generate_private_key(
        ec.SECP256R1(),  # P-256 curve
        default_backend()
    )
    
    # Obtener clave pública
    public_key = private_key.public_key()
    
    # Serializar clave privada en formato DER (binario)
    private_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serializar clave pública en formato DER
    public_der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Convertir a base64 URL-safe (sin padding) como espera py_vapid
    private_key_b64 = base64.urlsafe_b64encode(private_der).decode('utf-8').rstrip('=')
    public_key_b64 = base64.urlsafe_b64encode(public_der).decode('utf-8').rstrip('=')
    
    # También generar formato PEM para comparación
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    print("✅ Claves VAPID generadas")
    print(f"🔑 Formato de clave privada (b64): {len(private_key_b64)} caracteres")
    print(f"🔑 Formato de clave pública (b64): {len(public_key_b64)} caracteres")
    
    return {
        'private_key_b64': private_key_b64,
        'public_key_b64': public_key_b64,
        'private_key_pem': private_pem,
        'public_key_pem': public_pem
    }

def test_py_vapid_format():
    """Probar si las claves en formato py_vapid funcionan"""
    keys = generate_vapid_keys_py_vapid_format()
    
    try:
        from py_vapid import Vapid
        
        # Probar cargar la clave privada
        vapid = Vapid.from_string(private_key=keys['private_key_b64'])
        print("✅ Clave privada b64 cargada correctamente en py_vapid")
        
        # Generar claims de prueba
        print("✅ Clave privada b64 cargada correctamente en py_vapid")
        
        return keys
        
    except Exception as e:
        print(f"❌ Error probando claves con py_vapid: {e}")
        import traceback
        print(f"🔍 Traceback: {traceback.format_exc()}")
        return None

if __name__ == "__main__":
    print("🚀 Probando generación de claves VAPID para py_vapid")
    print("=" * 60)
    
    keys = test_py_vapid_format()
    
    if keys:
        print("\n📋 Claves VAPID generadas exitosamente:")
        print(f"Private Key (b64): {keys['private_key_b64']}")
        print(f"Public Key (b64): {keys['public_key_b64']}")
        print("\n💾 Guardando en archivo...")
        
        # Guardar en archivo
        import json
        with open('vapid_keys_py_vapid.json', 'w') as f:
            json.dump(keys, f, indent=2)
        
        print("✅ Claves guardadas en vapid_keys_py_vapid.json")