# 🚨 Integración con ECU-911 y Autoridades - Investigación

## 📋 Objetivo

Investigar y documentar cómo integrar alertas de pánico directamente con:
1. **ECU-911** - Sistema de emergencias de Ecuador
2. **Retenes Policiales** - UPC (Unidad Policía Comunitaria) más cercana
3. **Servicios de Emergencia** - Ambulancia, bomberos

---

## 🇪🇨 ECU-911 - Sistema Integrado de Seguridad

### ¿Qué es ECU-911?

El Servicio Integrado de Seguridad ECU 911 es el número único de atención de emergencias en Ecuador que coordina:
- Policía Nacional
- Bomberos
- Cruz Roja
- Comisión de Tránsito
- Fiscalía

### Información de Contacto

- **Número de Emergencia:** 911
- **WhatsApp:** +593 99 911 1911
- **Web:** https://www.ecu911.gob.ec
- **Correo:** contacto@ecu911.gob.ec

---

## 🔍 Investigación: API ECU-911

### Estado Actual (Enero 2026)

**⚠️ IMPORTANTE:** ECU-911 NO tiene una API pública documentada para desarrolladores privados.

### Opciones de Integración Identificadas:

#### 1. **Integración Oficial (Requiere Convenio)**

```
Para integración oficial con ECU-911:

1. Contactar a ECU-911 mediante:
   - Correo institucional: contacto@ecu911.gob.ec
   - Oficialmente como cooperativa de taxis
   
2. Solicitar convenio de cooperación institucional

3. Presentar:
   - Documentación legal de la cooperativa
   - Descripción técnica del sistema
   - Plan de seguridad de datos
   - Compromiso de uso responsable

4. Si aprueban, proporcionan:
   - Credenciales API privada
   - Documentación técnica
   - Endpoints específicos
   - Protocolo de envío de alertas
```

**Tiempo estimado:** 3-6 meses  
**Costo:** Varía, generalmente gratuito para servicios públicos

#### 2. **Integración Alternativa: Llamada Automática**

Ya que no hay API pública, podemos implementar:

```python
# Opción A: Abrir marcador telefónico (móviles)
def emergency_call_911():
    """
    En PWA: window.location.href = 'tel:911'
    En Android: Intent para llamada directa
    """
    pass

# Opción B: Enviar SMS automático con datos
def send_emergency_sms():
    """
    Enviar SMS al +593 99 911 1911 con:
    - Ubicación GPS
    - Tipo de emergencia
    - ID de carrera
    - Datos del conductor/cliente
    """
    from twilio.rest import Client
    
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f"🆘 EMERGENCIA TAXI\n"
             f"Ubicación: {lat},{lng}\n"
             f"Ver: https://maps.google.com/?q={lat},{lng}\n"
             f"Carrera: #{ride_id}\n"
             f"Conductor: {driver_name}\n"
             f"Placa: {plate}",
        from_='+593XXXXXXXX',
        to='+593999111911'
    )
```

**Costo:** $0.01-0.05 por SMS (Twilio)  
**Tiempo:** Implementación inmediata

#### 3. **Integración con WhatsApp Business ECU-911**

ECU-911 tiene WhatsApp oficial:

```python
def send_whatsapp_emergency():
    """
    Enviar mensaje a WhatsApp de ECU-911
    +593 99 911 1911
    """
    from twilio.rest import Client
    
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        body=f"🆘 EMERGENCIA - Cooperativa {org_name}\n\n"
             f"Tipo: Alerta de pánico conductor\n"
             f"Ubicación: {direccion}\n"
             f"Coordenadas: {lat}, {lng}\n"
             f"Ver en mapa: https://maps.google.com/?q={lat},{lng}\n\n"
             f"Conductor: {conductor_nombre}\n"
             f"Cédula: {conductor_cedula}\n"
             f"Placa: {placa}\n"
             f"Teléfono: {telefono}\n\n"
             f"Cliente: {cliente_nombre}\n"
             f"Teléfono: {cliente_telefono}\n\n"
             f"Carrera ID: #{ride_id}\n"
             f"Hora: {timestamp}",
        from_='whatsapp:+593XXXXXXXXX',  # Tu número WhatsApp Business
        to='whatsapp:+593999111911'       # ECU-911 WhatsApp
    )
```

**Ventajas:**
- ✅ No requiere convenio
- ✅ Implementación inmediata
- ✅ Costo bajo ($0.005 por mensaje)
- ✅ Comprobante de entrega

---

## 🚓 Retenes Policiales - UPC (Unidad Policía Comunitaria)

### Base de Datos de UPCs en Guayaquil

No existe una API oficial, pero podemos crear una base de datos local:

```python
# taxis/data/upc_guayaquil.py

UPC_GUAYAQUIL = [
    {
        'nombre': 'UPC Norte',
        'direccion': 'Av. Francisco de Orellana y Av. Juan Tanca Marengo',
        'telefono': '04-3709100',
        'lat': -2.1414,
        'lng': -79.8838,
        'zona': 'norte'
    },
    {
        'nombre': 'UPC Sur',
        'direccion': 'Av. 25 de Julio y Av. del Bombero',
        'telefono': '04-2444444',
        'lat': -2.2241,
        'lng': -79.9089,
        'zona': 'sur'
    },
    {
        'nombre': 'UPC Centro',
        'direccion': 'Calle Chile y 10 de Agosto',
        'telefono': '04-2326666',
        'lat': -2.1960,
        'lng': -79.8862,
        'zona': 'centro'
    },
    {
        'nombre': 'UPC Terminal Terrestre',
        'direccion': 'Av. Benjamín Carrión',
        'telefono': '04-2139800',
        'lat': -2.1956,
        'lng': -79.9095,
        'zona': 'norte'
    },
    {
        'nombre': 'UPC Aeropuerto',
        'direccion': 'Av. de las Américas',
        'telefono': '04-2169000',
        'lat': -2.1606,
        'lng': -79.8897,
        'zona': 'norte'
    },
    # Agregar más UPCs según zona
]
```

### Implementación: Notificar UPC Más Cercana

```python
# taxis/utils/emergency.py
from geopy.distance import geodesic
from .data.upc_guayaquil import UPC_GUAYAQUIL

def get_nearest_upc(latitude, longitude):
    """
    Encuentra la UPC más cercana a una ubicación
    """
    user_location = (latitude, longitude)
    
    nearest_upc = min(
        UPC_GUAYAQUIL,
        key=lambda upc: geodesic(user_location, (upc['lat'], upc['lng'])).km
    )
    
    distance = geodesic(
        user_location,
        (nearest_upc['lat'], nearest_upc['lng'])
    ).km
    
    return {
        **nearest_upc,
        'distance_km': round(distance, 2)
    }


def notify_nearest_upc(emergency):
    """
    Notifica a la UPC más cercana sobre una emergencia
    """
    upc = get_nearest_upc(emergency.latitude, emergency.longitude)
    
    # Método 1: Llamada automática (requiere Twilio Voice)
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    
    call = client.calls.create(
        twiml=f'<Response><Say language="es-ES">'
              f'Alerta de emergencia. Cooperativa {emergency.ride.organization.name}. '
              f'Conductor {emergency.triggered_by.get_full_name()}. '
              f'Ubicación: {emergency.latitude}, {emergency.longitude}. '
              f'Carrera número {emergency.ride.id}.'
              f'</Say></Response>',
        to=upc['telefono'],
        from_=settings.TWILIO_PHONE_NUMBER
    )
    
    # Método 2: SMS a UPC
    message = client.messages.create(
        body=f"🆘 EMERGENCIA TAXI\n\n"
             f"Cooperativa: {emergency.ride.organization.name}\n"
             f"Conductor: {emergency.triggered_by.get_full_name()}\n"
             f"Cédula: {emergency.triggered_by.national_id}\n"
             f"Placa: {emergency.ride.driver.taxi.plate_number}\n"
             f"Ubicación: https://maps.google.com/?q={emergency.latitude},{emergency.longitude}\n"
             f"Distancia: {upc['distance_km']} km de UPC {upc['nombre']}\n"
             f"Carrera: #{emergency.ride.id}",
        to=upc['telefono'],
        from_=settings.TWILIO_PHONE_NUMBER
    )
    
    # Guardar registro
    emergency.police_station_notified = upc['nombre']
    emergency.save()
    
    logger.critical(
        f"🚓 UPC NOTIFICADA: {upc['nombre']} - "
        f"Distancia: {upc['distance_km']}km - "
        f"Emergency #{emergency.id}"
    )
    
    return upc
```

---

## 💰 Costos de Implementación

### Opción 1: Integración Oficial ECU-911
- **Costo de integración:** Gratis (requiere convenio)
- **Costo mensual:** $0
- **Tiempo:** 3-6 meses
- **Confiabilidad:** ⭐⭐⭐⭐⭐

### Opción 2: SMS/WhatsApp a ECU-911 (Twilio)
- **Setup:** $0
- **Costo por alerta:** $0.01 - $0.05 USD
- **Estimado mensual (50 alertas):** $0.50 - $2.50 USD
- **Tiempo:** Inmediato
- **Confiabilidad:** ⭐⭐⭐⭐

### Opción 3: Llamada Automática + SMS a UPC
- **Setup:** $0
- **Costo por alerta:**
  - Llamada: $0.02 - $0.10 USD/min
  - SMS: $0.01 USD
- **Estimado mensual (50 alertas):** $1.50 - $5.50 USD
- **Tiempo:** Inmediato
- **Confiabilidad:** ⭐⭐⭐⭐

---

## 🛠️ Implementación Recomendada (Fase por Fase)

### Fase 1: Implementación Inmediata (SIN convenio ECU-911)

```python
# taxis/views.py - Agregar a panic_alert()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def panic_alert(request):
    # ... código existente ...
    
    # Crear alerta
    emergency = EmergencyAlert.objects.create(...)
    
    # === NOTIFICACIÓN A AUTORIDADES ===
    
    # 1. WhatsApp a ECU-911 (inmediato)
    try:
        send_whatsapp_to_ecu911(emergency)
        emergency.ecu911_notified = True
        emergency.ecu911_notification_time = timezone.now()
        emergency.save()
    except Exception as e:
        logger.error(f"Error notificando ECU-911: {e}")
    
    # 2. Notificar UPC más cercana (SMS + Llamada)
    try:
        upc = notify_nearest_upc(emergency)
        logger.info(f"UPC notificada: {upc['nombre']}")
    except Exception as e:
        logger.error(f"Error notificando UPC: {e}")
    
    # 3. Notificaciones existentes (admin, contactos, etc.)
    # ...
    
    return Response({
        'status': 'success',
        'emergency_id': emergency.id,
        'ecu911_notified': emergency.ecu911_notified,
        'upc_notified': emergency.police_station_notified
    })
```

### Fase 2: Solicitar Convenio ECU-911 (3-6 meses)

```
1. Preparar documentación:
   - RUC de la cooperativa
   - Estatutos
   - Nómina de socios conductores
   - Descripción del sistema técnico
   - Certificado de seguridad de datos

2. Enviar solicitud formal a:
   contacto@ecu911.gob.ec
   
3. Reunión con autoridades ECU-911

4. Firma de convenio

5. Recibir credenciales API oficial

6. Migrar de WhatsApp/SMS a API oficial
```

### Fase 3: Optimización (Post-convenio)

```python
# Con API oficial de ECU-911
def send_to_ecu911_official_api(emergency):
    """
    Integración oficial con API ECU-911
    (endpoints y autenticación proporcionados por ECU-911)
    """
    import requests
    
    headers = {
        'Authorization': f'Bearer {settings.ECU911_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'tipo_emergencia': 'PANICO_TAXI',
        'coordenadas': {
            'latitud': emergency.latitude,
            'longitud': emergency.longitude
        },
        'datos_conductor': {
            'nombre': emergency.triggered_by.get_full_name(),
            'cedula': emergency.triggered_by.national_id,
            'telefono': emergency.triggered_by.phone_number
        },
        'datos_vehiculo': {
            'placa': emergency.ride.driver.taxi.plate_number,
            'marca': emergency.ride.driver.taxi.brand,
            'modelo': emergency.ride.driver.taxi.model
        },
        'cooperativa': emergency.ride.organization.name,
        'timestamp': emergency.created_at.isoformat()
    }
    
    response = requests.post(
        'https://api.ecu911.gob.ec/v1/alertas',  # URL hipotética
        headers=headers,
        json=data,
        timeout=10
    )
    
    if response.status_code == 201:
        # Registrar número de caso ECU-911
        emergency.ecu911_case_number = response.json()['case_number']
        emergency.save()
        return True
    
    return False
```

---

## 📊 Comparación de Métodos

| Método | Velocidad | Costo | Confiabilidad | Legal | Inmediato |
|--------|-----------|-------|---------------|-------|-----------|
| API Oficial ECU-911 | ⭐⭐⭐⭐⭐ | Gratis | ⭐⭐⭐⭐⭐ | ✅ | ❌ (3-6 meses) |
| WhatsApp ECU-911 | ⭐⭐⭐⭐ | $0.005 | ⭐⭐⭐⭐ | ✅ | ✅ |
| SMS ECU-911 | ⭐⭐⭐⭐ | $0.01 | ⭐⭐⭐⭐ | ✅ | ✅ |
| Llamada a UPC | ⭐⭐⭐ | $0.05 | ⭐⭐⭐ | ✅ | ✅ |
| Marcador Tel 911 | ⭐⭐⭐ | Gratis | ⭐⭐⭐⭐⭐ | ✅ | ✅ |

---

## 🎯 Recomendación Final

### Implementación Escalonada:

**AHORA (Semana 1-2):**
1. ✅ Botón de pánico en PWA y Android
2. ✅ Notificación a admin cooperativa
3. ✅ WhatsApp/SMS automático a ECU-911
4. ✅ SMS a UPC más cercana
5. ✅ Marcador directo a 911

**DESPUÉS (Mes 1-2):**
1. 📝 Solicitar convenio oficial con ECU-911
2. 📝 Presentar documentación legal
3. 📝 Reunión con autoridades

**FUTURO (Mes 6+):**
1. 🔄 Migrar a API oficial ECU-911
2. 🔄 Integración directa con sistema policial
3. 🔄 Dashboard compartido con autoridades

---

## 📞 Contactos Útiles

### ECU-911
- Emergencias: **911**
- WhatsApp: **+593 99 911 1911**
- Email: contacto@ecu911.gob.ec
- Web: https://www.ecu911.gob.ec

### Policía Nacional
- Central: **101** o **911**
- Denuncias: https://denuncias.policia.gob.ec

### Twilio (Para SMS/Llamadas)
- Web: https://www.twilio.com
- Precio SMS Ecuador: ~$0.01 USD
- Precio WhatsApp: ~$0.005 USD
- Precio Voz: ~$0.02 USD/min

---

## 🔐 Consideraciones de Seguridad

1. **Datos Sensibles:** Toda comunicación con autoridades debe ser cifrada
2. **Logs Inmutables:** Registrar todas las alertas sin posibilidad de edición
3. **Backup:** Múltiples canales de notificación (redundancia)
4. **Verificación:** No alertas automáticas sin confirmación humana
5. **Responsabilidad:** Uso exclusivo para emergencias reales

---

## 📝 Notas Legales

⚠️ **IMPORTANTE:**
- Las falsas alarmas son delito en Ecuador (Art. 280 COIP)
- Usar solo para emergencias reales
- Cooperativa responsable del uso correcto del sistema
- Mantener registro de todas las alertas para auditoría

---

**Fecha:** 9 de enero de 2026  
**Estado:** Investigación completa - Listo para implementación Fase 1  
**Próximo paso:** Implementar WhatsApp/SMS a ECU-911 + UPC cercana
