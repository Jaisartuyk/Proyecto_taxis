# 🚕 De Aquí Pa'llá - Sistema de Gestión de Taxis

![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Channels](https://img.shields.io/badge/Channels-4.2.2-orange.svg)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Integrado-25D366.svg)

Sistema completo de gestión de taxis con funcionalidades en tiempo real, integración con WhatsApp y dashboards modernos.

## 🌟 Características Principales

### 🚖 Para Clientes
- ✅ Solicitud de carreras en tiempo real
- ✅ Seguimiento de viajes activos
- ✅ Historial de viajes
- ✅ **Solicitud por WhatsApp con Agente de IA**
- ✅ Dashboard moderno y responsivo
- ✅ Geocodificación automática de direcciones
- ✅ Cálculo de tarifas estimadas

### 🚗 Para Conductores
- ✅ Panel de control con estadísticas
- ✅ Visualización de carreras disponibles
- ✅ Gestión de carreras activas
- ✅ Notificaciones en tiempo real
- ✅ Chat con central
- ✅ Actualización de ubicación GPS
- ✅ Ganancias del día

### 👨‍💼 Para Administradores
- ✅ Gestión de usuarios (clientes y conductores)
- ✅ Monitoreo de carreras
- ✅ Estadísticas generales
- ✅ Comunicación con conductores
- ✅ Gestión de rutas compartidas

### 📱 Integración WhatsApp
- ✅ **Agente de IA conversacional**
- ✅ Solicitud de carreras por chat
- ✅ Consulta de estado
- ✅ Cancelación de carreras
- ✅ Notificaciones automáticas
- ✅ Geocodificación de direcciones

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 5.2
- **WebSockets**: Django Channels 4.2.2
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: HTML5, CSS3, JavaScript
- **Mapas**: Google Maps API
- **Geocodificación**: Geopy
- **WhatsApp**: WASender API
- **Autenticación**: Django Auth + Token Auth
- **API REST**: Django REST Framework 3.16.0

## 📋 Requisitos

- Python 3.8+
- Redis (para Django Channels)
- Cuenta en WASender (para WhatsApp)
- Google Maps API Key (opcional, para mapas)

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Jaisartuyk/Proyecto-Django-Channels.git
cd proyecto_completo
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (opcional)

Crea un archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# WhatsApp (WASender)
WASENDER_API_URL=https://wasenderapi.com/api/send-message
WASENDER_TOKEN=tu-token-aqui

# Google Maps (opcional)
GOOGLE_MAPS_API_KEY=tu-api-key-aqui
```

### 5. Realizar migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Ejecutar el servidor

```bash
# Servidor Django
python manage.py runserver

# En otra terminal, ejecutar Redis (necesario para Channels)
redis-server
```

## 📱 Configuración de WhatsApp

Para habilitar la funcionalidad de WhatsApp, sigue la guía detallada en:

📄 **[WHATSAPP_SETUP.md](WHATSAPP_SETUP.md)**

Resumen rápido:
1. Obtén credenciales de WASender
2. Configura el webhook en WASender apuntando a: `https://tu-dominio.com/webhook/whatsapp/`
3. Prueba enviando "MENU" al número configurado

## 🎯 Uso del Sistema

### Roles de Usuario

El sistema maneja 3 tipos de roles:

1. **Cliente** (`customer`)
   - Puede solicitar carreras
   - Ver historial de viajes
   - Editar perfil

2. **Conductor** (`driver`)
   - Ver carreras disponibles
   - Aceptar y gestionar carreras
   - Actualizar ubicación GPS

3. **Administrador** (`admin`)
   - Gestión completa del sistema
   - Monitoreo de carreras
   - Gestión de usuarios

### Comandos de WhatsApp

| Comando | Descripción |
|---------|-------------|
| `MENU` | Mostrar menú principal |
| `SOLICITAR` | Iniciar solicitud de carrera |
| `MIS CARRERAS` | Ver carreras activas |
| `ESTADO` | Consultar estado de carrera |
| `CANCELAR` | Cancelar una carrera |
| `AYUDA` | Ver ayuda |

## 🗂️ Estructura del Proyecto

```
proyecto_completo/
├── taxi_project/          # Configuración Django
├── taxis/                 # App principal
│   ├── models.py         # Modelos de datos
│   ├── views.py          # Vistas
│   ├── api_views.py      # API REST
│   ├── consumers.py      # WebSocket consumers
│   ├── whatsapp_agent.py # 🆕 Agente de IA WhatsApp
│   ├── whatsapp_webhook.py # 🆕 Webhook handler
│   └── templates/        # Templates HTML
├── static/               # Archivos estáticos
├── media/                # Archivos subidos
└── requirements.txt      # Dependencias
```

## 🔌 API Endpoints

### Autenticación
- `POST /api/login/` - Login de conductores

### Carreras
- `GET /request-ride/` - Solicitar carrera
- `GET /available-rides/` - Ver carreras disponibles
- `POST /update-ride-status/<id>/` - Actualizar estado
- `GET /ride/<id>/` - Detalles de carrera

### WhatsApp
- `POST /webhook/whatsapp/` - Webhook de mensajes
- `POST /webhook/whatsapp/status/` - Webhook de estados
- `POST /api/whatsapp/send-notification/` - Enviar notificación

### WebSocket
- `ws://localhost:8000/ws/chat/<room>/` - Chat en tiempo real

## 🎨 Capturas de Pantalla

### Dashboard del Cliente
- Diseño moderno con gradientes
- Estadísticas visuales
- Información de WhatsApp integrada

### Dashboard del Conductor
- Panel de control profesional
- Carreras disponibles y activas
- Indicador de estado en línea

## 🧪 Testing

```bash
# Ejecutar tests
python manage.py test

# Probar webhook localmente
curl -X POST "http://localhost:8000/webhook/whatsapp/" \
  -H "Content-Type: application/json" \
  -d '{"event": "message.received", "data": {"from": "+573001234567", "text": "MENU"}}'
```

## 🚀 Despliegue

### Render.com (Recomendado)

El proyecto incluye `render.yaml` para despliegue automático:

1. Conecta tu repositorio en Render
2. Render detectará automáticamente la configuración
3. Configura las variables de entorno
4. Despliega

### Heroku

```bash
# Login
heroku login

# Crear app
heroku create nombre-app

# Configurar variables
heroku config:set SECRET_KEY=tu-secret-key
heroku config:set WASENDER_TOKEN=tu-token

# Deploy
git push heroku main

# Migrar
heroku run python manage.py migrate
```

## 📊 Análisis del Proyecto

Para ver un análisis detallado de la estructura:

📄 **[ANALISIS_ESTRUCTURA.md](ANALISIS_ESTRUCTURA.md)**

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📝 Changelog

### v2.0.0 (2025-10-08)
- 🆕 Integración completa con WhatsApp
- 🆕 Agente de IA conversacional
- 🆕 Dashboards modernos y responsivos
- 🆕 Mejoras en la interfaz de usuario
- 🆕 Documentación completa

### v1.0.0
- ✅ Sistema base de gestión de taxis
- ✅ WebSockets para tiempo real
- ✅ API REST
- ✅ Integración con Telegram

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👥 Autores

- **Jaisartuyk** - Desarrollo inicial

## 📞 Soporte

Para soporte o preguntas:
- 📧 Email: soporte@deaquipalla.com
- 💬 WhatsApp: +57 XXX XXX XXXX
- 🐛 Issues: [GitHub Issues](https://github.com/Jaisartuyk/Proyecto-Django-Channels/issues)

## 🙏 Agradecimientos

- Django Community
- WASender API
- Todos los contribuidores

---

**¡Hecho con ❤️ en Colombia!** 🇨🇴