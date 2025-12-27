# 💬 INTEGRACIÓN RÁPIDA: CHAT CONDUCTOR-CLIENTE

## 🎯 OBJETIVO

Agregar el botón de chat en la pantalla de detalle de carrera para que el conductor pueda chatear con el cliente.

---

## ⚡ INTEGRACIÓN EN 3 PASOS

### **PASO 1: Import** (1 línea)

Abre `lib/screens/ride_detail_screen.dart` y agrega al inicio:

```dart
import 'customer_chat_screen.dart';
```

---

### **PASO 2: Botón Flotante** (15 líneas)

Busca el `Stack` en el método `build()` y agrega este código **ANTES** del último `]` del Stack:

```dart
// 💬 BOTÓN DE CHAT CONDUCTOR-CLIENTE
if (_fullRideData != null && 
    _fullRideData!['status'] == 'in_progress' &&
    _fullRideData!['customer'] != null)
  Positioned(
    bottom: 20,
    right: 20,
    child: FloatingActionButton(
      onPressed: _openCustomerChat,
      backgroundColor: Colors.blue,
      child: const Icon(Icons.chat),
      heroTag: 'customer_chat',
      tooltip: 'Chat con cliente',
    ),
  ),
```

---

### **PASO 3: Método** (20 líneas)

Agrega este método en la clase `_RideDetailScreenState`:

```dart
void _openCustomerChat() {
  // Validar que hay datos del cliente
  if (_fullRideData == null || _fullRideData!['customer'] == null) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('No se pudo abrir el chat con el cliente'),
        backgroundColor: Colors.red,
      ),
    );
    return;
  }

  // Abrir pantalla de chat
  Navigator.push(
    context,
    MaterialPageRoute(
      builder: (context) => CustomerChatScreen(
        customerId: _fullRideData!['customer']['id'],
        customerName: _fullRideData!['customer']['username'] ?? 
                      _fullRideData!['customer']['first_name'] ?? 
                      'Cliente',
        driverId: widget.driverId,
      ),
    ),
  );
}
```

---

## ✅ ¡LISTO!

Con estos 3 pasos, el chat estará integrado.

---

## 🎨 CÓMO SE VE

```
┌─────────────────────────────────────┐
│  📍 Detalle de Carrera              │
│                                     │
│  🗺️ [Mapa con origen y destinos]   │
│                                     │
│  📋 Información:                    │
│  👤 Cliente: Juan Pérez             │
│  💰 Precio: $5.50                   │
│  📍 Origen: Av. Principal           │
│  🎯 Destino: Centro Comercial       │
│                                     │
│  [Botón: Iniciar Carrera]          │
│                                     │
│                            💬 ←─────┤ Botón de chat
└─────────────────────────────────────┘
```

---

## 🔄 FLUJO COMPLETO

```
1. Conductor acepta carrera
   ↓
2. Carrera pasa a estado 'in_progress'
   ↓
3. Aparece botón flotante de chat 💬
   ↓
4. Conductor presiona botón
   ↓
5. Se abre CustomerChatScreen
   ↓
6. WebSocket se conecta automáticamente
   ↓
7. Conductor puede chatear con cliente
   ↓
8. Cliente recibe mensajes en tiempo real
   ↓
9. Carrera termina → Chat se cierra automáticamente
```

---

## 🎯 CUÁNDO APARECE EL BOTÓN

### **SÍ aparece cuando:**
- ✅ Viaje está en estado `'in_progress'`
- ✅ Hay datos del cliente disponibles
- ✅ El conductor está viendo el detalle de la carrera

### **NO aparece cuando:**
- ❌ Viaje está en `'requested'` (aún no aceptado)
- ❌ Viaje está en `'completed'` (ya terminó)
- ❌ Viaje está en `'cancelled'` (cancelado)
- ❌ No hay datos del cliente

---

## 🔒 SEGURIDAD

El backend **ya valida** que:

✅ Conductor y cliente sean de la misma organización  
✅ Solo el conductor del viaje puede chatear con ese cliente  
✅ El chat se cierra cuando el viaje termina  
✅ No hay fugas de información entre cooperativas  

---

## 📱 FUNCIONALIDADES DEL CHAT

### **Enviar:**
- ✅ Mensajes de texto
- ✅ Imágenes desde galería
- ✅ Emojis

### **Recibir:**
- ✅ Mensajes en tiempo real
- ✅ Imágenes
- ✅ Notificaciones

### **UI:**
- ✅ Scroll automático
- ✅ Indicador de conexión
- ✅ Banner informativo
- ✅ Diseño moderno

---

## 🧪 CÓMO PROBAR

1. **Acepta una carrera** desde la app
2. **Inicia la carrera** (cambia a 'in_progress')
3. **Verifica que aparezca** el botón flotante 💬
4. **Presiona el botón** para abrir el chat
5. **Envía un mensaje** de prueba
6. **Verifica** que el cliente lo reciba (si tienes acceso)

---

## 🐛 TROUBLESHOOTING

### **El botón no aparece:**
```dart
// Verifica en los logs:
print('Status: ${_fullRideData!['status']}');
print('Customer: ${_fullRideData!['customer']}');

// Debe mostrar:
// Status: in_progress
// Customer: {id: 123, username: 'juan', ...}
```

### **Error al abrir chat:**
```dart
// Verifica que customer tenga ID:
print('Customer ID: ${_fullRideData!['customer']['id']}');

// Debe mostrar un número, no null
```

### **WebSocket no conecta:**
```
// Verifica la URL en customer_chat_service.dart:
wss://taxis-deaquipalla.up.railway.app/ws/chat/{driver_id}/

// Debe reemplazar {driver_id} con el ID real del conductor
```

---

## 📝 CÓDIGO COMPLETO DE EJEMPLO

```dart
// lib/screens/ride_detail_screen.dart

import 'package:flutter/material.dart';
import 'customer_chat_screen.dart'; // ← PASO 1

class RideDetailScreen extends StatefulWidget {
  final int rideId;
  final int driverId;
  
  const RideDetailScreen({
    required this.rideId,
    required this.driverId,
  });
  
  @override
  _RideDetailScreenState createState() => _RideDetailScreenState();
}

class _RideDetailScreenState extends State<RideDetailScreen> {
  Map<String, dynamic>? _fullRideData;
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Detalle de Carrera')),
      body: Stack(
        children: [
          // Tu código existente del mapa y detalles...
          
          // ← PASO 2: Botón flotante
          if (_fullRideData != null && 
              _fullRideData!['status'] == 'in_progress' &&
              _fullRideData!['customer'] != null)
            Positioned(
              bottom: 20,
              right: 20,
              child: FloatingActionButton(
                onPressed: _openCustomerChat,
                backgroundColor: Colors.blue,
                child: const Icon(Icons.chat),
                heroTag: 'customer_chat',
                tooltip: 'Chat con cliente',
              ),
            ),
        ],
      ),
    );
  }
  
  // ← PASO 3: Método
  void _openCustomerChat() {
    if (_fullRideData == null || _fullRideData!['customer'] == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No se pudo abrir el chat con el cliente'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => CustomerChatScreen(
          customerId: _fullRideData!['customer']['id'],
          customerName: _fullRideData!['customer']['username'] ?? 
                        _fullRideData!['customer']['first_name'] ?? 
                        'Cliente',
          driverId: widget.driverId,
        ),
      ),
    );
  }
}
```

---

## ⏱️ TIEMPO ESTIMADO

- **Copiar código:** 5 minutos
- **Probar:** 10 minutos
- **Total:** 15 minutos

---

## 🎉 ¡ESO ES TODO!

Con estos 3 pasos simples, tendrás el chat conductor-cliente funcionando en tu app.

**¿Necesitas ayuda?** Revisa los archivos de documentación completa:
- `INTEGRACION_CHAT_CLIENTE.md`
- `RESUMEN_CHAT_CLIENTE.md`
- `EJEMPLO_INTEGRACION_CHAT.dart`
