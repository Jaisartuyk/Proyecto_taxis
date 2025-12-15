# 🔐 ACTUALIZAR CLAVES VAPID EN RAILWAY

## ⚠️ PROBLEMA IDENTIFICADO

Las claves VAPID actuales en Railway están en formato **PEM** (con `-----BEGIN...-----`), pero la biblioteca `pywebpush` requiere claves en formato **base64url**.

## ✅ CLAVES CONVERTIDAS

Ya convertí tus claves al formato correcto. Aquí están:

### VAPID_PUBLIC_KEY:
```


```

### VAPID_PRIVATE_KEY:
```
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgOT9i-uOVE15UqRodHpqQwEMR-8l65sxH8jJzhr9U2C-hRANCAAS3k_sgXdwmHT9dm9-rJByI5YglykvYjevTTw9GpMTeo5LgwkjjUEFKpz7zcu9SCA5Gmf1yZzvqc-k5EfFRj11A
```

### VAPID_ADMIN_EMAIL:
```
admin@deaquipalla.com
```

## 📋 PASOS PARA ACTUALIZAR EN RAILWAY

### 1. Ir a Railway Dashboard
- Abre: https://railway.app
- Inicia sesión con tu cuenta
- Selecciona tu proyecto "taxis-deaquipalla"

### 2. Abrir Variables de Entorno
- En el proyecto, haz clic en tu servicio
- Ve a la pestaña **"Variables"**
- Verás las variables actuales

### 3. Actualizar las 3 Variables

#### Variable 1: VAPID_PUBLIC_KEY
1. Busca o crea la variable `VAPID_PUBLIC_KEY`
2. **Borra** el contenido actual (el que tiene `-----BEGIN PUBLIC KEY-----`)
3. **Copia y pega** exactamente esto:
   ```
   BLeT-yBd3CYdP12b36skHIjliCXKS9iN69NPD0akxN6jkuDCSONQQUqnPvNy71IIDkaZ_XJnO-pz6TkR8VGPXUA
   ```

#### Variable 2: VAPID_PRIVATE_KEY
1. Busca o crea la variable `VAPID_PRIVATE_KEY`
2. **Borra** el contenido actual (el que tiene `-----BEGIN PRIVATE KEY-----`)
3. **Copia y pega** exactamente esto:
   ```
   MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgOT9i-uOVE15UqRodHpqQwEMR-8l65sxH8jJzhr9U2C-hRANCAAS3k_sgXdwmHT9dm9-rJByI5YglykvYjevTTw9GpMTeo5LgwkjjUEFKpz7zcu9SCA5Gmf1yZzvqc-k5EfFRj11A
   ```

#### Variable 3: VAPID_ADMIN_EMAIL
1. Verifica que existe `VAPID_ADMIN_EMAIL`
2. El valor debe ser:
   ```
   admin@deaquipalla.com
   ```

### 4. Guardar y Redesplegar
1. Haz clic en **"Save"** o el botón para guardar
2. Railway **automáticamente redespliegará** tu aplicación
3. Espera 2-3 minutos mientras se reinicia

### 5. Verificar que Funcione
1. Ve a: `https://taxis-deaquipalla.up.railway.app/test-notifications/`
2. Verifica que no haya errores en la consola
3. Prueba activar las notificaciones
4. Deberías poder suscribirte sin errores

## 🔍 VERIFICACIÓN RÁPIDA

Una vez actualizado, abre la consola del navegador (F12) en tu sitio y ejecuta:

```javascript
console.log(document.querySelector('meta[name="vapid-public-key"]').content);
```

Deberías ver:
```
BLeT-yBd3CYdP12b36skHIjliCXKS9iN69NPD0akxN6jkuDCSONQQUqnPvNy71IIDkaZ_XJnO-pz6TkR8VGPXUA
```

## ❗ IMPORTANTE

- **NO compartas estas claves públicamente** (aunque la pública es menos sensible)
- Las claves deben estar **sin saltos de línea**
- **NO incluyas** los headers `-----BEGIN...-----` ni `-----END...-----`
- Estas son las claves **correctas** derivadas de tus claves PEM originales

## 🐛 Si Siguen los Errores

Si después de actualizar siguen los errores:

1. **Verifica los logs de Railway:**
   - Ve a la pestaña "Deployments"
   - Revisa los logs del último despliegue
   - Busca errores relacionados con VAPID

2. **Limpia la caché:**
   - En tu navegador, abre DevTools (F12)
   - Ve a Application > Clear storage
   - Haz clic en "Clear site data"
   - Recarga la página

3. **Verifica el Service Worker:**
   - Ve a Application > Service Workers
   - Haz clic en "Unregister"
   - Recarga la página para registrarlo nuevamente

## 📚 Referencias

- **Archivo con las claves:** `vapid_keys_base64url.txt` (en este proyecto)
- **Script de conversión:** `convert_vapid_to_base64url.py`
- **Formato base64url:** RFC 4648 (URL-safe base64 sin padding)

---

**Fecha:** 11 de diciembre de 2025
**Estado:** Listo para aplicar en Railway
