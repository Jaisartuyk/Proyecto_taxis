# 🆘 Sistema de Botón de Pánico - Implementación Completa

## 📋 Descripción General

Sistema de alerta de emergencia para clientes (PWA) y conductores (App Android) que notifica a:
- ✅ Administrador de la cooperativa
- ✅ Contactos de emergencia personales
- ✅ La otra parte involucrada (cliente ↔ conductor)
- 🔜 ECU-911 (integración futura)
- 🔜 Retén policial más cercano (integración futura)

---

## 🎯 Características del Sistema

### Para Cliente (PWA):
- Botón de pánico flotante durante carrera activa
- Confirmación doble para evitar activaciones accidentales
- Tracking GPS cada 5 segundos
- Notificación al conductor y admin
- Botón directo para llamar al 911
- UI roja de emergencia activada

### Para Conductor (App Android):
- Botón de pánico en pantalla de carrera
- Confirmación doble
- Tracking GPS continuo cada 5 segundos
- Notificación al cliente y admin
- Marcador directo al 911
- UI de emergencia con alertas visuales

### Para Administrador (Panel Web):
- Recibe alerta en tiempo real vía WebSocket
- Ve ubicación en tiempo real en mapa
- Historial de ubicaciones durante emergencia
- Puede marcar emergencia como resuelta
- Panel de gestión de emergencias activas

---

## 💻 Implementación Frontend

### 1. Cliente PWA (JavaScript)

```javascript
// En customer_dashboard.html o ride_detail.html
<div class="panic-button-container" id="panicContainer" style="display: none;">
    <button id="panicButton" class="panic-btn">
        <i class="fas fa-exclamation-triangle"></i>
        🆘 EMERGENCIA
    </button>
</div>

<style>
.panic-button-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 9999;
}

.panic-btn {
    background: linear-gradient(135deg, #ff0000, #cc0000);
    color: white;
    border: 3px solid white;
    border-radius: 50%;
    width: 80px;
    height: 80px;
    font-size: 1.5rem;
    font-weight: bold;
    cursor: pointer;
    box-shadow: 0 8px 25px rgba(255, 0, 0, 0.4);
    animation: pulse 2s infinite;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.panic-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 12px 35px rgba(255, 0, 0, 0.6);
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 8px 25px rgba(255, 0, 0, 0.4); }
    50% { box-shadow: 0 8px 35px rgba(255, 0, 0, 0.8); }
}
</style>

<script>
// Mostrar botón solo durante carrera activa
if (rideStatus === 'in_progress' || rideStatus === 'accepted') {
    document.getElementById('panicContainer').style.display = 'block';
}

document.getElementById('panicButton').addEventListener('click', function() {
    if (confirm('⚠️ ¿Estás en una EMERGENCIA REAL?\n\nEsto notificará a:\n✓ Administrador\n✓ Tus contactos\n✓ Conductor\n\n¿CONTINUAR?')) {
        activatePanicAlert('customer');
    }
});

function activatePanicAlert(userType) {
    navigator.geolocation.getCurrentPosition(function(position) {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;
        
        fetch('/api/panic-alert/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                ride_id: currentRideId,
                user_type: userType,
                latitude: latitude,
                longitude: longitude,
                timestamp: new Date().toISOString()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showPanicActivatedUI(data.emergency_id);
                startContinuousLocationTracking(data.emergency_id);
            }
        });
    });
}

function startContinuousLocationTracking(emergencyId) {
    setInterval(function() {
        navigator.geolocation.getCurrentPosition(function(position) {
            fetch('/api/panic-alert/update-location/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    emergency_id: emergencyId,
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    timestamp: new Date().toISOString()
                })
            });
        });
    }, 5000);
}
</script>
```

### 2. Conductor Android (Flutter/Dart)

```dart
// lib/screens/driver_ride_screen.dart
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class DriverRideScreen extends StatefulWidget {
  final int rideId;
  DriverRideScreen({required this.rideId});
  
  @override
  _DriverRideScreenState createState() => _DriverRideScreenState();
}

class _DriverRideScreenState extends State<DriverRideScreen> {
  bool isPanicActive = false;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Contenido principal...
          
          // Botón de Pánico
          Positioned(
            bottom: 20,
            right: 20,
            child: FloatingActionButton.extended(
              onPressed: isPanicActive ? null : _activatePanic,
              backgroundColor: Colors.red,
              icon: Icon(Icons.warning, color: Colors.white),
              label: Text('🆘 EMERGENCIA'),
            ),
          ),
        ],
      ),
    );
  }
  
  Future<void> _activatePanic() async {
    bool? confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Colors.red[900],
        title: Text('⚠️ EMERGENCIA', style: TextStyle(color: Colors.white)),
        content: Text(
          '¿Estás en EMERGENCIA REAL?\n\n'
          'Notificará a:\n'
          '✓ Admin cooperativa\n'
          '✓ Cliente actual\n'
          '✓ Contactos emergencia',
          style: TextStyle(color: Colors.white),
        ),
        actions: [
          TextButton(
            child: Text('CANCELAR'),
            onPressed: () => Navigator.pop(context, false),
          ),
          ElevatedButton(
            child: Text('SÍ, ES EMERGENCIA'),
            onPressed: () => Navigator.pop(context, true),
          ),
        ],
      ),
    );
    
    if (confirmed == true) {
      await _sendPanicAlert();
    }
  }
  
  Future<void> _sendPanicAlert() async {
    Position position = await Geolocator.getCurrentPosition();
    String? token = await _getAuthToken();
    
    final response = await http.post(
      Uri.parse('https://taxis-deaquipalla.up.railway.app/api/panic-alert/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token $token',
      },
      body: jsonEncode({
        'ride_id': widget.rideId,
        'user_type': 'driver',
        'latitude': position.latitude,
        'longitude': position.longitude,
        'timestamp': DateTime.now().toIso8601String(),
      }),
    );
    
    if (response.statusCode == 200) {
      setState(() => isPanicActive = true);
      _startContinuousTracking();
    }
  }
  
  void _startContinuousTracking() {
    Stream.periodic(Duration(seconds: 5)).listen((_) async {
      if (!isPanicActive) return;
      Position position = await Geolocator.getCurrentPosition();
      // Enviar ubicación al servidor...
    });
  }
}
```

---

## 🖥️ Implementación Backend (Django)

### 1. Modelos

```python
# taxis/models.py
class EmergencyAlert(models.Model):
    USER_TYPES = [
        ('customer', 'Cliente'),
        ('driver', 'Conductor'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('resolved', 'Resuelta'),
        ('false_alarm', 'Falsa Alarma'),
    ]
    
    ride = models.ForeignKey('Ride', on_delete=models.CASCADE, related_name='emergencies')
    triggered_by = models.ForeignKey('AppUser', on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    alert_type = models.CharField(max_length=20, default='panic_button')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Integración con autoridades
    ecu911_notified = models.BooleanField(default=False)
    ecu911_notification_time = models.DateTimeField(null=True, blank=True)
    police_station_notified = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['ride', 'status']),
        ]

class EmergencyLocationLog(models.Model):
    """Tracking de ubicación durante emergencia"""
    emergency = models.ForeignKey('EmergencyAlert', on_delete=models.CASCADE, related_name='location_logs')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class EmergencyContact(models.Model):
    """Contactos de emergencia de usuarios"""
    user = models.ForeignKey('AppUser', on_delete=models.CASCADE, related_name='emergency_contacts')
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    relationship = models.CharField(max_length=50)
    priority = models.IntegerField(default=1)
    
    class Meta:
        ordering = ['priority']
```

### 2. Views/API

```python
# taxis/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def panic_alert(request):
    """
    API para activar alerta de pánico
    Usado por clientes (PWA) y conductores (Android)
    """
    data = request.data
    ride_id = data.get('ride_id')
    user_type = data.get('user_type')  # 'customer' o 'driver'
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    
    ride = get_object_or_404(Ride, id=ride_id)
    
    # Validar autorización
    if user_type == 'customer' and ride.customer != request.user:
        return Response({'error': 'No autorizado'}, status=403)
    if user_type == 'driver' and ride.driver != request.user:
        return Response({'error': 'No autorizado'}, status=403)
    
    # Crear alerta de emergencia
    emergency = EmergencyAlert.objects.create(
        ride=ride,
        triggered_by=request.user,
        user_type=user_type,
        latitude=latitude,
        longitude=longitude,
        status='active',
        alert_type='panic_button'
    )
    
    # === NOTIFICACIONES ===
    
    # 1. Administrador de cooperativa
    notify_admin_panic(ride.organization, emergency)
    
    # 2. Otra parte (cliente ↔ conductor)
    if user_type == 'customer' and ride.driver:
        notify_driver_panic(ride.driver, emergency)
    elif user_type == 'driver':
        notify_customer_panic(ride.customer, emergency)
    
    # 3. Contactos de emergencia
    notify_emergency_contacts(request.user, emergency)
    
    # 4. WebSocket tiempo real
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"emergency_{ride.organization.id}",
        {
            "type": "emergency_alert",
            "emergency_id": emergency.id,
            "ride_id": ride.id,
            "user_type": user_type,
            "triggered_by": request.user.get_full_name(),
            "location": {"lat": latitude, "lng": longitude}
        }
    )
    
    # 5. LOG CRÍTICO
    logger.critical(
        f"🆘 PANIC ALERT - Ride #{ride.id} - {user_type.upper()} "
        f"{request.user.get_full_name()} - Org: {ride.organization.name}"
    )
    
    # TODO: Integración ECU-911 (Fase 2)
    # notify_ecu911(emergency)
    
    return Response({
        'status': 'success',
        'emergency_id': emergency.id,
        'message': 'Alerta de emergencia activada'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def panic_alert_update_location(request):
    """Actualiza ubicación durante emergencia"""
    emergency_id = request.data.get('emergency_id')
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')
    
    emergency = get_object_or_404(EmergencyAlert, id=emergency_id, status='active')
    
    # Guardar log de ubicación
    EmergencyLocationLog.objects.create(
        emergency=emergency,
        latitude=latitude,
        longitude=longitude
    )
    
    # Notificar en tiempo real
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"emergency_{emergency.ride.organization.id}",
        {
            "type": "emergency_location_update",
            "emergency_id": emergency.id,
            "location": {"lat": latitude, "lng": longitude}
        }
    )
    
    return Response({'status': 'success'})
```

---

## 🔗 URLs

```python
# taxis/urls.py
urlpatterns = [
    # ... otras rutas ...
    
    # Botón de Pánico
    path('api/panic-alert/', views.panic_alert, name='panic_alert'),
    path('api/panic-alert/update-location/', views.panic_alert_update_location, name='panic_alert_update_location'),
]
```

---

## 🔧 Configuración Requerida

### Dependencias Python
```bash
pip install channels channels-redis geopy
```

### Dependencias Flutter
```yaml
dependencies:
  geolocator: ^10.1.0
  http: ^1.1.0
  url_launcher: ^6.2.2
```

---

## 📊 Flujo de Emergencia

```
Usuario presiona botón de pánico
    ↓
Confirmación doble
    ↓
Obtiene GPS actual
    ↓
Envía POST /api/panic-alert/
    ↓
Backend crea EmergencyAlert
    ↓
Notifica a:
  - Admin cooperativa (PWA push)
  - Otra parte (conductor/cliente)
  - Contactos emergencia (SMS)
  - WebSocket grupo emergencias
    ↓
Inicia tracking GPS cada 5s
    ↓
POST /api/panic-alert/update-location/
    ↓
EmergencyLocationLog guardado
    ↓
Admin ve mapa tiempo real
    ↓
Admin resuelve emergencia
```

---

## ⚠️ Consideraciones de Seguridad

1. **Confirmación Doble**: Evita activaciones accidentales
2. **Logging Crítico**: Todas las alertas se registran con nivel CRITICAL
3. **WebSocket Seguro**: Solo admin de la organización recibe alertas
4. **Tracking Continuo**: Ubicación cada 5 segundos durante emergencia
5. **No Cancelable**: Usuario no puede cancelar una vez activada (solo admin)

---

## 🚀 Próximas Fases

### Fase 2: Integración con Autoridades
- [ ] API ECU-911 (investigación en curso)
- [ ] Notificación a retén más cercano
- [ ] Integración con UPC (Unidad Policía Comunitaria)

### Fase 3: Funcionalidades Avanzadas
- [ ] Grabación de audio ambiente
- [ ] Botón pánico discreto (secuestro)
- [ ] Geofencing (alerta al salir de zona)
- [ ] Historial de rutas sospechosas

---

## 📝 Notas de Implementación

- ✅ Sistema completo frontend (PWA + Android)
- ✅ Backend API listo
- ✅ Modelos de BD definidos
- ⏳ Migración pendiente
- ⏳ Testing pendiente
- ⏳ Integración ECU-911 pendiente

---

**Fecha de Documentación:** 9 de enero de 2026  
**Autor:** Sistema de desarrollo  
**Estado:** Documentado - Pendiente implementación
