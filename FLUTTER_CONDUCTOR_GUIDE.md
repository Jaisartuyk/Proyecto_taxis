# 🚕 GUÍA COMPLETA: APP FLUTTER PARA CONDUCTORES
## Taxi "De Aquí Pa'llá" - Interfaz Profesional

---

## 📋 **ÍNDICE**

1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Configuración Inicial](#configuración-inicial)
3. [Arquitectura y Patrones](#arquitectura-y-patrones)
4. [Pantallas y Funcionalidades](#pantallas-y-funcionalidades)
5. [Servicios y API](#servicios-y-api)
6. [Instalación Paso a Paso](#instalación-paso-a-paso)

---

## 📁 **ESTRUCTURA DEL PROYECTO**

```
lib/
├── main.dart                          # Punto de entrada
├── config/
│   ├── theme.dart                     # Tema y colores
│   ├── routes.dart                    # Rutas de navegación
│   └── constants.dart                 # Constantes globales
├── models/
│   ├── user_model.dart                # Modelo de usuario
│   ├── ride_model.dart                # Modelo de carrera
│   ├── rating_model.dart              # Modelo de calificación
│   └── location_model.dart            # Modelo de ubicación
├── services/
│   ├── api_service.dart               # Cliente HTTP (Dio)
│   ├── auth_service.dart              # Autenticación
│   ├── fcm_service.dart               # Firebase Cloud Messaging
│   ├── websocket_service.dart         # WebSocket para tiempo real
│   ├── location_service.dart          # Geolocalización
│   └── storage_service.dart           # Almacenamiento local
├── providers/
│   ├── auth_provider.dart             # Estado de autenticación
│   ├── ride_provider.dart             # Estado de carreras
│   ├── location_provider.dart         # Estado de ubicación
│   └── notification_provider.dart     # Estado de notificaciones
├── screens/
│   ├── splash_screen.dart             # Pantalla de carga
│   ├── auth/
│   │   ├── login_screen.dart          # Login
│   │   ├── register_screen.dart       # Registro
│   │   └── forgot_password_screen.dart # Recuperar contraseña
│   ├── home/
│   │   ├── home_screen.dart           # Pantalla principal
│   │   ├── available_rides_screen.dart # Carreras disponibles
│   │   └── active_ride_screen.dart    # Carrera activa
│   ├── profile/
│   │   ├── profile_screen.dart        # Perfil del conductor
│   │   ├── edit_profile_screen.dart   # Editar perfil
│   │   └── stats_screen.dart          # Estadísticas
│   ├── history/
│   │   ├── ride_history_screen.dart   # Historial de carreras
│   │   └── ride_detail_screen.dart    # Detalle de carrera
│   ├── earnings/
│   │   └── earnings_screen.dart       # Ganancias
│   ├── ratings/
│   │   └── ratings_screen.dart        # Calificaciones recibidas
│   └── settings/
│       └── settings_screen.dart       # Configuración
└── widgets/
    ├── custom_button.dart             # Botón personalizado
    ├── custom_text_field.dart         # Campo de texto
    ├── ride_card.dart                 # Tarjeta de carrera
    ├── loading_indicator.dart         # Indicador de carga
    └── custom_app_bar.dart            # AppBar personalizado
```

---

## 🎨 **FUNCIONALIDADES POR PANTALLA**

### **1. 🔐 LOGIN (login_screen.dart)**
- Email/teléfono y contraseña
- Validación de campos
- Recordar sesión
- Recuperar contraseña
- Registro de nuevo conductor

### **2. 🏠 HOME (home_screen.dart)**
- Mapa con ubicación actual
- Estado: Disponible/Ocupado/Desconectado
- Botón de pánico
- Carreras cercanas
- Notificaciones en tiempo real
- Chat con central

### **3. 📋 CARRERAS DISPONIBLES (available_rides_screen.dart)**
- Lista de carreras cercanas
- Distancia y tiempo estimado
- Precio estimado
- Aceptar/Rechazar carrera
- Filtros (distancia, precio)

### **4. 🚗 CARRERA ACTIVA (active_ride_screen.dart)**
- Mapa con ruta
- Información del cliente
- Botón de llamada/chat
- Estado: En camino/Recogido/Completado
- Botón de emergencia
- Finalizar carrera

### **5. 👤 PERFIL (profile_screen.dart)**
- Foto de perfil
- Nombre y datos personales
- Calificación promedio
- Total de carreras
- Editar perfil
- Cerrar sesión

### **6. 📊 ESTADÍSTICAS (stats_screen.dart)**
- Carreras del día/semana/mes
- Ganancias del día/semana/mes
- Calificación promedio
- Tiempo en línea
- Gráficos de rendimiento

### **7. 💰 GANANCIAS (earnings_screen.dart)**
- Ganancias totales
- Ganancias por período
- Desglose por carrera
- Historial de pagos

### **8. ⭐ CALIFICACIONES (ratings_screen.dart)**
- Calificaciones recibidas
- Comentarios de clientes
- Promedio general
- Filtros por fecha

### **9. 📜 HISTORIAL (ride_history_screen.dart)**
- Lista de carreras completadas
- Búsqueda por fecha
- Detalles de cada carrera
- Exportar historial

---

## 🔧 **SERVICIOS PRINCIPALES**

### **API Service (api_service.dart)**
```dart
- login(email, password)
- register(userData)
- getProfile()
- updateProfile(data)
- getAvailableRides()
- acceptRide(rideId)
- startRide(rideId)
- completeRide(rideId)
- cancelRide(rideId, reason)
- getRideHistory()
- getEarnings()
- getRatings()
- updateLocation(lat, lon)
```

### **WebSocket Service (websocket_service.dart)**
```dart
- connect()
- disconnect()
- sendMessage(message)
- onNewRide(callback)
- onRideUpdate(callback)
- onChatMessage(callback)
```

### **FCM Service (fcm_service.dart)**
```dart
- initialize()
- getToken()
- registerToken(token)
- onNotification(callback)
```

### **Location Service (location_service.dart)**
```dart
- getCurrentLocation()
- startTracking()
- stopTracking()
- updateLocationToServer()
```

---

## 🎨 **DISEÑO Y TEMA**

### **Colores Principales**
```dart
Primary: #FF6B00 (Naranja)
Secondary: #FFB300 (Amarillo)
Background: #FFFFFF
Surface: #F5F5F5
Error: #D32F2F
Success: #388E3C
Text Primary: #212121
Text Secondary: #757575
```

### **Tipografía**
```dart
Font Family: Poppins
Heading 1: 32px, Bold
Heading 2: 24px, SemiBold
Heading 3: 20px, Medium
Body 1: 16px, Regular
Body 2: 14px, Regular
Caption: 12px, Regular
```

---

## 📦 **DEPENDENCIAS NECESARIAS**

```yaml
dependencies:
  flutter:
    sdk: flutter
  
  # Estado
  provider: ^6.1.1
  
  # HTTP y API
  dio: ^5.4.0
  
  # Firebase
  firebase_core: ^2.24.0
  firebase_messaging: ^14.7.0
  
  # Mapas y Ubicación
  google_maps_flutter: ^2.5.0
  geolocator: ^10.1.0
  geocoding: ^2.1.1
  
  # WebSockets
  web_socket_channel: ^2.4.0
  
  # Almacenamiento
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  
  # UI
  flutter_svg: ^2.0.9
  cached_network_image: ^3.3.0
  shimmer: ^3.0.0
  
  # Utilidades
  intl: ^0.18.1
  url_launcher: ^6.2.2
  image_picker: ^1.0.5
  permission_handler: ^11.1.0
  
  # Notificaciones locales
  flutter_local_notifications: ^16.3.0
```

---

## 🚀 **INSTALACIÓN PASO A PASO**

### **PASO 1: Crear Proyecto Flutter**

```bash
flutter create taxi_conductor_app
cd taxi_conductor_app
```

### **PASO 2: Actualizar pubspec.yaml**

Copia todas las dependencias de arriba en `pubspec.yaml`

```bash
flutter pub get
```

### **PASO 3: Configurar Firebase**

1. Descarga `google-services.json` de Firebase Console
2. Colócalo en `android/app/`
3. Modifica `android/build.gradle`:

```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

4. Modifica `android/app/build.gradle`:

```gradle
apply plugin: 'com.google.gms.google-services'
```

### **PASO 4: Configurar Permisos Android**

En `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET"/>
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION"/>
<uses-permission android:name="android.permission.ACCESS_BACKGROUND_LOCATION"/>
<uses-permission android:name="android.permission.FOREGROUND_SERVICE"/>
<uses-permission android:name="android.permission.CAMERA"/>
```

### **PASO 5: Crear Estructura de Carpetas**

```bash
mkdir lib/config lib/models lib/services lib/providers lib/screens lib/widgets
mkdir lib/screens/auth lib/screens/home lib/screens/profile lib/screens/history lib/screens/earnings lib/screens/ratings lib/screens/settings
```

---

## 📝 **ARCHIVOS PRINCIPALES A CREAR**

### **1. config/constants.dart**

```dart
class AppConstants {
  // API
  static const String baseUrl = 'https://taxis-deaquipalla.up.railway.app/api';
  static const String wsUrl = 'wss://taxis-deaquipalla.up.railway.app/ws';
  
  // Storage Keys
  static const String authTokenKey = 'auth_token';
  static const String userDataKey = 'user_data';
  
  // Timeouts
  static const Duration apiTimeout = Duration(seconds: 30);
  static const Duration wsReconnectDelay = Duration(seconds: 5);
}
```

### **2. config/theme.dart**

```dart
import 'package:flutter/material.dart';

class AppTheme {
  static const Color primaryColor = Color(0xFFFF6B00);
  static const Color secondaryColor = Color(0xFFFFB300);
  
  static ThemeData lightTheme = ThemeData(
    primaryColor: primaryColor,
    colorScheme: ColorScheme.fromSeed(
      seedColor: primaryColor,
      secondary: secondaryColor,
    ),
    fontFamily: 'Poppins',
    useMaterial3: true,
  );
}
```

### **3. services/api_service.dart**

```dart
import 'package:dio/dio.dart';
import '../config/constants.dart';

class ApiService {
  final Dio _dio = Dio(
    BaseOptions(
      baseUrl: AppConstants.baseUrl,
      connectTimeout: AppConstants.apiTimeout,
      receiveTimeout: AppConstants.apiTimeout,
    ),
  );
  
  String? _authToken;
  
  void setAuthToken(String token) {
    _authToken = token;
    _dio.options.headers['Authorization'] = 'Token $token';
  }
  
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await _dio.post('/login/', data: {
      'username': username,
      'password': password,
    });
    return response.data;
  }
  
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get('/profile/');
    return response.data;
  }
  
  Future<List<dynamic>> getAvailableRides() async {
    final response = await _dio.get('/rides/available/');
    return response.data;
  }
  
  Future<Map<String, dynamic>> acceptRide(int rideId) async {
    final response = await _dio.post('/rides/$rideId/accept/');
    return response.data;
  }
  
  // ... más métodos
}
```

---

## 🎯 **FLUJO DE NAVEGACIÓN**

```
Splash Screen
    ↓
¿Autenticado?
    ├─ NO → Login Screen → Home Screen
    └─ SÍ → Home Screen
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
Carreras    Perfil    Historial
```

---

## 📱 **CARACTERÍSTICAS PRINCIPALES**

### ✅ **Implementadas en Backend**
- Login y registro
- Gestión de perfil
- Sistema de carreras (CRUD completo)
- Calificaciones
- Historial
- Notificaciones push (FCM)
- WebSockets (chat y audio)
- Geolocalización

### 🔨 **Por Implementar en Flutter**
- Interfaz de usuario
- Integración con API
- Manejo de estado
- Navegación
- Notificaciones locales
- Mapas interactivos

---

## 🔐 **SEGURIDAD**

- Token de autenticación en headers
- Almacenamiento seguro de credenciales
- Validación de permisos
- Encriptación de datos sensibles
- Timeout de sesión

---

## 📊 **MÉTRICAS Y ANALYTICS**

- Tiempo en línea
- Carreras completadas
- Ganancias por período
- Calificación promedio
- Tasa de aceptación

---

## 🆘 **FUNCIONES DE EMERGENCIA**

- Botón de pánico
- Compartir ubicación en tiempo real
- Llamada directa a central
- Historial de emergencias

---

## 📞 **SOPORTE**

- Chat con central
- Audio walkie-talkie
- Notificaciones push
- Mensajes en tiempo real

---

## 🎓 **PRÓXIMOS PASOS**

1. ✅ Configurar Firebase
2. ✅ Crear estructura de carpetas
3. ⏳ Implementar servicios
4. ⏳ Crear modelos
5. ⏳ Implementar providers
6. ⏳ Diseñar pantallas
7. ⏳ Integrar API
8. ⏳ Probar en dispositivo real

---

**¿Listo para comenzar? Sigue la guía paso a paso y tendrás una app profesional para conductores.**
