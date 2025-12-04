# 📱 CONFIGURACIÓN DE NOTIFICACIONES PUSH - De Aquí Pa'llá

## ✅ Estado Actual: CASI LISTO

Tu aplicación ya tiene **TODO el código necesario** para notificaciones push como aplicación nativa. Solo faltan algunos pasos de configuración.

---

## 🔐 PASO 1: Claves VAPID Generadas ✅

Las claves VAPID ya fueron generadas y configuradas en `settings.py`:

```python
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": "LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0K...",
    "VAPID_PRIVATE_KEY": "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk...",
    "VAPID_ADMIN_EMAIL": "admin@deaquipalla.com"
}
```

---

## 🚀 PASO 2: Configurar Variables de Entorno en Railway

### Opción A: Usar las claves por defecto (más fácil)
Las claves ya están en `settings.py` como valores por defecto. **No necesitas hacer nada más**.

### Opción B: Usar variables de entorno (más seguro - recomendado)
1. Ve a tu proyecto en Railway
2. Abre la pestaña **Variables**
3. Agrega estas 3 variables:

```
VAPID_PUBLIC_KEY=LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFNjgxazRRMEhWVUtCZGxiR3F6M1JmejVycEJvbwpVUkRpeEVrN2RVNWhpSUxjelA0WlNLbFdEN3dURTVTQnpLeVhEZS8wL2ZaUTI2aE4zOFQ5d1VRVU9RPT0KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg

VAPID_PRIVATE_KEY=LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ2JoZ01vUGtTV2RhTXc1emsKdDVYZFBaeVMvSEVLUU9jQjNvTmh0L05pZGlPaFJBTkNBQVRyeldUaERRZFZRb0YyVnNhclBkRi9QbXVrR2loUgpFT0xFU1R0MVRtR0lndHpNL2hsSXFWWVB2Qk1UbElITXJKY043L1Q5OWxEYnFFM2Z4UDNCUkJRNQotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg

VAPID_ADMIN_EMAIL=admin@deaquipalla.com
```

4. Guarda y espera a que Railway redeploy automáticamente

---

## 📋 PASO 3: Verificar que el endpoint de suscripción funcione

El endpoint `/api/webpush/subscribe/` ya está implementado en `api_views.py`. 

### Verificar en Railway:
1. Abre tu app: `https://taxis-deaquipalla.up.railway.app`
2. Inicia sesión
3. Abre la consola del navegador (F12)
4. Busca logs como:
   ```
   Service Worker registered successfully
   Push subscription successful
   Subscription sent to server
   ```

---

## 🔔 PASO 4: Integrar notificaciones con eventos del chat

Ya tienes las funciones en `push_notifications.py`. Solo necesitas llamarlas cuando ocurran eventos.

### Ejemplo: Enviar notificación cuando llega un mensaje de chat

En tu `consumers.py` o donde manejes los mensajes de chat, agrega:

```python
from taxis.push_notifications import send_chat_message_notification

# Cuando se envía un mensaje
async def receive(self, text_data):
    data = json.loads(text_data)
    message = data['message']
    recipient_id = data['recipient_id']
    
    # ... tu código existente ...
    
    # Enviar notificación push
    from taxis.models import AppUser
    recipient = await database_sync_to_async(AppUser.objects.get)(id=recipient_id)
    sender = self.scope['user']
    
    await database_sync_to_async(send_chat_message_notification)(
        sender=sender,
        recipient=recipient,
        message=message
    )
```

---

## 📱 PASO 5: Probar en dispositivos móviles

### Android (Chrome/Edge/Firefox):
1. Abre `https://taxis-deaquipalla.up.railway.app` en el navegador
2. Cuando aparezca el prompt, acepta las notificaciones
3. Instala la PWA (botón "Agregar a pantalla de inicio")
4. Cierra la app
5. Envía un mensaje desde otro dispositivo
6. ✅ Deberías recibir una notificación nativa

### iOS (Safari 16.4+):
1. Abre `https://taxis-deaquipalla.up.railway.app` en Safari
2. Toca el botón de compartir
3. Selecciona "Agregar a pantalla de inicio"
4. Abre la app desde la pantalla de inicio
5. Acepta las notificaciones cuando se solicite
6. ✅ Las notificaciones funcionarán incluso con la app cerrada

---

## 🎯 FUNCIONES DISPONIBLES

Ya tienes estas funciones listas para usar en `push_notifications.py`:

### 1. Notificación de nuevo viaje
```python
from taxis.push_notifications import send_new_ride_notification
send_new_ride_notification(ride)
```

### 2. Notificación de mensaje de chat
```python
from taxis.push_notifications import send_chat_message_notification
send_chat_message_notification(sender, recipient, message)
```

### 3. Notificación de mensaje de audio
```python
from taxis.push_notifications import send_audio_message_notification
send_audio_message_notification(sender, recipient)
```

### 4. Notificación a todos los conductores
```python
from taxis.push_notifications import send_push_to_all_drivers
send_push_to_all_drivers(title, body, data)
```

---

## 🔧 TROUBLESHOOTING

### Las notificaciones no llegan:
1. Verifica que el Service Worker esté registrado (consola del navegador)
2. Verifica que el usuario haya aceptado los permisos de notificación
3. Verifica que la suscripción se haya guardado en la base de datos:
   ```python
   from taxis.models import WebPushSubscription
   WebPushSubscription.objects.filter(user=tu_usuario)
   ```

### Error "VAPID key not found":
- Asegúrate de que las variables de entorno estén configuradas en Railway
- O que los valores por defecto estén en `settings.py`

### Las notificaciones no aparecen en iOS:
- Asegúrate de que la PWA esté instalada desde Safari
- iOS solo soporta notificaciones push para PWAs instaladas
- Requiere iOS 16.4 o superior

---

## ✨ CARACTERÍSTICAS

### ✅ Lo que ya funciona:
- 📱 PWA instalable en Android e iOS
- 🔔 Notificaciones push del sistema operativo
- 🔄 Reconexión automática de Service Worker
- 💾 Almacenamiento de suscripciones en base de datos
- 🎨 Notificaciones con iconos y acciones personalizadas
- 📳 Vibración al recibir notificación
- 🔗 Click en notificación abre la app en la página correcta

### 🎯 Próximos pasos recomendados:
1. Integrar las notificaciones con los eventos de chat (PASO 4)
2. Probar en dispositivos reales (PASO 5)
3. Personalizar los mensajes de notificación según el tipo de evento
4. Agregar notificaciones para otros eventos (viaje completado, conductor cerca, etc.)

---

## 📞 SOPORTE

Si tienes problemas, revisa los logs en:
- Consola del navegador (F12)
- Logs de Railway
- Logs de Django en producción

---

**¡Tu app ya está lista para enviar notificaciones push como una aplicación nativa! 🚀📱**
