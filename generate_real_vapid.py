"""
Generar claves VAPID válidas usando py_vapid
"""
try:
    from py_vapid import Vapid01
    
    # Generar claves VAPID
    vapid = Vapid01()
    vapid.generate_keys()
    
    # Obtener claves en formato correcto
    private_key = vapid.private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_key = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    print("=" * 70)
    print("🔐 CLAVES VAPID VÁLIDAS GENERADAS")
    print("=" * 70)
    print("\n📋 CLAVE PÚBLICA (VAPID_PUBLIC_KEY):")
    print(public_key)
    print("\n📋 CLAVE PRIVADA (VAPID_PRIVATE_KEY):")
    print(private_key)
    print("\n📋 EMAIL (VAPID_ADMIN_EMAIL):")
    print("admin@deaquipalla.com")
    print("\n" + "=" * 70)
    
    # Guardar en archivo
    with open('vapid_real_keys.txt', 'w') as f:
        f.write(f"PUBLIC_KEY:\n{public_key}\n\n")
        f.write(f"PRIVATE_KEY:\n{private_key}\n\n")
        f.write("ADMIN_EMAIL: admin@deaquipalla.com\n")
    
    print("✅ Claves guardadas en 'vapid_real_keys.txt'")
    
except ImportError:
    print("❌ Error: py-vapid no está instalado")
    print("Instalando py-vapid...")
    import subprocess
    subprocess.run(["pip", "install", "py-vapid"])
    print("\n✅ py-vapid instalado. Ejecuta este script de nuevo.")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIntentando método alternativo con cryptography...")
    
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    import base64
    
    # Generar par de claves EC
    private_key_obj = ec.generate_private_key(ec.SECP256R1(), default_backend())
    public_key_obj = private_key_obj.public_key()
    
    # Serializar en formato PEM
    private_pem = private_key_obj.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')
    
    public_pem = public_key_obj.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    print("=" * 70)
    print("🔐 CLAVES VAPID VÁLIDAS GENERADAS (Cryptography)")
    print("=" * 70)
    print("\n📋 CLAVE PÚBLICA (VAPID_PUBLIC_KEY):")
    print(public_pem)
    print("\n📋 CLAVE PRIVADA (VAPID_PRIVATE_KEY):")
    print(private_pem)
    print("\n📋 EMAIL (VAPID_ADMIN_EMAIL):")
    print("admin@deaquipalla.com")
    print("\n" + "=" * 70)
    
    # Guardar en archivo
    with open('vapid_real_keys.txt', 'w') as f:
        f.write(f"PUBLIC_KEY:\n{public_pem}\n\n")
        f.write(f"PRIVATE_KEY:\n{private_pem}\n\n")
        f.write("ADMIN_EMAIL: admin@deaquipalla.com\n")
    
    print("✅ Claves guardadas en 'vapid_real_keys.txt'")
