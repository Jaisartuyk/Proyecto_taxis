#!/usr/bin/env python3
"""
Script para convertir claves VAPID de formato PEM a base64url
para usar con Web Push API
"""

import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def pem_to_base64url(pem_string, key_type='public'):
    """
    Convierte una clave PEM a formato base64url
    
    Args:
        pem_string: String con la clave en formato PEM
        key_type: 'public' o 'private'
    
    Returns:
        String en formato base64url
    """
    try:
        # Limpiar el string
        pem_bytes = pem_string.strip().encode('utf-8')
        
        if key_type == 'public':
            # Cargar clave pública
            public_key = serialization.load_pem_public_key(
                pem_bytes,
                backend=default_backend()
            )
            
            # Exportar en formato raw (sin PEM)
            raw_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
        else:
            # Cargar clave privada
            private_key = serialization.load_pem_private_key(
                pem_bytes,
                password=None,
                backend=default_backend()
            )
            
            # Exportar en formato raw
            raw_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        
        # Convertir a base64url (URL-safe base64 sin padding)
        base64url = base64.urlsafe_b64encode(raw_bytes).decode('utf-8').rstrip('=')
        
        return base64url
        
    except Exception as e:
        print(f"Error al convertir clave {key_type}: {e}")
        return None


if __name__ == "__main__":
    # Tus claves PEM de Railway
    public_key_pem = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEt5P7IF3cJh0/XZvfqyQciOWIJcpL
2I3r008PRqTE3qOS4MJI41BBSqc+83LvUggORpn9cmc76nPpORHxUY9dQA==
-----END PUBLIC KEY-----"""

    private_key_pem = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgOT9i+uOVE15UqRod
HpqQwEMR+8l65sxH8jJzhr9U2C+hRANCAAS3k/sgXdwmHT9dm9+rJByI5YglykvY
jevTTw9GpMTeo5LgwkjjUEFKpz7zcu9SCA5Gmf1yZzvqc+k5EfFRj11A
-----END PRIVATE KEY-----"""

    print("=" * 70)
    print("🔐 CONVERSIÓN DE CLAVES VAPID PEM A BASE64URL")
    print("=" * 70)
    print()
    
    # Convertir clave pública
    public_base64url = pem_to_base64url(public_key_pem, 'public')
    
    if public_base64url:
        print("✅ VAPID_PUBLIC_KEY (base64url):")
        print("-" * 70)
        print(public_base64url)
        print()
    else:
        print("❌ Error al convertir la clave pública")
        print()
    
    # Convertir clave privada
    private_base64url = pem_to_base64url(private_key_pem, 'private')
    
    if private_base64url:
        print("✅ VAPID_PRIVATE_KEY (base64url):")
        print("-" * 70)
        print(private_base64url)
        print()
    else:
        print("❌ Error al convertir la clave privada")
        print()
    
    print("=" * 70)
    print("📋 INSTRUCCIONES PARA RAILWAY:")
    print("=" * 70)
    print()
    print("1. Ve a tu proyecto en Railway")
    print("2. Abre la pestaña 'Variables'")
    print("3. Actualiza las siguientes variables:")
    print()
    print("   VAPID_PUBLIC_KEY =", public_base64url if public_base64url else "ERROR")
    print()
    print("   VAPID_PRIVATE_KEY =", private_base64url if private_base64url else "ERROR")
    print()
    print("   VAPID_ADMIN_EMAIL = admin@deaquipalla.com")
    print()
    print("4. Guarda los cambios")
    print("5. Railway reiniciará automáticamente el servicio")
    print()
    print("=" * 70)
    
    # Guardar en archivo también
    with open('vapid_keys_base64url.txt', 'w') as f:
        f.write("# Claves VAPID en formato base64url para Railway\n\n")
        f.write(f"VAPID_PUBLIC_KEY={public_base64url}\n\n")
        f.write(f"VAPID_PRIVATE_KEY={private_base64url}\n\n")
        f.write("VAPID_ADMIN_EMAIL=admin@deaquipalla.com\n")
    
    print("💾 Las claves también se guardaron en: vapid_keys_base64url.txt")
    print()
