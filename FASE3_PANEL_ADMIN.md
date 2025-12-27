# 🚀 FASE 3: Panel de Administración Multi-Tenant

## 📋 OBJETIVO

Crear un panel de administración completo para que el super admin pueda:
- ✅ Gestionar cooperativas (crear, editar, eliminar)
- ✅ Ver estadísticas globales de todas las cooperativas
- ✅ Gestionar planes y facturación
- ✅ Aprobar/rechazar conductores
- ✅ Ver reportes financieros
- ✅ Configurar branding por cooperativa

---

## 🎯 FUNCIONALIDADES A IMPLEMENTAR

### **1. Dashboard Super Admin**
- Vista general de todas las cooperativas
- Estadísticas globales:
  - Total de cooperativas activas
  - Total de conductores por plan
  - Ingresos mensuales por comisiones
  - Carreras totales del sistema
- Gráficos de crecimiento
- Alertas de cooperativas que exceden límites

### **2. Gestión de Cooperativas**
- **Listar cooperativas:**
  - Tabla con filtros (plan, estado, fecha)
  - Búsqueda por nombre
  - Ordenamiento
  
- **Crear cooperativa:**
  - Formulario con validación
  - Campos: nombre, plan, comisión, límite conductores
  - Asignar admin de cooperativa
  - Configurar branding (logo, colores)
  
- **Editar cooperativa:**
  - Cambiar plan
  - Ajustar comisión
  - Modificar límites
  - Actualizar branding
  
- **Eliminar/Suspender cooperativa:**
  - Soft delete (mantener datos históricos)
  - Desactivar conductores asociados
  - Notificar al admin de la cooperativa

### **3. Gestión de Conductores**
- **Aprobar conductores:**
  - Lista de conductores pendientes
  - Ver documentos subidos
  - Aprobar/rechazar con comentarios
  - Notificación automática al conductor
  
- **Ver todos los conductores:**
  - Filtrar por cooperativa
  - Filtrar por estado (pendiente, aprobado, rechazado)
  - Ver historial de carreras
  - Suspender/reactivar conductor

### **4. Reportes Financieros**
- **Ingresos por comisiones:**
  - Por cooperativa
  - Por mes
  - Gráficos de tendencias
  
- **Facturación:**
  - Generar facturas mensuales
  - Historial de pagos
  - Exportar a PDF/Excel

### **5. Configuración de Planes**
- **Gestionar planes:**
  - Crear/editar planes
  - Definir precios y comisiones
  - Establecer límites
  - Activar/desactivar planes

### **6. Branding por Cooperativa**
- **Configurar:**
  - Logo de la cooperativa
  - Colores primarios/secundarios
  - Nombre personalizado
  - Mensaje de bienvenida
  - Información de contacto

---

## 🗂️ ESTRUCTURA DE ARCHIVOS

```
taxis/
├── admin_views.py (NUEVO)
│   ├── SuperAdminDashboardView
│   ├── OrganizationListView
│   ├── OrganizationCreateView
│   ├── OrganizationUpdateView
│   ├── OrganizationDeleteView
│   ├── DriverApprovalView
│   ├── FinancialReportsView
│   └── PlanManagementView
│
├── forms.py (NUEVO)
│   ├── OrganizationForm
│   ├── DriverApprovalForm
│   └── PlanForm
│
├── decorators.py (NUEVO)
│   └── superadmin_required
│
templates/admin/
├── dashboard.html (NUEVO)
├── organizations/
│   ├── list.html
│   ├── create.html
│   ├── edit.html
│   └── detail.html
├── drivers/
│   ├── approval_list.html
│   └── detail.html
├── reports/
│   ├── financial.html
│   └── statistics.html
└── plans/
    ├── list.html
    └── edit.html

static/admin/
├── css/
│   └── admin-dashboard.css (NUEVO)
└── js/
    └── admin-dashboard.js (NUEVO)
```

---

## 📊 MODELOS A EXTENDER

### **Organization (ya existe, agregar campos)**
```python
class Organization(models.Model):
    # Campos existentes...
    
    # NUEVOS CAMPOS FASE 3:
    is_active = models.BooleanField(default=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    suspension_reason = models.TextField(blank=True)
    
    # Branding
    primary_color = models.CharField(max_length=7, default='#007bff')
    secondary_color = models.CharField(max_length=7, default='#6c757d')
    welcome_message = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    
    # Facturación
    billing_email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Estadísticas
    total_rides = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

### **Invoice (NUEVO)**
```python
class Invoice(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Montos
    subscription_fee = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Estado
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pendiente'),
        ('paid', 'Pagada'),
        ('overdue', 'Vencida'),
        ('cancelled', 'Cancelada')
    ])
    
    issued_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Archivo PDF
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
```

---

## 🔐 PERMISOS Y SEGURIDAD

### **Decorador superadmin_required**
```python
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def superadmin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## 🎨 DISEÑO UI/UX

### **Dashboard Principal**
- Cards con métricas clave
- Gráficos interactivos (Chart.js)
- Tabla de cooperativas activas
- Alertas y notificaciones
- Accesos rápidos a funciones comunes

### **Paleta de Colores**
- Primary: #007bff (azul)
- Success: #28a745 (verde)
- Warning: #ffc107 (amarillo)
- Danger: #dc3545 (rojo)
- Dark: #343a40 (gris oscuro)

---

## 📈 ESTADÍSTICAS Y REPORTES

### **Métricas Globales**
```python
def get_global_stats():
    return {
        'total_organizations': Organization.objects.filter(is_active=True).count(),
        'total_drivers': AppUser.objects.filter(role='driver', driver_status='approved').count(),
        'total_rides_today': Ride.objects.filter(created_at__date=today).count(),
        'total_revenue_month': Ride.objects.filter(
            created_at__month=current_month,
            status='completed'
        ).aggregate(Sum('price'))['price__sum'] or 0,
        'total_commission_month': Ride.objects.filter(
            created_at__month=current_month,
            status='completed'
        ).aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
    }
```

### **Estadísticas por Cooperativa**
```python
def get_organization_stats(organization_id):
    org = Organization.objects.get(id=organization_id)
    return {
        'active_drivers': org.appuser_set.filter(
            role='driver',
            driver_status='approved'
        ).count(),
        'pending_drivers': org.appuser_set.filter(
            role='driver',
            driver_status='pending'
        ).count(),
        'total_rides': org.ride_set.count(),
        'completed_rides': org.ride_set.filter(status='completed').count(),
        'total_revenue': org.ride_set.filter(
            status='completed'
        ).aggregate(Sum('price'))['price__sum'] or 0,
        'total_commission': org.ride_set.filter(
            status='completed'
        ).aggregate(Sum('commission_amount'))['commission_amount__sum'] or 0,
    }
```

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### **Paso 1: Modelos y Migraciones** (30 min)
- Extender modelo Organization
- Crear modelo Invoice
- Generar migraciones
- Aplicar migraciones

### **Paso 2: Vistas y Formularios** (1 hora)
- Crear admin_views.py
- Crear forms.py
- Implementar decoradores
- Crear URLs

### **Paso 3: Templates** (1 hora)
- Dashboard principal
- CRUD de cooperativas
- Aprobación de conductores
- Reportes financieros

### **Paso 4: Estilos y JavaScript** (30 min)
- CSS personalizado
- Gráficos con Chart.js
- Interactividad con AJAX

### **Paso 5: Testing** (30 min)
- Probar todas las funcionalidades
- Verificar permisos
- Validar reportes

---

## 📝 URLS

```python
# urls.py
urlpatterns = [
    # Super Admin Dashboard
    path('admin/dashboard/', SuperAdminDashboardView.as_view(), name='admin_dashboard'),
    
    # Gestión de Cooperativas
    path('admin/organizations/', OrganizationListView.as_view(), name='admin_organizations'),
    path('admin/organizations/create/', OrganizationCreateView.as_view(), name='admin_organization_create'),
    path('admin/organizations/<int:pk>/edit/', OrganizationUpdateView.as_view(), name='admin_organization_edit'),
    path('admin/organizations/<int:pk>/delete/', OrganizationDeleteView.as_view(), name='admin_organization_delete'),
    path('admin/organizations/<int:pk>/', OrganizationDetailView.as_view(), name='admin_organization_detail'),
    
    # Gestión de Conductores
    path('admin/drivers/pending/', DriverApprovalListView.as_view(), name='admin_drivers_pending'),
    path('admin/drivers/<int:pk>/approve/', DriverApproveView.as_view(), name='admin_driver_approve'),
    path('admin/drivers/<int:pk>/reject/', DriverRejectView.as_view(), name='admin_driver_reject'),
    
    # Reportes
    path('admin/reports/financial/', FinancialReportsView.as_view(), name='admin_reports_financial'),
    path('admin/reports/statistics/', StatisticsReportsView.as_view(), name='admin_reports_statistics'),
    
    # Planes
    path('admin/plans/', PlanListView.as_view(), name='admin_plans'),
    path('admin/plans/<int:pk>/edit/', PlanUpdateView.as_view(), name='admin_plan_edit'),
]
```

---

## 🎯 RESULTADO ESPERADO

Al finalizar la Fase 3, tendrás:

✅ Panel de administración completo y funcional
✅ Gestión visual de cooperativas
✅ Sistema de aprobación de conductores
✅ Reportes financieros detallados
✅ Configuración de branding por cooperativa
✅ Sistema de facturación automático
✅ Estadísticas en tiempo real
✅ UI moderna y responsive

---

**¿Comenzamos con el Paso 1: Modelos y Migraciones?** 🚀
