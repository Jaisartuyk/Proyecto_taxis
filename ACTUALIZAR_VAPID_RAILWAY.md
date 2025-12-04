# 🔐 ACTUALIZAR CLAVES VAPID EN RAILWAY

## ⚠️ IMPORTANTE: Debes actualizar las variables en Railway

Las claves VAPID anteriores tenían un formato incorrecto. Ahora tienes nuevas claves que funcionarán correctamente.

---

## 📋 PASO 1: Copiar las nuevas claves

Las nuevas claves están en el archivo `vapid_simple_keys.txt`:

```
PUBLIC_KEY=HHFKpkNYiNsS2tlnB4kM26UAH1GCF5rs-ple0NDA8vwF42XtNAAd1SmsHfQOWbo-quzkhlCRi-nX8IM74PyYvQ0
PRIVATE_KEY=wP74TyM70vkLcVL3mpbBhIlJMwUagcL-ToY4i_gmz80
ADMIN_EMAIL=admin@deaquipalla.com
```

---

## 🚀 PASO 2: Actualizar en Railway

1. Ve a tu proyecto en Railway: https://railway.app
2. Selecciona tu servicio de Django
3. Ve a la pestaña **Variables**
4. **ACTUALIZA** (no agregues nuevas, reemplaza las existentes):

### Variable 1: VAPID_PUBLIC_KEY
```
HHFKpkNYiNsS2tlnB4kM26UAH1GCF5rs-ple0NDA8vwF42XtNAAd1SmsHfQOWbo-quzkhlCRi-nX8IM74PyYvQ0
```

### Variable 2: VAPID_PRIVATE_KEY
```
wP74TyM70vkLcVL3mpbBhIlJMwUagcL-ToY4i_gmz80
```

### Variable 3: VAPID_ADMIN_EMAIL
```
admin@deaquipalla.com
```

5. Guarda los cambios
6. Railway hará **redeploy automáticamente**

---

## ✅ PASO 3: Verificar que funcione

Después del redeploy (toma 2-3 minutos):

1. Abre tu app: https://taxis-deaquipalla.up.railway.app
2. Inicia sesión
3. Abre la consola del navegador (F12)
4. Busca estos mensajes:
   ```
   Service Worker registered successfully
   Push subscription successful
   Subscription sent to server
   ```

5. Envía un mensaje de prueba desde otro dispositivo
6. Verifica en los logs de Railway que NO aparezca el error:
   ```
   ❌ Error al enviar notificación push: Could not deserialize key data
   ```

7. En su lugar, deberías ver:
   ```
   📱 Notificación push enviada: usuario1 -> usuario2
   ```

---

## 🔍 SOLUCIÓN DE PROBLEMAS

### Si sigues viendo el error de "Could not deserialize key data":
1. Verifica que las variables en Railway estén **exactamente** como se muestran arriba
2. Asegúrate de que no haya espacios al inicio o final
3. Verifica que Railway haya hecho redeploy después de cambiar las variables

### Si las notificaciones no llegan:
1. Verifica que el usuario haya aceptado los permisos de notificación
2. Verifica que la suscripción se haya guardado en la base de datos:
   - Ve al admin de Django: `/admin/`
   - Busca "Web Push Subscriptions"
   - Verifica que exista una suscripción para el usuario

### Para ver logs en Railway:
1. Ve a tu proyecto en Railway
2. Click en tu servicio
3. Ve a la pestaña **Deployments**
4. Click en el deployment activo
5. Ve a **View Logs**

---

## 🎯 RESULTADO ESPERADO

Después de actualizar las claves, cuando envíes un mensaje:

**En los logs de Railway verás:**
```
Mensaje guardado en BD: Admin -> Conductor
Mensaje de 1 enviado a 11
📱 Notificación push enviada: admin -> conductor
```

**En el dispositivo del receptor:**
- 📱 Notificación nativa del sistema
- 🔔 Con el título y mensaje
- 📳 Vibración
- 🎨 Icono de la app

---

## 📝 NOTAS DE SEGURIDAD

✅ **CORRECTO:** Las claves ahora solo están en las variables de entorno de Railway
✅ **CORRECTO:** El código en GitHub no contiene claves reales
✅ **CORRECTO:** Los valores por defecto en settings.py están vacíos

❌ **NO SUBAS** el archivo `vapid_simple_keys.txt` a GitHub (ya está en .gitignore)

---

**¡Listo! Después de actualizar las variables en Railway, las notificaciones push funcionarán correctamente! 🎉**
