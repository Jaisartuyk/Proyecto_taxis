# 🔧 FIX: Audio NO se reproduce (Android + Web)

## 🐛 PROBLEMA IDENTIFICADO

**Síntomas:**
- ✅ Notificaciones push SÍ llegan
- ✅ Audio SÍ se graba y envía
- ❌ Audio NO se reproduce en Android
- ❌ Audio NO se reproduce en Web

**Causa:**
1. **Android:** WebSocket no tiene token de autenticación (error 403)
2. **Web:** WebSocket se desconecta inmediatamente (código 1001)

---

## ✅ SOLUCIÓN PARA ANDROID

### Paso 1: Recompilar la app con el fix del token

```bash
cd "C:\Users\H P\Downloads\flutter_application_1"
flutter clean
flutter pub get
flutter run
```

### Paso 2: Probar la conexión

1. Abre la app
2. Inicia sesión
3. Presiona "CONECTAR"
4. Verifica en los logs:
   ```
   🔑 Token presente: 05d5042478...
   ✅ Header Authorization agregado
   ✅ Conectado exitosamente
   ```

### Paso 3: Probar audio

1. Mantén presionado el botón azul
2. Habla
3. Suelta el botón
4. Verifica que se envíe:
   ```
   ✅ Audio enviado por WebSocket
   ```

---

## ✅ SOLUCIÓN PARA WEB

### Problema: WebSocket se desconecta (código 1001)

El código 1001 significa "Going Away" - el cliente está cerrando la conexión.

### Posibles causas:

1. **Múltiples instancias de WebSocket**
2. **Error en el código JavaScript**
3. **Conflicto entre script inline y archivo externo**

### Fix Rápido:

#### Opción 1: Verificar logs del navegador

1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Console"
3. Busca errores relacionados con WebSocket
4. Busca: "WebSocket connection closed" o "1001"

#### Opción 2: Verificar que solo hay UNA conexión

En la consola del navegador, ejecuta:

```javascript
// Ver si hay múltiples WebSockets
console.log('WebSockets activos:', window.audioWebSocket);
```

#### Opción 3: Forzar reconexión

En `comunicacion-completa.js`, busca la función de conexión y agrega:

```javascript
// Asegurar que solo hay una instancia
if (window.audioWebSocket) {
    console.log('⚠️ Cerrando WebSocket anterior');
    window.audioWebSocket.close();
    window.audioWebSocket = null;
}

// Crear nueva conexión
window.audioWebSocket = new WebSocket(wsUrl);
```

---

## 🔍 DIAGNÓSTICO RÁPIDO

### Para saber dónde está el problema:

#### 1. Verificar en Railway logs:

```
✅ BUENO: WSCONNECT /ws/audio/conductores/
✅ BUENO: Audio recibido de carlos
❌ MALO: WSDISCONNECT código: 1001
```

Si ves el WSDISCONNECT inmediatamente después del WSCONNECT, el problema está en el JavaScript.

#### 2. Verificar en la consola del navegador:

```
✅ BUENO: WebSocket conectado
✅ BUENO: Audio recibido
❌ MALO: WebSocket connection closed: 1001
```

#### 3. Verificar en la app Android:

```
✅ BUENO: 🔑 Token presente
✅ BUENO: ✅ Conectado exitosamente
❌ MALO: ❌ Error WebSocket: 403 Forbidden
```

---

## 🎯 SOLUCIÓN DEFINITIVA

### Para Web (JavaScript):

Necesito ver el archivo `comunicacion-completa.js` para identificar el problema exacto.

**Ubicación:** `taxis/static/js/comunicacion-completa.js`

**Buscar:**
- Función de conexión WebSocket
- Manejo de eventos onclose
- Múltiples llamadas a connect()

### Para Android (Flutter):

Ya está corregido, solo falta recompilar.

---

## 📋 CHECKLIST DE VERIFICACIÓN

### Android:
- [ ] App recompilada con fix del token
- [ ] Usuario inicia sesión
- [ ] Botón "CONECTAR" presionado
- [ ] Log muestra "Token presente"
- [ ] Log muestra "Conectado exitosamente"
- [ ] Audio se envía correctamente
- [ ] Audio se recibe y reproduce

### Web:
- [ ] Abrir página de comunicación
- [ ] Verificar consola del navegador (F12)
- [ ] WebSocket se conecta
- [ ] WebSocket NO se desconecta inmediatamente
- [ ] Audio se envía correctamente
- [ ] Audio se recibe y reproduce

---

## 🚨 SI EL PROBLEMA PERSISTE

### Información necesaria para debug:

1. **Logs de Railway** (últimos 50 líneas)
2. **Logs de la consola del navegador** (pestaña Console)
3. **Logs de Flutter** (cuando presionas CONECTAR)
4. **Captura de pantalla** del error

---

## 💡 SOLUCIÓN TEMPORAL

Mientras se corrige el problema principal:

### Para Web:
1. Recargar la página (Ctrl+R)
2. Esperar 2 segundos antes de enviar audio
3. Verificar que el indicador de conexión esté verde

### Para Android:
1. Cerrar y abrir la app
2. Iniciar sesión nuevamente
3. Presionar CONECTAR
4. Esperar a ver "Conectado exitosamente"

---

**Fecha:** 27 de diciembre de 2025  
**Estado:** 🔧 EN PROCESO  
**Prioridad:** 🔴 CRÍTICA
