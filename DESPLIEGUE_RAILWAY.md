# 🚀 Guía de Despliegue en Railway - PWA Completa

## 📋 Cambios Realizados

### 1. Configuración de Archivos Estáticos
✅ Actualizado `settings.py` para apuntar a `taxis/static/`
✅ Configurado `STATIC_ROOT` para producción
✅ WhiteNoise configurado para servir archivos estáticos

### 2. Archivos de Configuración Creados
- ✅ `railway.toml` - Configuración de build y deploy
- ✅ `railway_deploy.sh` - Script de despliegue
- ✅ Procfile ya existente (correcto)

## 🔧 Pasos para Desplegar

### Opción 1: Despliegue Automático (Recomendado)

```bash
# 1. Agregar todos los cambios
git add .

# 2. Hacer commit
git commit -m "Implementar PWA completa con archivos estáticos corregidos"

# 3. Push a Railway (se desplegará automáticamente)
git push origin main
```

Railway ejecutará automáticamente:
1. `pip install -r requirements.txt`
2. `python manage.py collectstatic --noinput`
3. `python manage.py migrate --noinput`
4. Iniciará el servidor con Daphne

### Opción 2: Despliegue Manual desde Railway CLI

```bash
# 1. Instalar Railway CLI (si no lo tienes)
npm i -g @railway/cli

# 2. Login
railway login

# 3. Link al proyecto
railway link

# 4. Deploy
railway up
```

## ✅ Verificación Post-Despliegue

### 1. Verificar Archivos Estáticos
Abre tu navegador y verifica que estos archivos carguen correctamente:

- ✅ `https://tu-app.up.railway.app/static/js/service-worker.js`
- ✅ `https://tu-app.up.railway.app/static/js/notifications.js`
- ✅ `https://tu-app.up.railway.app/static/js/comunicacion.js`
- ✅ `https://tu-app.up.railway.app/static/manifest.json`
- ✅ `https://tu-app.up.railway.app/static/css/theme.css`

### 2. Verificar Service Worker
1. Abre DevTools (F12)
2. Ve a Application → Service Workers
3. Deberías ver el service worker registrado

### 3. Verificar PWA
1. Busca el ícono de instalación en la barra de direcciones
2. Intenta instalar la aplicación
3. Verifica que funcione offline

### 4. Verificar Notificaciones
1. Acepta los permisos cuando se soliciten
2. Prueba enviar una notificación desde la consola:
```javascript
notificationManager.showNotification('Test', {body: 'Prueba'});
```

## 🐛 Solución de Problemas

### Problema: Archivos estáticos no cargan (404)

**Solución 1: Ejecutar collectstatic manualmente**
```bash
# Desde Railway CLI
railway run python manage.py collectstatic --noinput
```

**Solución 2: Verificar configuración**
```python
# En settings.py debe estar:
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'taxis', 'static'),
]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

**Solución 3: Verificar que los archivos existan**
```bash
# Verificar estructura local
ls -la taxis/static/js/
ls -la taxis/static/css/
```

### Problema: Service Worker no se registra

**Solución:**
1. Verifica que HTTPS esté activo (Railway lo provee automáticamente)
2. Limpia el caché del navegador
3. Verifica la consola del navegador para errores
4. Asegúrate de que `service-worker.js` cargue correctamente

### Problema: Manifest.json no se encuentra

**Solución:**
1. Verifica que el archivo exista en `taxis/static/manifest.json`
2. Ejecuta `collectstatic` nuevamente
3. Verifica que la ruta en `base.html` sea correcta:
```html
<link rel="manifest" href="{% static 'manifest.json' %}">
```

## 📊 Logs de Railway

Para ver los logs en tiempo real:

```bash
# Opción 1: Desde Railway CLI
railway logs

# Opción 2: Desde el Dashboard de Railway
# Ve a tu proyecto → Deployments → Ver logs
```

Busca estas líneas para confirmar que todo está bien:
```
✅ Collecting static files...
✅ X static files copied to '/app/staticfiles'
✅ Starting server at tcp:port=8080
```

## 🔄 Actualizar la PWA

Cuando hagas cambios en el Service Worker:

1. **Incrementa la versión del caché** en `service-worker.js`:
```javascript
const CACHE_NAME = 'taxi-app-v4'; // Cambiar de v3 a v4
```

2. **Haz commit y push**:
```bash
git add .
git commit -m "Actualizar Service Worker a v4"
git push origin main
```

3. **Los usuarios verán la actualización** automáticamente la próxima vez que visiten la app

## 📱 Probar en Dispositivos Móviles

### Android (Chrome):
1. Abre la app en Chrome
2. Toca el menú (⋮) → "Instalar aplicación"
3. La app se añadirá a tu pantalla de inicio

### iOS (Safari):
1. Abre la app en Safari
2. Toca el botón compartir
3. "Añadir a pantalla de inicio"

## 🎯 Checklist Final

Antes de considerar el despliegue completo:

- [ ] Archivos estáticos cargan correctamente (sin 404)
- [ ] Service Worker se registra sin errores
- [ ] Manifest.json es accesible
- [ ] La app se puede instalar
- [ ] Las notificaciones funcionan
- [ ] El modo offline funciona
- [ ] WebSockets conectan correctamente
- [ ] El mapa de Google Maps carga
- [ ] La comunicación de audio funciona

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa los logs de Railway**
2. **Verifica la consola del navegador**
3. **Comprueba que todas las variables de entorno estén configuradas**:
   - `GOOGLE_API_KEY` ✅
   - `REDIS_URL` ✅
   - `DATABASE_URL` ✅

## 📚 Recursos Adicionales

- [Documentación de Railway](https://docs.railway.app/)
- [Guía de Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)
- [PWA Features Documentation](./PWA_FEATURES.md)

---

**Última actualización**: 2025-10-28  
**Versión PWA**: 3.0  
**Estado**: ✅ Listo para desplegar
