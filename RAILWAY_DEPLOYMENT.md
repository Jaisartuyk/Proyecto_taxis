# 🚀 Despliegue en Railway con PostgreSQL y Redis

## 📋 Configuración Inicial

### 1. **Servicios en Railway**

Railway proporciona automáticamente:
- ✅ **PostgreSQL** - Base de datos principal
- ✅ **Redis** - Para WebSockets y caché
- ✅ **Variables de entorno** - Configuración automática

### 2. **Variables de Entorno Requeridas**

Configura estas variables en el panel de Railway:

```bash
# Django
SECRET_KEY=tu-secret-key-super-seguro-aqui
RAILWAY_ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=taxi_project.settings_railway

# Base de datos (Railway lo proporciona automáticamente)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Redis (Railway lo proporciona automáticamente)
REDIS_URL=redis://default:password@host:port

# WhatsApp
WASENDER_API_URL=https://wasenderapi.com/api/send-message
WASENDER_TOKEN=tu-token-wasender-aqui

# Google Maps
GOOGLE_API_KEY=tu-google-maps-api-key-aqui

# Telegram
TELEGRAM_BOT_TOKEN=tu-telegram-bot-token-aqui
TELEGRAM_CHAT_ID_GRUPO_TAXISTAS=-tu-chat-id-grupo-aqui

# Claude AI (Opcional)
CLAUDE_API_KEY=tu-claude-api-key-aqui
```

## 🚀 Pasos de Despliegue

### 1. **Conectar Repositorio**

1. Ve a [Railway](https://railway.app)
2. Conecta tu repositorio de GitHub
3. Railway detectará automáticamente que es un proyecto Django

### 2. **Configurar Servicios**

1. **PostgreSQL**: Railway lo crea automáticamente
2. **Redis**: Railway lo crea automáticamente
3. **Web Service**: Configurado automáticamente

### 3. **Configurar Variables de Entorno**

En el panel de Railway, ve a Variables y agrega:

```bash
SECRET_KEY=tu-secret-key-aqui
RAILWAY_ENVIRONMENT=production
DJANGO_SETTINGS_MODULE=taxi_project.settings_railway
WASENDER_TOKEN=tu-token-wasender
GOOGLE_API_KEY=tu-google-maps-key
TELEGRAM_BOT_TOKEN=tu-telegram-token
TELEGRAM_CHAT_ID_GRUPO_TAXISTAS=-tu-chat-id
```

### 4. **Configurar Build Command**

Railway usará automáticamente:
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

### 5. **Configurar Start Command**

Railway usará automáticamente:
```bash
daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
```

## 🔧 Configuración Automática

### **settings_railway.py**

El archivo `settings_railway.py` se activa automáticamente cuando:
- `RAILWAY_ENVIRONMENT=production`
- `DJANGO_SETTINGS_MODULE=taxi_project.settings_railway`

### **Características Automáticas**

✅ **PostgreSQL**: Configuración automática de base de datos
✅ **Redis**: Configuración automática para WebSockets
✅ **SSL**: Configuración automática de HTTPS
✅ **Static Files**: Servido por WhiteNoise
✅ **CORS**: Configurado para Railway
✅ **Logging**: Configurado para Railway

## 📊 Verificación del Despliegue

### 1. **Verificar Base de Datos**

```bash
# En Railway Console
python manage.py dbshell
```

### 2. **Verificar Redis**

```bash
# En Railway Console
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

### 3. **Verificar WebSockets**

Visita tu aplicación y verifica que:
- Los dashboards cargan correctamente
- Las notificaciones en tiempo real funcionan
- El chat funciona

## 🔍 Solución de Problemas

### **Error de Base de Datos**

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

### **Error de Redis**

Verifica que `REDIS_URL` esté configurado correctamente en Railway.

### **Error de Static Files**

```bash
# Recopilar archivos estáticos
python manage.py collectstatic --noinput
```

### **Error de WebSockets**

Verifica que:
1. Redis esté funcionando
2. `CHANNEL_LAYERS` esté configurado correctamente
3. `ASGI_APPLICATION` esté configurado

## 📱 Configuración de WhatsApp

### 1. **Configurar Webhook en WASender**

URL del webhook:
```
https://tu-dominio-railway.up.railway.app/webhook/whatsapp/
```

### 2. **Probar Webhook**

```bash
curl -X GET https://tu-dominio-railway.up.railway.app/webhook/whatsapp/
```

Debería responder:
```json
{
  "status": "ok",
  "message": "WhatsApp Webhook is active",
  "service": "De Aquí Pa'llá - Taxi Service"
}
```

## 🎯 URLs Importantes

### **Aplicación Principal**
- `https://tu-dominio.up.railway.app/` - Página principal
- `https://tu-dominio.up.railway.app/admin/` - Panel de administración

### **APIs**
- `https://tu-dominio.up.railway.app/webhook/whatsapp/` - Webhook WhatsApp
- `https://tu-dominio.up.railway.app/api/check_new_rides/` - API de carreras

### **Dashboards**
- `https://tu-dominio.up.railway.app/customer-dashboard/` - Dashboard cliente
- `https://tu-dominio.up.railway.app/driver-dashboard/` - Dashboard conductor
- `https://tu-dominio.up.railway.app/admin_dashboard/` - Dashboard admin

## 📈 Monitoreo

### **Logs en Railway**

1. Ve a tu proyecto en Railway
2. Click en "Deployments"
3. Click en el deployment más reciente
4. Ve a la pestaña "Logs"

### **Métricas**

Railway proporciona métricas automáticas de:
- CPU y memoria
- Requests por minuto
- Tiempo de respuesta
- Errores

## 🔄 Actualizaciones

### **Despliegue Automático**

Railway despliega automáticamente cuando:
- Haces push a la rama principal
- Cambias variables de entorno
- Modificas la configuración

### **Despliegue Manual**

```bash
# Hacer push para desplegar
git add .
git commit -m "Actualización"
git push origin main
```

## 🎉 ¡Listo!

Tu aplicación estará disponible en:
`https://tu-dominio.up.railway.app`

### **Próximos Pasos**

1. ✅ Configurar variables de entorno
2. ✅ Configurar webhook de WhatsApp
3. ✅ Probar todas las funcionalidades
4. ✅ Crear superusuario
5. ✅ Configurar conductores y clientes

---

**¡Disfruta tu sistema de taxis en Railway!** 🚕✨
