# 📱 API REST - Documentación para Flutter

## 🌐 Base URL
```
Production: https://taxis-deaquipalla.up.railway.app/api/
Development: http://localhost:8000/api/
```

## 🔐 Autenticación

Todos los endpoints (excepto login y register) requieren autenticación con Token.

### Headers requeridos:
```http
Authorization: Token YOUR_TOKEN_HERE
Content-Type: application/json
```

---

## 📋 **ENDPOINTS DISPONIBLES**

### 1️⃣ **AUTENTICACIÓN**

#### **Login**
```http
POST /api/login/
```

**Request Body:**
```json
{
  "username": "carlos",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "message": "Inicio de sesión exitoso.",
  "user_id": 11,
  "role": "driver",
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
}
```

**Response (401 Unauthorized):**
```json
{
  "error": "Usuario o contraseña incorrectos."
}
```

---

### 2️⃣ **REGISTRO**

#### **Registrar Conductor**
```http
POST /api/register/driver/
```

**Request Body:**
```json
{
  "username": "nuevo_conductor",
  "email": "conductor@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone_number": "+593987654321",
  "plate_number": "ABC-1234",
  "vehicle_description": "Toyota Corolla 2020 Blanco"
}
```

**Response (201 Created):**
```json
{
  "message": "Conductor registrado exitosamente",
  "user": {
    "id": 15,
    "username": "nuevo_conductor",
    "email": "conductor@example.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "full_name": "Juan Pérez",
    "role": "driver",
    "phone_number": "+593987654321",
    "profile_picture": null
  }
}
```

#### **Registrar Cliente**
```http
POST /api/register/customer/
```

**Request Body:**
```json
{
  "username": "nuevo_cliente",
  "email": "cliente@example.com",
  "password": "password123",
  "password_confirm": "password123",
  "first_name": "María",
  "last_name": "González",
  "phone_number": "+593987654321"
}
```

---

### 3️⃣ **PERFIL**

#### **Obtener Perfil**
```http
GET /api/profile/
```

**Response (200 OK):**
```json
{
  "id": 11,
  "username": "carlos",
  "email": "carlos@example.com",
  "first_name": "Carlos",
  "last_name": "Cedeño Martinez",
  "full_name": "Carlos Cedeño Martinez",
  "role": "driver",
  "phone_number": "+593987654321",
  "national_id": "0987654321",
  "profile_picture": "/media/profile_pics/carlos.jpg",
  "last_latitude": -2.1894128,
  "last_longitude": -79.8890662,
  "average_rating": 4.5,
  "total_ratings": 12
}
```

#### **Actualizar Perfil**
```http
PATCH /api/profile/
```

**Request Body (partial update):**
```json
{
  "first_name": "Carlos Alberto",
  "phone_number": "+593999888777"
}
```

#### **Subir Foto de Perfil**
```http
POST /api/profile/upload-picture/
Content-Type: multipart/form-data
```

**Form Data:**
```
picture: [FILE]
```

#### **Estadísticas del Usuario**
```http
GET /api/profile/stats/
```

**Response (Conductor):**
```json
{
  "total_rides": 45,
  "completed_rides": 40,
  "canceled_rides": 3,
  "in_progress_rides": 2,
  "total_earnings": 450.50,
  "average_rating": 4.5,
  "total_ratings": 12
}
```

**Response (Cliente):**
```json
{
  "total_rides": 20,
  "completed_rides": 18,
  "canceled_rides": 2,
  "pending_rides": 0,
  "total_spent": 180.00
}
```

---

### 4️⃣ **CONDUCTORES**

#### **Listar Conductores**
```http
GET /api/drivers/
```

**Query Parameters:**
- `search` - Buscar por nombre o placa

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "plate_number": "ABC-1234",
    "vehicle_description": "Toyota Corolla 2020 Blanco",
    "latitude": -2.1894128,
    "longitude": -79.8890662,
    "updated_at": "2025-12-16T10:30:00Z",
    "direccion_origen": "Guayaquil",
    "driver": {
      "id": 11,
      "username": "carlos",
      "email": "carlos@example.com",
      "first_name": "Carlos",
      "last_name": "Cedeño Martinez",
      "full_name": "Carlos Cedeño Martinez",
      "role": "driver",
      "phone_number": "+593987654321",
      "profile_picture": "/media/profile_pics/carlos.jpg"
    },
    "driver_name": "Carlos Cedeño Martinez"
  }
]
```

#### **Detalle de Conductor**
```http
GET /api/drivers/{id}/
```

#### **Conductores Cercanos**
```http
GET /api/drivers/nearby/?lat=-2.1894128&lon=-79.8890662&radius=5
```

**Query Parameters:**
- `lat` (required) - Latitud
- `lon` (required) - Longitud
- `radius` (optional) - Radio en km (default: 5)

---

### 5️⃣ **CARRERAS (RIDES)**

#### **Listar Carreras**
```http
GET /api/rides/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "customer_name": "María González",
    "driver_name": "Carlos Cedeño Martinez",
    "origin": "Av. 9 de Octubre y Malecón",
    "status": "in_progress",
    "status_display": "En progreso",
    "price": "15.50",
    "created_at": "2025-12-16T10:00:00Z",
    "start_time": "2025-12-16T10:05:00Z",
    "end_time": null,
    "destinations_count": 2
  }
]
```

#### **Detalle de Carrera**
```http
GET /api/rides/{id}/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "customer": {
    "id": 5,
    "username": "maria",
    "email": "maria@example.com",
    "first_name": "María",
    "last_name": "González",
    "full_name": "María González",
    "role": "customer",
    "phone_number": "+593987654321",
    "profile_picture": null
  },
  "driver": {
    "id": 11,
    "username": "carlos",
    "email": "carlos@example.com",
    "first_name": "Carlos",
    "last_name": "Cedeño Martinez",
    "full_name": "Carlos Cedeño Martinez",
    "role": "driver",
    "phone_number": "+593987654321",
    "profile_picture": "/media/profile_pics/carlos.jpg"
  },
  "origin": "Av. 9 de Octubre y Malecón",
  "origin_address": "Av. 9 de Octubre y Malecón, Guayaquil",
  "origin_latitude": -2.1894128,
  "origin_longitude": -79.8890662,
  "destinations": [
    {
      "id": 1,
      "destination": "Mall del Sol",
      "destination_latitude": -2.2045,
      "destination_longitude": -79.8976,
      "order": 0
    },
    {
      "id": 2,
      "destination": "Aeropuerto José Joaquín de Olmedo",
      "destination_latitude": -2.1574,
      "destination_longitude": -79.8838,
      "order": 1
    }
  ],
  "start_time": "2025-12-16T10:05:00Z",
  "end_time": null,
  "price": "15.50",
  "status": "in_progress",
  "status_display": "En progreso",
  "created_at": "2025-12-16T10:00:00Z",
  "notified": true
}
```

#### **Crear Carrera**
```http
POST /api/rides/
```

**Request Body:**
```json
{
  "origin": "Av. 9 de Octubre y Malecón",
  "origin_latitude": -2.1894128,
  "origin_longitude": -79.8890662,
  "destinations": [
    {
      "destination": "Mall del Sol",
      "destination_latitude": -2.2045,
      "destination_longitude": -79.8976,
      "order": 0
    }
  ],
  "price": "15.50"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "origin": "Av. 9 de Octubre y Malecón",
  "origin_latitude": -2.1894128,
  "origin_longitude": -79.8890662,
  "destinations": [
    {
      "id": 1,
      "destination": "Mall del Sol",
      "destination_latitude": -2.2045,
      "destination_longitude": -79.8976,
      "order": 0
    }
  ],
  "price": "15.50"
}
```

#### **Aceptar Carrera (Solo Conductores)**
```http
POST /api/rides/{id}/accept/
```

**Response (200 OK):**
```json
{
  "id": 1,
  "status": "accepted",
  ...
}
```

#### **Iniciar Carrera (Solo Conductor Asignado)**
```http
POST /api/rides/{id}/start/
```

#### **Completar Carrera (Solo Conductor Asignado)**
```http
POST /api/rides/{id}/complete/
```

#### **Cancelar Carrera**
```http
POST /api/rides/{id}/cancel/
```

#### **Carreras Disponibles (Solo Conductores)**
```http
GET /api/rides/available/
```

**Response:** Lista de carreras con `status=requested`

#### **Carreras Activas**
```http
GET /api/rides/active/
```

**Response:** Carreras con status `accepted` o `in_progress` del usuario

---

### 6️⃣ **CALIFICACIONES**

#### **Listar Calificaciones**
```http
GET /api/ratings/
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "ride": 1,
    "ride_info": {
      "id": 1,
      "origin": "Av. 9 de Octubre y Malecón",
      "status": "completed",
      "created_at": "2025-12-16T10:00:00Z"
    },
    "rater": 5,
    "rater_name": "María González",
    "rated": 11,
    "rated_name": "Carlos Cedeño Martinez",
    "rating": 5,
    "stars_display": "⭐⭐⭐⭐⭐",
    "comment": "Excelente servicio, muy puntual",
    "created_at": "2025-12-16T11:00:00Z"
  }
]
```

#### **Crear Calificación**
```http
POST /api/ratings/
```

**Request Body:**
```json
{
  "ride": 1,
  "rated": 11,
  "rating": 5,
  "comment": "Excelente servicio, muy puntual"
}
```

**Validaciones:**
- Solo puedes calificar carreras completadas
- Solo puedes calificar si eres parte de la carrera
- No puedes calificar la misma carrera dos veces
- Rating debe estar entre 1 y 5

#### **Calificaciones Recibidas**
```http
GET /api/ratings/received/
```

**Response (200 OK):**
```json
{
  "average": 4.5,
  "total": 12,
  "ratings": [...]
}
```

#### **Calificaciones Dadas**
```http
GET /api/ratings/given/
```

---

### 7️⃣ **UBICACIÓN**

#### **Actualizar Ubicación**
```http
POST /api/update-location/
```

**Request Body:**
```json
{
  "latitude": -2.1894128,
  "longitude": -79.8890662
}
```

**Response (200 OK):**
```json
{
  "message": "Ubicación actualizada exitosamente.",
  "latitude": -2.1894128,
  "longitude": -79.8890662
}
```

---

### 8️⃣ **BADGES Y NOTIFICACIONES**

#### **Contador de Badges**
```http
GET /api/badge-count/
```

**Response (200 OK):**
```json
{
  "unread_count": 5
}
```

#### **Limpiar Badge**
```http
POST /api/clear-badge/
```

#### **Marcar Mensajes como Leídos**
```http
POST /api/mark-messages-read/
```

**Request Body:**
```json
{
  "sender_id": 11
}
```

---

## 🔌 **WEBSOCKETS**

### **Chat en Tiempo Real**
```
wss://taxis-deaquipalla.up.railway.app/ws/chat/
```

**Mensaje de envío:**
```json
{
  "type": "chat_message",
  "message": "Hola, ¿cómo estás?",
  "recipient_id": 11
}
```

**Mensaje recibido:**
```json
{
  "type": "chat_message",
  "senderId": 5,
  "senderName": "María González",
  "message": "Hola, ¿cómo estás?",
  "timestamp": "2025-12-16T10:30:00Z"
}
```

### **Audio Walkie-Talkie**
```
wss://taxis-deaquipalla.up.railway.app/ws/audio/conductores/
```

**Enviar audio:**
```json
{
  "type": "audio_message",
  "audio": "BASE64_ENCODED_AUDIO_DATA",
  "senderId": 11,
  "senderName": "Carlos Cedeño Martinez"
}
```

**Recibir audio:**
```json
{
  "type": "audio_broadcast",
  "senderId": 11,
  "senderRole": "driver",
  "audio": "BASE64_ENCODED_AUDIO_DATA"
}
```

---

## 📊 **CÓDIGOS DE ESTADO**

| Código | Significado |
|--------|-------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado exitosamente |
| 400 | Bad Request - Error en los datos enviados |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 500 | Internal Server Error - Error del servidor |

---

## 🎯 **ROLES DE USUARIO**

| Role | Descripción | Permisos |
|------|-------------|----------|
| `customer` | Cliente | Solicitar carreras, calificar conductores |
| `driver` | Conductor | Aceptar carreras, actualizar ubicación |
| `admin` | Administrador | Acceso completo |

---

## 🚀 **EJEMPLO DE USO EN FLUTTER**

```dart
import 'package:dio/dio.dart';

class TaxiApiClient {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'https://taxis-deaquipalla.up.railway.app/api/',
    headers: {'Content-Type': 'application/json'},
  ));
  
  String? _token;
  
  // Login
  Future<Map<String, dynamic>> login(String username, String password) async {
    final response = await _dio.post('login/', data: {
      'username': username,
      'password': password,
    });
    
    _token = response.data['token'];
    _dio.options.headers['Authorization'] = 'Token $_token';
    
    return response.data;
  }
  
  // Obtener perfil
  Future<Map<String, dynamic>> getProfile() async {
    final response = await _dio.get('profile/');
    return response.data;
  }
  
  // Crear carrera
  Future<Map<String, dynamic>> createRide({
    required String origin,
    required double originLat,
    required double originLon,
    required List<Map<String, dynamic>> destinations,
    required double price,
  }) async {
    final response = await _dio.post('rides/', data: {
      'origin': origin,
      'origin_latitude': originLat,
      'origin_longitude': originLon,
      'destinations': destinations,
      'price': price,
    });
    
    return response.data;
  }
  
  // Listar carreras activas
  Future<List<dynamic>> getActiveRides() async {
    final response = await _dio.get('rides/active/');
    return response.data;
  }
}
```

---

## 📝 **NOTAS IMPORTANTES**

1. **Autenticación:** Todos los endpoints requieren token excepto login y register
2. **Paginación:** Los listados grandes están paginados (usar `?page=2`)
3. **Filtros:** Usa `?search=texto` para buscar
4. **WebSockets:** Requieren autenticación en el handshake
5. **Push Notifications:** Actualmente usa Web Push (migrar a FCM para móvil)

---

## 🔧 **PRÓXIMOS PASOS**

- [ ] Implementar paginación en todos los listados
- [ ] Migrar de Web Push a Firebase Cloud Messaging
- [ ] Agregar Swagger/OpenAPI para documentación interactiva
- [ ] Implementar rate limiting
- [ ] Agregar versionado de API (v1, v2)
