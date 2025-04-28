import requests
# Reemplaza con tu token real


# Reemplaza con la URL de tu webhook
webhook_url = "https://jairojavier.app.n8n.cloud/webhook-test/nueva carrera "

# Datos simulados de una nueva carrera
data = {
    "cliente": "Juan Pérez",
    "origen": "Av. Siempre Viva 123",
    "destino": "Calle Falsa 456",
    "precio_estimado": 3.75
}

# Encabezados con el token de autorización
headers = {
    "Authorization": "2345abcde7890",
    "Content-Type": "application/json"
}

# Enviar solicitud POST
response = requests.post(webhook_url, json=data, headers=headers)

# Imprimir la respuesta
print("Status code:", response.status_code)
print("Respuesta:", response.text)
