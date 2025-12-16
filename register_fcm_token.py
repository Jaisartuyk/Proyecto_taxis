#!/usr/bin/env python3
"""
Script para registrar el token FCM en el backend
"""

import requests
import json

# Configuración
API_URL = "https://taxis-deaquipalla.up.railway.app/api/fcm/register/"
FCM_TOKEN = "fL6rJ0XZQoK_4KelG6o1qR:APA91bEjeQOsHx3ewq6ITKoB3THf6i9hcrglFw__wGl93w030uxHOi7Qmc4LcaphOzl0kuVYgxsjAEBq8eg5_UAju640L0sPK5fu6QS168SC7nBqn9QRZ7s"

# Datos del conductor (ajusta según tu usuario)
# Opciones: usa el username de tu conductor, por ejemplo: "carlos", "admin", etc.
USER_ID = "carlos"  # Cambia esto por tu username de conductor
DEVICE_TYPE = "android"

def register_token():
    """Registra el token FCM en el backend"""
    
    payload = {
        "token": FCM_TOKEN,
        "user_id": USER_ID,
        "device_type": DEVICE_TYPE
    }
    
    print("🔄 Registrando token FCM...")
    print(f"📱 Token: {FCM_TOKEN[:50]}...")
    print(f"👤 Usuario: {USER_ID}")
    print(f"📲 Dispositivo: {DEVICE_TYPE}")
    print()
    
    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print("✅ ¡Token registrado exitosamente!")
            print(f"📄 Respuesta: {response.json()}")
        else:
            print(f"❌ Error al registrar token")
            print(f"📄 Status Code: {response.status_code}")
            print(f"📄 Respuesta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    register_token()
