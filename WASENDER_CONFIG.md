# Configuración de WASender para De Aquí Pa'llá

## 📱 Información de la API

### Credenciales
- **API URL:** `https://wasenderapi.com/api/send-message`
- **Token:** `e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6`

---

## 🔗 Configuración del Webhook

### URL del Webhook
```
https://tu-dominio.railway.app/webhook/whatsapp/
```

**Ejemplo:**
```
https://proyecto-django-channels-production.up.railway.app/webhook/whatsapp/
```

### Eventos a Suscribir
En el panel de WASender, configura los siguientes eventos:

1. ✅ **messages.upsert** - Mensajes entrantes
2. ✅ **message.status** - Estados de mensajes (opcional)

---

## 🧪 Prueba del Webhook

### Método 1: Test desde WASender
En el panel de WASender, usa el botón "Test Webhook". Deberías recibir:

**Request:**
```json
{
  "event": "webhook.test",
  "timestamp": "1757318059855",
  "session_id": 8359,
  "data": {
    "message": "This is a test webhook from WASender",
    "test": true
  }
}
```

**Response esperada:**
```json
{
  "status": "success",
  "message": "Test webhook received successfully",
  "timestamp": "1757318059855",
  "session_id": 8359
}
```

### Método 2: Verificación GET
Abre en tu navegador:
```
https://tu-dominio.railway.app/webhook/whatsapp/
```

Deberías ver:
```json
{
  "status": "ok",
  "message": "WhatsApp Webhook is active",
  "service": "De Aquí Pa'llá - Taxi Service",
  "endpoint": "/webhook/whatsapp/"
}
```

---

## 📤 Envío de Mensajes

### Usando cURL
```bash
curl -X POST "https://wasenderapi.com/api/send-message" \
  -H "Authorization: Bearer e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+593968192046",
    "text": "¡Hola! Tu taxi está en camino 🚕"
  }'
```

### Desde Python (ya implementado)
```python
from taxis.whatsapp_agent_ai import whatsapp_agent_ai

# Enviar mensaje simple
whatsapp_agent_ai.enviar_mensaje(
    numero_telefono="+593968192046",
    mensaje="Tu carrera ha sido aceptada"
)
```

---

## 📥 Formato de Mensajes Entrantes

### Mensaje de Texto
```json
{
  "event": "messages.upsert",
  "timestamp": "1757318059855",
  "session_id": 8359,
  "data": {
    "messages": {
      "key": {
        "remoteJid": "593968192046@s.whatsapp.net",
        "fromMe": false
      },
      "message": {
        "conversation": "Hola, necesito un taxi"
      },
      "pushName": "Juan Pérez"
    }
  }
}
```

### Ubicación GPS
```json
{
  "event": "messages.upsert",
  "timestamp": "1757318059855",
  "session_id": 8359,
  "data": {
    "messages": {
      "key": {
        "remoteJid": "593968192046@s.whatsapp.net",
        "fromMe": false
      },
      "message": {
        "locationMessage": {
          "degreesLatitude": -2.1894,
          "degreesLongitude": -79.8890
        }
      },
      "pushName": "Juan Pérez"
    }
  }
}
```

---

## 🤖 Comandos Disponibles

### Para Clientes
- **MENU** - Ver opciones disponibles
- **SOLICITAR** - Solicitar un taxi
- **MIS CARRERAS** - Ver carreras activas
- **ESTADO** - Ver estado de carrera actual
- **CANCELAR** - Cancelar carrera
- **AYUDA** - Obtener ayuda

### Para Conductores
- **ACEPTAR [ID]** - Aceptar carrera
- **RECHAZAR [ID]** - Rechazar carrera
- **LLEGUE** - Notificar llegada al origen
- **FINALIZAR** - Finalizar carrera

---

## 🔒 Seguridad

### Validación de Firma (X-Webhook-Signature)
El webhook verifica la firma en el header `X-Webhook-Signature` para asegurar que las peticiones vienen de WASender.

```python
webhook_signature = request.headers.get('X-Webhook-Signature', '')
if webhook_signature:
    logger.info(f"🔐 Webhook signature recibida: {webhook_signature[:20]}...")
```

### Validación de Usuarios
Solo usuarios registrados en la base de datos pueden usar el servicio:

```python
usuario = AppUser.objects.filter(
    phone_number__in=[numero_telefono, numero_local]
).first()

if not usuario:
    # Enviar mensaje de error
    return
```

---

## 📊 Logs

### Ver logs en Railway
```bash
railway logs
```

### Logs importantes
```
📥 Webhook recibido: {...}
✅ Webhook test recibido correctamente
📤 Enviando mensaje a +593968192046: ...
✅ Mensaje enviado exitosamente
💬 Procesando mensaje de +593968192046: Hola
📍 Ubicación GPS recibida de +593968192046: -2.1894, -79.8890
```

---

## 🐛 Troubleshooting

### Problema: Webhook no recibe mensajes
1. Verifica que la URL del webhook esté correctamente configurada en WASender
2. Verifica que el dominio de Railway esté activo
3. Revisa los logs: `railway logs`

### Problema: Mensajes no se envían
1. Verifica el token de WASender
2. Verifica el formato del número de teléfono (+593...)
3. Revisa los logs para ver errores de API

### Problema: Usuario no registrado
1. El número debe estar registrado en la base de datos
2. Formato: `0968192046` o `+593968192046`
3. Verificar en admin: `/admin/taxis/appuser/`

---

## ✅ Checklist de Configuración

- [ ] Token de WASender configurado en el código
- [ ] URL del webhook configurada en WASender
- [ ] Evento `messages.upsert` suscrito
- [ ] Test del webhook exitoso (200 OK)
- [ ] Usuarios registrados en la base de datos
- [ ] Números de teléfono con formato correcto
- [ ] Logs funcionando correctamente

---

## 📞 Soporte

Si tienes problemas, revisa:
1. Logs de Railway: `railway logs`
2. Panel de WASender: https://wasenderapi.com
3. Documentación de WASender API
