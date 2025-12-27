# 🔍 Análisis Pre-Implementación Multi-Tenant

## 📋 OBJETIVO
Revisar todo el sistema actual para asegurar que la implementación del modelo `Organization` no rompa código existente y que toda la lógica se complemente correctamente.

---

## 🗂️ COMPONENTES A REVISAR

### 1. **MODELOS (models.py)** ✅
### 2. **VISTAS (views.py)** ⚠️
### 3. **APIs (serializers.py, viewsets)** ⚠️
### 4. **WEBSOCKETS (consumers.py)** ⚠️
### 5. **TEMPLATES (HTML)** ✅
### 6. **JAVASCRIPT (comunicacion-completa.js)** ✅
### 7. **APP FLUTTER** ⚠️
### 8. **MIGRACIONES Y DATOS EXISTENTES** ⚠️

---

## 📊 ANÁLISIS DETALLADO

## 1. ✅ MODELOS (models.py)

### **Estado Actual:**
- `AppUser`: Usuario con roles (customer, driver, admin)
- `Taxi`: Vehículo asociado a conductor
- `Ride`: Carrera con customer y driver
- `RideDestination`: Destinos de la carrera
- `ChatMessage`: Mensajes entre usuarios
- `FCMToken`: Tokens de notificaciones push
- `WhatsAppConversation`: Conversaciones de WhatsApp

### **Cambios Necesarios:**

#### **A. Agregar modelo Organization:**
```python
class Organization(models.Model):
    """Cooperativa o grupo de taxis"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo = CloudinaryField('image', folder='org_logos', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#FFD700')
    secondary_color = models.CharField(max_length=7, default='#000000')
    
    # Contacto
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    city = models.CharField(max_length=100)
    
    # Suscripción
    plan = models.CharField(max_length=20, default='basic')
    status = models.CharField(max_length=20, default='trial')
    max_drivers = models.IntegerField(default=10)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=29.00)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Admin de la cooperativa
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

#### **B. Modificar AppUser:**
```python
class AppUser(AbstractUser):
    # ... campos existentes ...
    
    # ✅ NUEVO
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # ⚠️ IMPORTANTE: null=True para migración
        blank=True,
        help_text="Cooperativa a la que pertenece"
    )
    
    # ✅ NUEVO: Número de unidad
    driver_number = models.CharField(
        max_length=10,
        unique=True,
        null=True,
        blank=True
    )
    
    # ✅ NUEVO: Estado de aprobación
    driver_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('approved', 'Aprobado'),
            ('suspended', 'Suspendido'),
            ('rejected', 'Rechazado'),
        ],
        default='pending'
    )
```

#### **C. Modificar Ride:**
```python
class Ride(models.Model):
    # ... campos existentes ...
    
    # ✅ NUEVO
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='rides',
        null=True,  # ⚠️ IMPORTANTE: null=True para migración
        blank=True
    )
    
    # ✅ NUEVO: Comisión
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
```

#### **D. Modificar Taxi:**
```python
class Taxi(models.Model):
    # ... campos existentes ...
    
    # ✅ NUEVO (opcional, se puede inferir del user.organization)
    # organization = models.ForeignKey('Organization', ...)
```

### **⚠️ IMPACTO:**
- **BAJO**: Los campos nuevos son `null=True`, no rompe datos existentes
- **MIGRACIÓN**: Necesaria pero segura
- **RETROCOMPATIBILIDAD**: ✅ Mantenida

---

## 2. ⚠️ VISTAS (views.py)

### **Queries que necesitan filtro por Organization:**

#### **A. Dashboard de Conductor (líneas 224-280):**
```python
# ❌ ACTUAL (sin filtro)
total_rides = Ride.objects.filter(driver=request.user).count()

# ✅ DEBE SER (con filtro)
total_rides = Ride.objects.filter(
    driver=request.user,
    organization=request.user.organization  # ✅ AGREGAR
).count()
```

**Afectados:**
- `total_rides`
- `completed_rides`
- `canceled_rides`
- `active_rides_count`
- `today_earnings`
- `month_earnings`
- `total_earnings`
- `today_rides_count`
- `available_rides_list` ⚠️ **MUY IMPORTANTE**
- `active_rides_list`
- `recent_completed`

#### **B. Dashboard de Cliente (líneas 312-320):**
```python
# ❌ ACTUAL
total_rides = Ride.objects.filter(customer=request.user).count()

# ✅ DEBE SER
# Cliente puede usar cualquier cooperativa, NO filtrar por organization
total_rides = Ride.objects.filter(customer=request.user).count()
```

**Nota:** Los clientes NO se filtran por organización, pueden usar cualquier cooperativa.

#### **C. Dashboard de Admin (líneas 336-371):**
```python
# ❌ ACTUAL (ve TODO el sistema)
total_users = AppUser.objects.count()

# ✅ DEBE SER (ve solo su cooperativa)
if request.user.is_superuser:
    # Super admin ve todo
    total_users = AppUser.objects.count()
else:
    # Admin de cooperativa ve solo su org
    total_users = AppUser.objects.filter(
        organization=request.user.organization
    ).count()
```

**Afectados:**
- `total_users`
- `total_drivers`
- `total_customers` (NO filtrar, clientes son globales)
- `total_rides`
- `requested_rides`
- `accepted_rides`
- `in_progress_rides`
- `completed_rides`
- `canceled_rides`
- `total_revenue`
- `today_rides`
- `today_revenue`
- `active_drivers`
- `recent_rides`

#### **D. Carreras Disponibles (línea 1146):**
```python
# ❌ ACTUAL (muestra TODAS las carreras)
rides = Ride.objects.filter(status='requested').order_by('created_at')

# ✅ DEBE SER (solo de su cooperativa)
rides = Ride.objects.filter(
    status='requested',
    organization=request.user.organization  # ✅ CRÍTICO
).order_by('created_at')
```

**⚠️ CRÍTICO:** Si no se filtra, conductores verán carreras de otras cooperativas.

#### **E. Aceptar Carrera (línea 1359-1360):**
```python
# ✅ AGREGAR VALIDACIÓN
driver = AppUser.objects.get(id=driver_id, role='driver')
ride = Ride.objects.get(id=ride_id)

# Validar que el conductor pertenezca a la misma organización
if ride.organization != driver.organization:
    return JsonResponse({'error': 'No puedes aceptar carreras de otra cooperativa'}, status=403)
```

#### **F. Crear Carrera (líneas 807, 900, 1034):**
```python
# ✅ AGREGAR organization al crear
ride = Ride.objects.create(
    customer=request.user,
    origin=origin,
    # ... otros campos ...
    organization=selected_organization  # ✅ AGREGAR
)
```

### **⚠️ IMPACTO:**
- **ALTO**: Muchas vistas necesitan modificación
- **CRÍTICO**: Carreras disponibles DEBE filtrarse
- **SEGURIDAD**: Validar organización en aceptación de carreras

---

## 3. ⚠️ APIs (serializers.py, viewsets)

### **Archivos a revisar:**
- `serializers.py`
- `viewsets.py` o vistas API en `views.py`

### **Cambios Necesarios:**

#### **A. Serializers:**
```python
# serializers.py
class RideSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    
    class Meta:
        model = Ride
        fields = ['id', 'origin', 'status', 'organization', 'organization_name', ...]
```

#### **B. ViewSets/APIs:**
```python
# API de carreras disponibles
@api_view(['GET'])
def available_rides_api(request):
    organization_id = request.GET.get('organization_id')
    
    if not organization_id:
        return Response({'error': 'organization_id required'}, status=400)
    
    rides = Ride.objects.filter(
        status='requested',
        organization_id=organization_id
    )
    
    serializer = RideSerializer(rides, many=True)
    return Response(serializer.data)
```

### **⚠️ IMPACTO:**
- **MEDIO**: APIs necesitan parámetro `organization_id`
- **APP FLUTTER**: Debe enviar `organization_id` en requests

---

## 4. ⚠️ WEBSOCKETS (consumers.py)

### **Cambios Necesarios:**

#### **A. ChatConsumer:**
```python
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.organization_id = self.user.organization_id
        
        # ✅ Grupo por organización
        self.room_group_name = f'chat_org_{self.organization_id}'
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
```

#### **B. AudioConsumer:**
```python
class AudioConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.organization_id = self.user.organization_id
        
        # ✅ Canal de audio por organización
        self.audio_group_name = f'audio_org_{self.organization_id}'
        
        await self.channel_layer.group_add(
            self.audio_group_name,
            self.channel_name
        )
        await self.accept()
```

### **⚠️ IMPACTO:**
- **ALTO**: WebSockets deben agruparse por organización
- **CRÍTICO**: Sin esto, conductores escucharían audio de otras cooperativas

---

## 5. ✅ TEMPLATES (HTML)

### **Cambios Mínimos:**
- Mostrar nombre de organización en header
- Logo de organización en navbar
- Filtros ya se aplican en el backend

```html
<!-- central_comunicacion.html -->
<div class="org-info">
    <img src="{{ request.user.organization.logo.url }}" alt="Logo">
    <span>{{ request.user.organization.name }}</span>
</div>
```

### **⚠️ IMPACTO:**
- **BAJO**: Solo cambios visuales

---

## 6. ✅ JAVASCRIPT (comunicacion-completa.js)

### **Cambios Mínimos:**
- Ya usa datos del backend
- No necesita cambios lógicos

### **⚠️ IMPACTO:**
- **NINGUNO**: JavaScript consume datos ya filtrados

---

## 7. ⚠️ APP FLUTTER

### **Cambios Necesarios:**

#### **A. Agregar organization_id en requests:**
```dart
// Antes
final response = await http.get(
  Uri.parse('$baseUrl/api/rides/?status=requested')
);

// Después
final prefs = await SharedPreferences.getInstance();
final orgId = prefs.getInt('organization_id');

final response = await http.get(
  Uri.parse('$baseUrl/api/rides/?status=requested&organization_id=$orgId')
);
```

#### **B. Guardar organización en login:**
```dart
// Después del login exitoso
final prefs = await SharedPreferences.getInstance();
await prefs.setInt('organization_id', userData['organization_id']);
await prefs.setString('organization_name', userData['organization_name']);
```

#### **C. WebSocket con organización:**
```dart
// Conectar a canal de audio de la organización
final orgId = prefs.getInt('organization_id');
final wsUrl = 'wss://taxis-deaquipalla.up.railway.app/ws/audio/org/$orgId/';
```

### **⚠️ IMPACTO:**
- **MEDIO**: Requiere actualización de la app
- **CRÍTICO**: Sin esto, la app no funcionará correctamente

---

## 8. ⚠️ MIGRACIONES Y DATOS EXISTENTES

### **Plan de Migración:**

#### **Paso 1: Crear Organization por defecto**
```python
# Script de migración
from taxis.models import Organization, AppUser, Ride

# Crear organización por defecto
default_org = Organization.objects.create(
    name="De Aquí Pa'llá",
    slug="de-aqui-pa-lla",
    phone="0999999999",
    email="admin@deaquipalla.com",
    city="Guayaquil",
    plan="premium",
    status="active",
    max_drivers=1000,
    owner=AppUser.objects.filter(is_superuser=True).first()
)

# Asignar todos los usuarios existentes
AppUser.objects.all().update(organization=default_org)

# Asignar todas las carreras existentes
Ride.objects.all().update(organization=default_org)

print(f"✅ Migración completada: {AppUser.objects.count()} usuarios y {Ride.objects.count()} carreras asignados")
```

#### **Paso 2: Hacer campo obligatorio**
```python
# Después de la migración de datos, cambiar a null=False
class AppUser(AbstractUser):
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        null=False,  # ✅ Ahora obligatorio
        blank=False
    )
```

### **⚠️ IMPACTO:**
- **ALTO**: Requiere script de migración
- **SEGURO**: Datos existentes se preservan

---

## 📋 RESUMEN DE IMPACTOS

| Componente | Impacto | Prioridad | Complejidad |
|------------|---------|-----------|-------------|
| **Modelos** | Bajo | Alta | Baja |
| **Vistas** | Alto | Crítica | Media |
| **APIs** | Medio | Alta | Baja |
| **WebSockets** | Alto | Crítica | Media |
| **Templates** | Bajo | Baja | Baja |
| **JavaScript** | Ninguno | Baja | Ninguna |
| **App Flutter** | Medio | Alta | Media |
| **Migración** | Alto | Crítica | Media |

---

## ✅ PLAN DE IMPLEMENTACIÓN SEGURO

### **Fase 1: Preparación (Semana 1)**
1. ✅ Crear modelo `Organization`
2. ✅ Agregar campos a `AppUser` y `Ride` (con `null=True`)
3. ✅ Crear migración
4. ✅ Ejecutar migración
5. ✅ Script de migración de datos (asignar org por defecto)

### **Fase 2: Backend (Semana 2)**
1. ✅ Modificar vistas para filtrar por organización
2. ✅ Agregar validaciones de organización
3. ✅ Modificar WebSockets para agrupar por organización
4. ✅ Actualizar APIs con filtro de organización
5. ✅ Testing exhaustivo

### **Fase 3: Frontend (Semana 3)**
1. ✅ Actualizar templates con info de organización
2. ✅ Modificar app Flutter para enviar organization_id
3. ✅ Agregar pantalla de selección de cooperativa
4. ✅ Testing en app

### **Fase 4: Validación (Semana 4)**
1. ✅ Testing end-to-end
2. ✅ Verificar que no haya fugas de datos entre organizaciones
3. ✅ Performance testing
4. ✅ Documentación

---

## 🚨 PUNTOS CRÍTICOS A NO OLVIDAR

### **1. Seguridad:**
- ✅ SIEMPRE filtrar por organización en queries
- ✅ Validar organización al aceptar carreras
- ✅ WebSockets agrupados por organización
- ✅ No permitir acceso a datos de otras organizaciones

### **2. Performance:**
- ✅ Índices en campo `organization` (automático con ForeignKey)
- ✅ `select_related('organization')` en queries
- ✅ Caché de datos de organización

### **3. Datos:**
- ✅ Migración de datos existentes a organización por defecto
- ✅ Backup antes de migración
- ✅ Verificar integridad después de migración

### **4. App Flutter:**
- ✅ Guardar organization_id en SharedPreferences
- ✅ Enviar organization_id en TODAS las requests
- ✅ Actualizar WebSocket URLs con organización

---

## 🎯 RECOMENDACIÓN FINAL

**✅ EL SISTEMA ESTÁ LISTO PARA MULTI-TENANT**

**Razones:**
1. ✅ Arquitectura bien diseñada (fácil agregar ForeignKey)
2. ✅ Migración segura (null=True → migrar datos → null=False)
3. ✅ Impacto controlado (cambios localizados)
4. ✅ No rompe funcionalidad existente

**Orden de Implementación:**
1. **Primero:** Modelos + Migración de datos
2. **Segundo:** Vistas + APIs (backend)
3. **Tercero:** WebSockets
4. **Cuarto:** App Flutter
5. **Quinto:** Testing completo

**Tiempo Estimado:** 4 semanas
**Riesgo:** Bajo (con testing adecuado)

---

## 📞 PRÓXIMOS PASOS

¿Empezamos con la Fase 1 (Modelos + Migración)?

Puedo:
1. ✅ Crear el modelo `Organization` completo
2. ✅ Modificar `AppUser` y `Ride`
3. ✅ Generar las migraciones
4. ✅ Crear script de migración de datos
5. ✅ Ejecutar y verificar

**Todo sin romper nada existente.** 🚀
