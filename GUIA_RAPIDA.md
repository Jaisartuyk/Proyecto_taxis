# 🚀 Guía Rápida de Inicio

## ⚡ Inicio Rápido (5 minutos)

### 1️⃣ Instalar Dependencias
```bash
cd proyecto_completo
pip install -r requirements.txt
```

### 2️⃣ Configurar Base de Datos
```bash
python manage.py migrate
```

### 3️⃣ Crear Superusuario
```bash
python manage.py createsuperuser
# Usuario: admin
# Email: admin@deaquipalla.com
# Password: (tu contraseña)
```

### 4️⃣ Ejecutar Servidor
```bash
python manage.py runserver
```

### 5️⃣ Acceder a la Aplicación
```
http://localhost:8000
```

---

## 🎯 Acceso Rápido

### Panel de Administración
```
URL: http://localhost:8000/admin/
Usuario: admin (el que creaste)
```

### Dashboards
- **Cliente**: http://localhost:8000/customer-dashboard/
- **Conductor**: http://localhost:8000/driver-dashboard/
- **Admin**: http://localhost:8000/admin_dashboard/

---

## 👥 Crear Usuarios de Prueba

### Opción 1: Desde el Admin Panel
1. Ve a http://localhost:8000/admin/
2. Click en "App users" → "Add"
3. Completa los datos:
   - Username: conductor1
   - Password: (tu contraseña)
   - Role: driver
   - First name: Juan
   - Last name: Pérez
   - Phone number: +573001234567

### Opción 2: Desde la Aplicación
1. Ve a http://localhost:8000/register/driver/
2. Completa el formulario
3. Inicia sesión

---

## 📱 Configurar WhatsApp (Opcional)

### Desarrollo Local con ngrok

1. **Instalar ngrok**
   ```bash
   # Descarga desde https://ngrok.com/download
   ```

2. **Ejecutar ngrok**
   ```bash
   ngrok http 8000
   ```

3. **Copiar URL HTTPS**
   ```
   Ejemplo: https://abc123.ngrok.io
   ```

4. **Configurar en WASender**
   - Panel de WASender → Webhooks
   - URL: `https://abc123.ngrok.io/webhook/whatsapp/`
   - Eventos: `message.received`

5. **Probar**
   - Envía "MENU" al número de WhatsApp configurado
   - El agente debe responder automáticamente

---

## 🧪 Probar el Sistema

### Test 1: Crear una Carrera (Web)
1. Login como cliente
2. Click en "Solicitar un Taxi"
3. Completa origen y destino
4. Confirma la carrera

### Test 2: Aceptar Carrera (Conductor)
1. Login como conductor
2. Ve al dashboard
3. Click en "Ver Carreras Disponibles"
4. Click en "Aceptar Carrera"

### Test 3: WhatsApp (Si está configurado)
1. Envía "MENU" por WhatsApp
2. Responde "1" para solicitar
3. Envía dirección de origen
4. Envía dirección de destino
5. Confirma con "SÍ"

---

## 🔧 Comandos Útiles

### Migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### Crear Superusuario
```bash
python manage.py createsuperuser
```

### Recolectar Archivos Estáticos
```bash
python manage.py collectstatic
```

### Ejecutar Shell
```bash
python manage.py shell
```

### Ver Logs
```bash
# Los logs aparecen en la consola donde ejecutaste runserver
```

---

## 📊 Datos de Prueba

### Crear Taxi para un Conductor
```python
python manage.py shell

from taxis.models import Taxi, AppUser

# Obtener conductor
conductor = AppUser.objects.get(username='conductor1')

# Crear taxi
taxi = Taxi.objects.create(
    user=conductor,
    plate_number='ABC123',
    vehicle_description='Toyota Corolla 2020 - Blanco',
    latitude=6.2442,
    longitude=-75.5812
)
```

### Crear Carrera de Prueba
```python
from taxis.models import Ride, RideDestination, AppUser

# Obtener cliente y conductor
cliente = AppUser.objects.get(role='customer')
conductor = AppUser.objects.get(role='driver')

# Crear carrera
ride = Ride.objects.create(
    customer=cliente,
    driver=conductor,
    origin='Parque Lleras, Medellín',
    origin_latitude=6.2088,
    origin_longitude=-75.5686,
    status='accepted'
)

# Agregar destino
RideDestination.objects.create(
    ride=ride,
    destination='Aeropuerto José María Córdova',
    destination_latitude=6.1645,
    destination_longitude=-75.4234,
    order=1
)
```

---

## 🐛 Solución de Problemas Comunes

### Error: "No module named 'channels'"
```bash
pip install channels channels_redis
```

### Error: "Connection refused" (Redis)
```bash
# Instalar Redis
# Windows: https://github.com/microsoftarchive/redis/releases
# Linux: sudo apt-get install redis-server
# Mac: brew install redis

# Iniciar Redis
redis-server
```

### Error: "Table doesn't exist"
```bash
python manage.py migrate
```

### Error: "Static files not found"
```bash
python manage.py collectstatic --noinput
```

### WhatsApp no responde
1. Verifica que ngrok esté corriendo
2. Verifica la URL en WASender
3. Revisa los logs del servidor
4. Prueba con curl:
```bash
curl -X POST "http://localhost:8000/webhook/whatsapp/" \
  -H "Content-Type: application/json" \
  -d '{"event": "message.received", "data": {"from": "+573001234567", "text": "MENU", "name": "Test"}}'
```

---

## 📱 Comandos de WhatsApp

| Comando | Acción |
|---------|--------|
| `MENU` o `HOLA` | Mostrar menú principal |
| `1` o `SOLICITAR` | Solicitar una carrera |
| `2` o `MIS CARRERAS` | Ver carreras activas |
| `3` o `CANCELAR` | Cancelar una carrera |
| `4` o `AYUDA` | Mostrar ayuda |
| `ESTADO` | Ver estado de carrera actual |

---

## 🎨 Personalización Rápida

### Cambiar Logo
1. Reemplaza: `taxis/static/imagenes/DE_AQU_PALL_Logo.png`
2. Ejecuta: `python manage.py collectstatic`

### Cambiar Colores del Dashboard
Edita en `customer_dashboard.html` o `driver_dashboard.html`:
```css
:root {
    --primary-color: #TU_COLOR;
    --secondary-color: #TU_COLOR;
}
```

### Cambiar Tarifa Base
Edita en `whatsapp_agent.py`:
```python
def _calcular_tarifa(self, distancia_km):
    tarifa_base = 5000  # Cambiar aquí
    tarifa_por_km = 2500  # Cambiar aquí
    return tarifa_base + (distancia_km * tarifa_por_km)
```

---

## 📚 Documentación Completa

- **README.md** - Información general del proyecto
- **WHATSAPP_SETUP.md** - Configuración detallada de WhatsApp
- **ANALISIS_ESTRUCTURA.md** - Análisis de la estructura
- **MEJORAS_IMPLEMENTADAS.md** - Resumen de mejoras

---

## 🚀 Despliegue Rápido

### Render.com (Gratis)
1. Sube tu código a GitHub
2. Ve a https://render.com
3. New → Web Service
4. Conecta tu repositorio
5. Render detectará automáticamente `render.yaml`
6. Agrega variables de entorno
7. Deploy

### Variables de Entorno Necesarias
```
SECRET_KEY=tu-secret-key-generada
DEBUG=False
ALLOWED_HOSTS=tu-dominio.onrender.com
WASENDER_TOKEN=tu-token-wasender
```

---

## ✅ Checklist de Inicio

- [ ] Dependencias instaladas
- [ ] Base de datos migrada
- [ ] Superusuario creado
- [ ] Servidor corriendo
- [ ] Admin panel accesible
- [ ] Usuario conductor creado
- [ ] Usuario cliente creado
- [ ] Taxi creado para conductor
- [ ] Carrera de prueba creada
- [ ] WhatsApp configurado (opcional)
- [ ] ngrok corriendo (si usas WhatsApp)

---

## 🎯 Próximos Pasos

1. ✅ Completar el checklist de inicio
2. 📱 Configurar WhatsApp con ngrok
3. 🧪 Probar flujo completo de carrera
4. 🎨 Personalizar colores y logo
5. 👥 Crear usuarios reales
6. 🚀 Desplegar en producción
7. 📊 Monitorear y optimizar

---

## 📞 Ayuda

¿Necesitas ayuda?
- 📧 Email: soporte@deaquipalla.com
- 💬 WhatsApp: +57 XXX XXX XXXX
- 🐛 GitHub Issues

---

**¡Listo para comenzar!** 🎉

Ejecuta `python manage.py runserver` y visita http://localhost:8000
