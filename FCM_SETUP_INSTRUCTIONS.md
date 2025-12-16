# 🔥 CONFIGURACIÓN DE FIREBASE CLOUD MESSAGING (FCM)

## 📋 **PASO 1: Crear Proyecto en Firebase**

1. **Ve a:** https://console.firebase.google.com/
2. **Clic en:** "Agregar proyecto" o "Add project"
3. **Nombre del proyecto:** `TaxiDeAquiPalla` (o el que prefieras)
4. **Desactiva Google Analytics** (opcional, no es necesario para FCM)
5. **Clic en:** "Crear proyecto"

---

## 📱 **PASO 2: Configurar App Android en Firebase**

1. **En el proyecto Firebase**, clic en el ícono de Android
2. **Package name:** `com.deaquipalla.taxi` (o el que uses en Flutter)
3. **App nickname:** `Taxi De Aquí Pa'llá`
4. **SHA-1:** (opcional por ahora)
5. **Descargar `google-services.json`** y guardarlo para Flutter

---

## 🔑 **PASO 3: Obtener Credenciales del Servidor**

### **Opción A: Archivo de Credenciales (Recomendado para desarrollo)**

1. **En Firebase Console**, ve a **⚙️ Project Settings**
2. **Ve a la pestaña:** "Service accounts"
3. **Clic en:** "Generate new private key"
4. **Descarga el archivo JSON** (será algo como `taxi-deaquipalla-firebase-adminsdk-xxxxx.json`)
5. **Guarda el archivo en:** `c:\Users\H P\OneDrive\Imágenes\virtual\proyecto_completo\firebase-credentials.json`

### **Opción B: Variable de Entorno (Recomendado para producción)**

1. **Abre el archivo JSON** descargado en el paso anterior
2. **Copia TODO el contenido** del archivo
3. **En Railway**, ve a tu proyecto → Variables
4. **Crea una nueva variable:**
   - **Nombre:** `FIREBASE_CREDENTIALS_JSON`
   - **Valor:** Pega TODO el contenido del JSON (incluyendo las llaves `{}`)

---

## ⚙️ **PASO 4: Configurar Django Settings**

Abre `taxi_project/settings.py` y agrega al final:

```python
# =====================================================
# FIREBASE CLOUD MESSAGING (FCM)
# =====================================================

# Opción 1: Usar archivo local (desarrollo)
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# Opción 2: Usar variable de entorno (producción)
# La variable FIREBASE_CREDENTIALS_JSON se configura en Railway
# El sistema automáticamente detectará cuál usar
```

---

## 📦 **PASO 5: Instalar Dependencias**

Ejecuta en tu terminal:

```bash
pip install firebase-admin
```

Actualiza `requirements.txt`:

```bash
pip freeze > requirements.txt
```

---

## 🗄️ **PASO 6: Aplicar Migraciones**

```bash
python manage.py migrate
```

Esto creará la tabla `FCMToken` en la base de datos.

---

## 🧪 **PASO 7: Probar FCM**

### **Desde Python Shell:**

```bash
python manage.py shell
```

```python
from taxis.fcm_notifications import initialize_firebase, send_fcm_notification
from django.contrib.auth import get_user_model

# Verificar inicialización
initialize_firebase()

# Obtener un usuario
User = get_user_model()
user = User.objects.get(username='carlos')

# Enviar notificación de prueba
result = send_fcm_notification(
    user=user,
    title='🧪 Prueba FCM',
    body='Si ves esto, FCM funciona correctamente',
    data={'type': 'test'}
)

print(result)
```

### **Desde la API:**

```bash
# 1. Login
curl -X POST https://taxis-deaquipalla.up.railway.app/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "carlos", "password": "tu_password"}'

# 2. Registrar token FCM (desde Flutter)
curl -X POST https://taxis-deaquipalla.up.railway.app/api/fcm/register/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{
    "token": "fcm_token_from_flutter",
    "platform": "android",
    "device_id": "unique_device_id"
  }'

# 3. Enviar notificación de prueba
curl -X POST https://taxis-deaquipalla.up.railway.app/api/fcm/test/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -d '{
    "title": "Prueba",
    "body": "Mensaje de prueba"
  }'
```

---

## 📱 **PASO 8: Integrar en Flutter**

### **1. Agregar dependencias en `pubspec.yaml`:**

```yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  flutter_local_notifications: ^16.3.0
```

### **2. Configurar Firebase en Flutter:**

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

// En main.dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  await Firebase.initializeApp();
  
  // Configurar FCM
  FirebaseMessaging messaging = FirebaseMessaging.instance;
  
  // Solicitar permisos
  NotificationSettings settings = await messaging.requestPermission(
    alert: true,
    badge: true,
    sound: true,
  );
  
  // Obtener token
  String? token = await messaging.getToken();
  print('FCM Token: $token');
  
  // Registrar token en backend
  if (token != null) {
    await registerFCMToken(token);
  }
  
  runApp(MyApp());
}

// Función para registrar token
Future<void> registerFCMToken(String token) async {
  final dio = Dio();
  dio.options.headers['Authorization'] = 'Token YOUR_AUTH_TOKEN';
  
  await dio.post(
    'https://taxis-deaquipalla.up.railway.app/api/fcm/register/',
    data: {
      'token': token,
      'platform': 'android',
      'device_id': 'unique_device_id',
    },
  );
}
```

### **3. Manejar notificaciones en Flutter:**

```dart
// Escuchar notificaciones en foreground
FirebaseMessaging.onMessage.listen((RemoteMessage message) {
  print('Notificación recibida: ${message.notification?.title}');
  
  // Mostrar notificación local
  showLocalNotification(message);
});

// Manejar tap en notificación
FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
  print('Notificación tocada: ${message.data}');
  
  // Navegar a la pantalla correspondiente
  if (message.data['type'] == 'new_ride') {
    Navigator.pushNamed(context, '/ride/${message.data['ride_id']}');
  }
});
```

---

## 🔄 **PASO 9: Actualizar Consumers para usar FCM**

Los consumers ya están preparados para usar tanto Web Push como FCM. Para activar FCM:

1. **Abre `taxis/consumers.py`**
2. **Importa las funciones FCM:**

```python
from .fcm_notifications import (
    send_chat_message_notification_fcm,
    send_audio_message_notification_fcm
)
```

3. **En `ChatConsumer.receive()`, agrega:**

```python
# Enviar notificación FCM además de Web Push
try:
    send_chat_message_notification_fcm(
        sender=self.user,
        recipient=recipient_user,
        message=message
    )
except Exception as e:
    logger.error(f"Error enviando FCM: {e}")
```

---

## 📊 **ENDPOINTS DISPONIBLES**

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/fcm/register/` | POST | Registrar token FCM |
| `/api/fcm/unregister/` | POST | Desregistrar token FCM |
| `/api/fcm/test/` | POST | Enviar notificación de prueba |

---

## 🔍 **VERIFICAR CONFIGURACIÓN**

### **Checklist:**

- [ ] Proyecto Firebase creado
- [ ] App Android configurada en Firebase
- [ ] `google-services.json` descargado
- [ ] Credenciales del servidor descargadas
- [ ] Variable `FIREBASE_CREDENTIALS_JSON` configurada en Railway
- [ ] `firebase-admin` instalado
- [ ] Migraciones aplicadas
- [ ] Modelo `FCMToken` visible en Django Admin
- [ ] Endpoints FCM funcionando
- [ ] Flutter configurado con Firebase
- [ ] Token FCM registrado desde Flutter
- [ ] Notificación de prueba recibida

---

## ❌ **TROUBLESHOOTING**

### **Error: "Firebase no está inicializado"**

**Solución:**
1. Verifica que el archivo `firebase-credentials.json` existe
2. O verifica que la variable `FIREBASE_CREDENTIALS_JSON` está configurada en Railway
3. Reinicia el servidor Django

### **Error: "Token inválido"**

**Solución:**
1. El token FCM puede expirar
2. Solicita un nuevo token en Flutter
3. Registra el nuevo token en el backend

### **No llegan notificaciones**

**Solución:**
1. Verifica que el token está registrado: `FCMToken.objects.filter(user=user)`
2. Verifica que `is_active=True`
3. Verifica los logs del servidor
4. Verifica que Firebase está correctamente configurado

---

## 📚 **RECURSOS ADICIONALES**

- [Firebase Console](https://console.firebase.google.com/)
- [Firebase Admin SDK - Python](https://firebase.google.com/docs/admin/setup)
- [FlutterFire - Firebase Messaging](https://firebase.flutter.dev/docs/messaging/overview/)
- [FCM HTTP v1 API](https://firebase.google.com/docs/cloud-messaging/http-server-ref)

---

## 🎯 **PRÓXIMOS PASOS**

1. ✅ Configurar Firebase (este documento)
2. ✅ Instalar dependencias
3. ✅ Aplicar migraciones
4. ✅ Configurar Flutter
5. ⏳ Probar notificaciones
6. ⏳ Integrar con WebSockets
7. ⏳ Desplegar a producción

---

## 💡 **NOTAS IMPORTANTES**

- **Web Push vs FCM:** Web Push solo funciona en navegadores. FCM funciona en apps nativas.
- **Múltiples dispositivos:** Un usuario puede tener varios tokens FCM (un token por dispositivo).
- **Tokens expirados:** Los tokens FCM pueden expirar. El sistema automáticamente los desactiva.
- **Producción:** Usa variables de entorno en Railway, NO subas el archivo JSON a Git.

---

**¿Necesitas ayuda?** Revisa los logs del servidor o contacta al equipo de desarrollo.
