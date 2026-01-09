# 📱 Guía: Implementar Control de Transmisión de Audio en Android

## 🎯 Objetivo
Agregar el sistema de "Alguien está hablando" a la app Android Flutter para que:
- Muestre cuando alguien está transmitiendo
- Deshabilite el botón de micrófono cuando otro habla
- Tenga timeout de 30 segundos
- Se sincronice con la central web

---

## 📋 PASO 1: Identificar los Archivos

En tu proyecto Flutter, abre la **Terminal** y ejecuta:

```powershell
Get-ChildItem -Recurse -Include *.dart | Select-String "WebSocket" | Select-Object Path -Unique
```

También ejecuta:

```powershell
Get-ChildItem -Recurse -Include *.dart | Select-String "audioSocket\|AudioService\|recordAudio\|startRecording" | Select-Object Path -Unique
```

**Anota los archivos que aparezcan.** Probablemente serán:
- `lib/services/websocket_service.dart` o `lib/services/audio_service.dart`
- `lib/screens/main_screen.dart` o `lib/screens/home_screen.dart`

---

## 📋 PASO 2: Modificar el Servicio de WebSocket/Audio

### 📁 Archivo: `lib/services/websocket_service.dart` (o `audio_service.dart`)

#### 2.1. Agregar imports necesarios (al inicio del archivo)

```dart
import 'dart:async';
import 'dart:convert';
```

#### 2.2. Agregar variables de estado (dentro de la clase)

Busca donde están las variables de la clase (después de `class AudioService {` o similar) y agrega:

```dart
class AudioService {
  // ... variables existentes ...
  
  // ✅ NUEVO: Variables para control de transmisión
  bool isSomeoneTransmitting = false;
  String? currentSpeakerName;
  String? currentSpeakerRole;
  Timer? transmissionTimeout;
  final int TIMEOUT_SECONDS = 30;
  
  // StreamController para notificar a la UI
  final _transmissionStatusController = StreamController<Map<String, dynamic>>.broadcast();
  Stream<Map<String, dynamic>> get transmissionStatusStream => _transmissionStatusController.stream;
```

#### 2.3. Agregar manejo del nuevo tipo de mensaje

Busca donde está el listener del WebSocket (algo como `_channel!.stream.listen((message) {`):

**ANTES:**
```dart
_channel!.stream.listen((message) {
  final data = jsonDecode(message);
  final type = data['type'];
  
  if (type == 'audio_broadcast') {
    // ... código existente ...
  }
  
  if (type == 'location_update') {
    // ... código existente ...
  }
});
```

**DESPUÉS (agregar este caso):**
```dart
_channel!.stream.listen((message) {
  final data = jsonDecode(message);
  final type = data['type'];
  
  if (type == 'audio_broadcast') {
    // ... código existente ...
  }
  
  if (type == 'location_update') {
    // ... código existente ...
  }
  
  // ✅ NUEVO: Manejar estado de transmisión
  if (type == 'audio_transmission_status') {
    _handleTransmissionStatus(data);
    return;
  }
});
```

#### 2.4. Agregar la función que maneja el estado

Agrega esta función **dentro de la clase**, después del listener:

```dart
// ✅ NUEVO: Manejar cuando alguien empieza o termina de hablar
void _handleTransmissionStatus(Map<String, dynamic> data) {
  final status = data['status'];
  final senderName = data['sender_name'] ?? 'Usuario';
  final senderRole = data['sender_role'] ?? 'conductor';
  final senderId = data['sender_id'];
  
  if (status == 'started') {
    // Alguien empezó a transmitir
    print('🔴 $senderName ($senderRole) empezó a transmitir');
    
    isSomeoneTransmitting = true;
    currentSpeakerName = senderName;
    currentSpeakerRole = senderRole;
    
    // Notificar a la UI
    _transmissionStatusController.add({
      'status': 'started',
      'name': senderName,
      'role': senderRole,
      'id': senderId,
    });
    
  } else if (status == 'stopped' || status == 'force_stopped') {
    // Terminó de transmitir
    print('✅ $senderName terminó de transmitir');
    
    isSomeoneTransmitting = false;
    currentSpeakerName = null;
    currentSpeakerRole = null;
    
    // Notificar a la UI
    _transmissionStatusController.add({
      'status': 'stopped',
      'forced': status == 'force_stopped',
    });
  }
}
```

#### 2.5. Agregar funciones para notificar start/stop

Agrega estas funciones **dentro de la clase**:

```dart
// ✅ NUEVO: Notificar que empezaste a transmitir
void notifyTransmissionStarted(int userId, String userName) {
  if (_channel != null) {
    _channel!.sink.add(jsonEncode({
      'type': 'audio_transmission_started',
      'sender_id': userId,
      'sender_name': userName,
      'sender_role': 'conductor',
    }));
    
    print('📡 Notificado: transmisión iniciada');
    
    // Timeout de seguridad (30 segundos)
    transmissionTimeout = Timer(Duration(seconds: TIMEOUT_SECONDS), () {
      print('⏱️ Timeout alcanzado, deteniendo transmisión');
      notifyTransmissionStopped(userId, userName);
      
      // Detener la grabación si está activa
      stopRecording();
    });
  }
}

// ✅ NUEVO: Notificar que terminaste de transmitir
void notifyTransmissionStopped(int userId, String userName) {
  if (transmissionTimeout != null) {
    transmissionTimeout!.cancel();
    transmissionTimeout = null;
  }
  
  if (_channel != null) {
    _channel!.sink.add(jsonEncode({
      'type': 'audio_transmission_stopped',
      'sender_id': userId,
      'sender_name': userName,
    }));
    
    print('📡 Notificado: transmisión detenida');
  }
}
```

#### 2.6. Limpiar recursos en dispose

Busca la función `dispose()` y agrega:

```dart
void dispose() {
  _transmissionStatusController.close();  // ✅ NUEVO
  transmissionTimeout?.cancel();          // ✅ NUEVO
  
  // ... resto del código existente de dispose ...
  _channel?.sink.close();
}
```

---

## 📋 PASO 3: Modificar la Pantalla Principal (UI)

### 📁 Archivo: `lib/screens/main_screen.dart` (o donde esté el botón de audio)

#### 3.1. Agregar variables de estado

Busca donde está el `State` de tu pantalla (algo como `class _MainScreenState extends State<MainScreen> {`) y agrega:

```dart
class _MainScreenState extends State<MainScreen> {
  // ... variables existentes ...
  
  // ✅ NUEVO: Estado de transmisión
  bool isSomeoneTransmitting = false;
  String? currentSpeakerName;
  bool isButtonEnabled = true;
```

#### 3.2. Escuchar cambios de estado en initState

Busca la función `initState()` y agrega al final (antes del `}`):

```dart
@override
void initState() {
  super.initState();
  
  // ... código existente ...
  
  // ✅ NUEVO: Escuchar cambios de estado de transmisión
  audioService.transmissionStatusStream.listen((status) {
    setState(() {
      if (status['status'] == 'started') {
        isSomeoneTransmitting = true;
        currentSpeakerName = status['name'];
        isButtonEnabled = false;
        
        // Mostrar notificación
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🔴 ${status['name']} está transmitiendo...'),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 30),
          ),
        );
      } else {
        isSomeoneTransmitting = false;
        currentSpeakerName = null;
        isButtonEnabled = true;
        
        // Cerrar notificación
        ScaffoldMessenger.of(context).clearSnackBars();
        
        if (status['forced'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('🚨 Transmisión interrumpida por la central'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      }
    });
  });
}
```

#### 3.3. Modificar el botón de audio

Busca donde está tu botón de micrófono. Puede ser:
- `GestureDetector` con `onLongPress`
- `InkWell` con `onTapDown` / `onTapUp`
- `FloatingActionButton`

**EJEMPLO - Si tienes GestureDetector:**

**ANTES:**
```dart
GestureDetector(
  onLongPressStart: (_) {
    audioService.startRecording();
  },
  onLongPressEnd: (_) {
    audioService.stopRecording();
  },
  child: Icon(Icons.mic, size: 50),
)
```

**DESPUÉS:**
```dart
GestureDetector(
  onLongPressStart: (_) {
    // ✅ Verificar si alguien está transmitiendo
    if (isSomeoneTransmitting) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('⚠️ $currentSpeakerName está transmitiendo, espera...'),
          backgroundColor: Colors.orange,
        ),
      );
      return;
    }
    
    // Empezar a grabar
    audioService.startRecording();
    
    // ✅ NUEVO: Notificar que empezaste
    audioService.notifyTransmissionStarted(
      widget.userId,      // Tu ID de usuario
      widget.userName,    // Tu nombre
    );
  },
  onLongPressEnd: (_) {
    // Detener y enviar
    audioService.stopRecording();
    
    // ✅ NUEVO: Notificar que terminaste
    audioService.notifyTransmissionStopped(
      widget.userId,
      widget.userName,
    );
  },
  child: Opacity(
    opacity: isButtonEnabled ? 1.0 : 0.5,
    child: Stack(
      children: [
        Icon(
          Icons.mic,
          size: 50,
          color: isButtonEnabled ? Colors.blue : Colors.grey,
        ),
        // ✅ Indicador visual cuando está deshabilitado
        if (isSomeoneTransmitting)
          Positioned(
            top: 0,
            right: 0,
            child: Container(
              padding: EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.red,
                shape: BoxShape.circle,
              ),
              child: Icon(Icons.block, size: 16, color: Colors.white),
            ),
          ),
      ],
    ),
  ),
)
```

**NOTA:** Reemplaza `widget.userId` y `widget.userName` con las variables correctas donde guardas el ID y nombre del usuario en tu app.

#### 3.4. Agregar banner superior (OPCIONAL pero recomendado)

Busca el `Scaffold` y su `body`. Modifica para agregar un `Column`:

**ANTES:**
```dart
Scaffold(
  appBar: AppBar(...),
  body: // tu contenido actual
)
```

**DESPUÉS:**
```dart
Scaffold(
  appBar: AppBar(...),
  body: Column(
    children: [
      // ✅ NUEVO: Banner cuando alguien está hablando
      if (isSomeoneTransmitting)
        Container(
          width: double.infinity,
          color: Colors.red,
          padding: EdgeInsets.all(12),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.mic, color: Colors.white, size: 20),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  '🔴 $currentSpeakerName está transmitiendo...',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ],
          ),
        ),
      
      // Tu contenido existente envuelto en Expanded
      Expanded(
        child: // tu contenido actual aquí
      ),
    ],
  ),
)
```

---

## 📋 PASO 4: Probar

### 4.1. Guardar y recargar
1. Guarda todos los archivos: **Ctrl + K, luego S**
2. Hot reload: Presiona **r** en la terminal o **Ctrl + F5**

### 4.2. Pruebas a realizar

**Test 1: Central habla → Android escucha**
1. Desde la web (central), presiona el botón de micrófono
2. En el móvil debería:
   - ✅ Aparecer banner rojo "🔴 Central está transmitiendo..."
   - ✅ Botón de micrófono gris y deshabilitado
   - ✅ Al soltar en la web, el móvil se habilita

**Test 2: Android habla → Central escucha**
1. Desde el móvil, presiona el botón de micrófono
2. En la web debería:
   - ✅ Aparecer banner rojo con el nombre del conductor
   - ✅ Botón deshabilitado
   - ✅ Al soltar, se habilita

**Test 3: Timeout de 30 segundos**
1. Mantén presionado el botón más de 30 segundos
2. Debería:
   - ✅ Detenerse automáticamente
   - ✅ Mostrar mensaje "Transmisión detenida automáticamente"
   - ✅ Permitir volver a hablar inmediatamente

**Test 4: Interrupción de emergencia**
1. Conductor habla
2. Central presiona "🚨 Interrumpir Transmisión"
3. Conductor debería:
   - ✅ Recibir mensaje "Transmisión interrumpida por la central"
   - ✅ Su grabación se detiene

---

## 🐛 Solución de Problemas

### Error: `The getter 'userId' isn't defined`

**Causa:** No se encontró la variable con el ID del usuario.

**Solución:** Busca cómo guardas el ID del usuario en tu app. Puede ser:
- `SharedPreferences`
- Variable global
- Parámetro del widget
- Provider/Bloc

Reemplaza `widget.userId` con tu variable real.

### Error: `_transmissionStatusController is already closed`

**Causa:** Intentaste usar el stream después de cerrar la conexión.

**Solución:** Verifica que estás cancelando la suscripción correctamente en dispose:

```dart
@override
void dispose() {
  audioService.transmissionStatusStream.listen(null); // Cancelar
  super.dispose();
}
```

### El botón no se deshabilita

**Causa:** El listener del stream no se está ejecutando.

**Solución:**
1. Verifica que agregaste el listener en `initState()`
2. Asegúrate de que el `audioService` esté inicializado
3. Agrega prints para debug:

```dart
audioService.transmissionStatusStream.listen((status) {
  print('DEBUG: Status recibido: $status');  // ✅ Agregar esto
  setState(() {
    // ...
  });
});
```

### No recibo los mensajes del WebSocket

**Causa:** El tipo de mensaje no coincide.

**Solución:** Agrega un log en el listener principal:

```dart
_channel!.stream.listen((message) {
  final data = jsonDecode(message);
  print('DEBUG WebSocket recibido: ${data['type']}');  // ✅ Agregar esto
  
  if (type == 'audio_transmission_status') {
    // ...
  }
});
```

---

## 📚 Resumen de Cambios

### Archivos Modificados:
1. ✅ `lib/services/websocket_service.dart` (o `audio_service.dart`)
   - Variables de estado
   - Handler de `audio_transmission_status`
   - Funciones `notifyTransmissionStarted()` / `notifyTransmissionStopped()`
   
2. ✅ `lib/screens/main_screen.dart` (o similar)
   - Variables de estado de la UI
   - Listener del stream en `initState()`
   - Modificación del botón de audio
   - Banner superior (opcional)

### Nuevas Funcionalidades:
- 🔴 Indicador visual cuando alguien habla
- 🔒 Botón deshabilitado automáticamente
- ⏱️ Timeout de 30 segundos
- 🚨 Interrupción de emergencia desde la central
- 📡 Sincronización en tiempo real

---

## ✅ Checklist Final

- [ ] Agregué las variables de estado en el servicio
- [ ] Agregué el handler `_handleTransmissionStatus`
- [ ] Agregué las funciones `notifyTransmissionStarted` / `Stopped`
- [ ] Agregué el listener en `initState()` de la UI
- [ ] Modifiqué el botón para verificar `isSomeoneTransmitting`
- [ ] Agregué las llamadas a `notifyTransmissionStarted` / `Stopped`
- [ ] Agregué el banner superior (opcional)
- [ ] Probé desde web → móvil
- [ ] Probé desde móvil → web
- [ ] Probé el timeout de 30 segundos
- [ ] Probé la interrupción de emergencia

---

## 🆘 ¿Necesitas Ayuda?

Si encuentras algún error:

1. **Copia el error completo**
2. **Dime qué archivo estás editando**
3. **Muestra el código alrededor de la línea con error**

¡Y te ayudo a solucionarlo! 🚀

---

**Creado:** 8 de enero de 2026
**Versión:** 1.0
**Backend:** Django Channels + WebSocket
**Frontend:** Flutter (Android)
