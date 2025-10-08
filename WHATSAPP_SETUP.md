# 📱 Configuración del Agente de WhatsApp

## Descripción General

Este sistema incluye un **agente de IA inteligente** que permite a los clientes solicitar carreras de taxi directamente desde WhatsApp. El agente puede:

- ✅ Recibir solicitudes de carreras
- ✅ Geocodificar direcciones automáticamente
- ✅ Buscar el taxista más cercano
- ✅ Calcular tarifas estimadas
- ✅ Confirmar y crear carreras en el sistema
- ✅ Notificar a conductores
- ✅ Consultar estado de carreras
- ✅ Cancelar carreras

## 🔧 Configuración de WASender

### 1. Credenciales de API

Ya tienes configurado:
- **API URL**: `https://wasenderapi.com/api/send-message`
- **Token**: `e736f86d08e73ce5ee6f209098dc701a60deb8157f26b79485f66e1249aabee6`

### 2. Configurar el Webhook en WASender

1. Accede a tu panel de WASender
2. Ve a la sección de **Webhooks**
3. Configura el webhook con la siguiente URL:

```
https://tu-dominio.com/webhook/whatsapp/
```

**Nota**: Reemplaza `tu-dominio.com` con tu dominio real o URL de ngrok para desarrollo.

### 3. Eventos a Suscribir

Asegúrate de suscribirte a estos eventos:
- ✅ `message.received` - Cuando se recibe un mensaje
- ✅ `message.status` - Actualizaciones de estado de mensajes (opcional)

### 4. Formato del Webhook

WASender enviará webhooks en este formato:

```json
{
  "event": "message.received",
  "timestamp": "1757318059855",
  "session_id": 8359,
  "data": {
    "from": "+573001234567",
    "text": "Hola, quiero un taxi",
    "name": "Juan Pérez",
    "message_id": "ABC123"
  }
}
```

## 🚀 Endpoints Disponibles

### 1. Webhook Principal
```
POST /webhook/whatsapp/
```
Recibe mensajes entrantes de WhatsApp y los procesa con el agente de IA.

### 2. Webhook de Estado
```
POST /webhook/whatsapp/status/
```
Recibe actualizaciones de estado de mensajes enviados.

### 3. Enviar Notificación (Interno)
```
POST /api/whatsapp/send-notification/
```
Endpoint interno para enviar notificaciones desde otras partes de la aplicación.

**Ejemplo de uso:**
```bash
curl -X POST "http://localhost:8000/api/whatsapp/send-notification/" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+573001234567",
    "message": "Tu carrera ha sido aceptada"
  }'
```

## 💬 Comandos del Agente de WhatsApp

Los usuarios pueden interactuar con el agente usando estos comandos:

### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `HOLA` / `MENU` | Muestra el menú principal |
| `1` / `SOLICITAR` | Iniciar solicitud de carrera |
| `2` / `MIS CARRERAS` | Ver carreras activas |
| `3` / `CANCELAR` | Cancelar una carrera |
| `4` / `AYUDA` | Ver ayuda |
| `ESTADO` | Consultar estado de carrera activa |

### Flujo de Solicitud de Carrera

1. **Usuario**: "SOLICITAR" o "1"
2. **Bot**: Solicita dirección de origen
3. **Usuario**: Envía dirección o ubicación
4. **Bot**: Solicita dirección de destino
5. **Usuario**: Envía dirección de destino
6. **Bot**: Muestra resumen con tarifa estimada
7. **Usuario**: "SÍ" para confirmar
8. **Bot**: Crea la carrera y notifica al conductor

## 🧪 Pruebas en Desarrollo

### Opción 1: Usar ngrok (Recomendado)

1. Instala ngrok:
```bash
# Descarga desde https://ngrok.com/download
```

2. Ejecuta tu servidor Django:
```bash
python manage.py runserver
```

3. En otra terminal, ejecuta ngrok:
```bash
ngrok http 8000
```

4. Copia la URL HTTPS que ngrok te proporciona (ej: `https://abc123.ngrok.io`)

5. Configura el webhook en WASender con:
```
https://abc123.ngrok.io/webhook/whatsapp/
```

### Opción 2: Probar Localmente

Puedes probar el webhook localmente enviando solicitudes POST:

```bash
curl -X POST "http://localhost:8000/webhook/whatsapp/" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "message.received",
    "timestamp": "1757318059855",
    "session_id": 8359,
    "data": {
      "from": "+573001234567",
      "text": "MENU",
      "name": "Usuario Prueba"
    }
  }'
```

## 📝 Configuración Adicional

### 1. Variables de Entorno (Opcional)

Puedes mover las credenciales a variables de entorno para mayor seguridad:

En `settings.py`:
```python
WASENDER_API_URL = os.environ.get('WASENDER_API_URL', 'https://wasenderapi.com/api/send-message')
WASENDER_TOKEN = os.environ.get('WASENDER_TOKEN', 'tu-token-aqui')
```

En `whatsapp_agent.py`:
```python
from django.conf import settings

WASENDER_API_URL = settings.WASENDER_API_URL
WASENDER_TOKEN = settings.WASENDER_TOKEN
```

### 2. Personalizar Mensajes

Puedes personalizar los mensajes del agente editando el archivo:
```
taxis/whatsapp_agent.py
```

### 3. Almacenamiento de Conversaciones

Actualmente las conversaciones se almacenan en memoria. Para producción, considera:

- **Opción 1**: Usar Redis
- **Opción 2**: Usar la base de datos (modelo `ConversacionTelegram` puede adaptarse)

## 🔍 Monitoreo y Logs

Los logs del agente se guardan en el logger de Django. Para ver los logs:

```python
# En settings.py, asegúrate de tener:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## 🚨 Solución de Problemas

### Problema: El webhook no recibe mensajes

**Solución**:
1. Verifica que la URL del webhook esté correctamente configurada en WASender
2. Asegúrate de que tu servidor sea accesible públicamente (usa ngrok en desarrollo)
3. Revisa los logs de Django para ver si hay errores

### Problema: Los mensajes no se envían

**Solución**:
1. Verifica que el token de WASender sea correcto
2. Asegúrate de que los números de teléfono incluyan el código de país (+57 para Colombia)
3. Revisa los logs para ver el error específico

### Problema: Geocodificación falla

**Solución**:
1. Asegúrate de tener conexión a internet
2. Verifica que `geopy` esté instalado: `pip install geopy`
3. Considera usar Google Maps API para mejor precisión

## 📊 Integración con el Sistema

El agente de WhatsApp se integra automáticamente con:

- ✅ **Modelo de Usuarios**: Crea usuarios automáticamente si no existen
- ✅ **Modelo de Carreras**: Crea carreras en la base de datos
- ✅ **Sistema de Notificaciones**: Notifica a conductores cuando se asigna una carrera
- ✅ **Geocodificación**: Convierte direcciones en coordenadas

## 🎯 Próximos Pasos

1. **Configurar el webhook en WASender** con tu URL pública
2. **Probar el flujo completo** enviando mensajes desde WhatsApp
3. **Personalizar mensajes** según tus necesidades
4. **Implementar Redis** para almacenamiento de conversaciones en producción
5. **Agregar métricas** para monitorear el uso del agente

## 📞 Soporte

Para más información sobre la API de WASender, visita:
- Documentación: https://wasenderapi.com/docs
- Soporte: https://wasenderapi.com/support

---

**¡El agente de WhatsApp está listo para usar!** 🎉
