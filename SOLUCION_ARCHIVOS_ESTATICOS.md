# 🔧 Solución: Archivos Estáticos 404

## Problema Actual:
Los archivos PWA están dando 404:
- `/static/js/service-worker.js` ❌
- `/static/js/notifications.js` ❌
- `/static/js/install-prompt.js` ❌
- `/static/manifest.json` ❌

## ✅ Solución: Forzar Redespliegue en Railway

### Opción 1: Desde Railway Dashboard (Recomendado)

1. **Ve a Railway Dashboard**:
   - https://railway.app/dashboard

2. **Selecciona tu proyecto**:
   - "taxis-deaquipalla" o similar

3. **Ve a Settings**:
   - Click en la pestaña "Settings"

4. **Forzar Redespliegue**:
   - Busca el botón "Redeploy"
   - Click en "Redeploy"
   - Espera 2-3 minutos

5. **Verifica los logs**:
   - Ve a la pestaña "Deployments"
   - Click en el deployment más reciente
   - Busca en los logs:
   ```
   ✓ Collecting static files
   ✓ X static files copied to '/app/staticfiles'
   ```

### Opción 2: Ejecutar Collectstatic Manualmente

Si el redespliegue no funciona, ejecuta collectstatic manualmente:

1. **Desde Railway CLI**:
```bash
# Instalar Railway CLI (si no lo tienes)
npm i -g @railway/cli

# Login
railway login

# Link al proyecto
railway link

# Ejecutar collectstatic
railway run python manage.py collectstatic --noinput
```

2. **Reiniciar el servicio**:
```bash
railway restart
```

### Opción 3: Variable de Entorno

Añade una variable de entorno en Railway para forzar collectstatic:

1. Ve a Railway Dashboard → tu proyecto
2. Click en "Variables"
3. Añade:
   - **Key**: `DJANGO_SETTINGS_MODULE`
   - **Value**: `taxi_project.settings`
4. Redeploy

## 🔍 Verificación

Después del redespliegue, verifica que los archivos carguen:

```
https://taxis-deaquipalla.up.railway.app/static/js/service-worker.js
https://taxis-deaquipalla.up.railway.app/static/js/notifications.js
https://taxis-deaquipalla.up.railway.app/static/manifest.json
```

Deberías ver el código JavaScript/JSON, no un error 404.

## 📊 Diagnóstico

### Verificar en los logs de Railway:

**✅ Correcto**:
```
Collecting static files...
X static files copied to '/app/staticfiles'
```

**❌ Incorrecto**:
```
No se menciona collectstatic
O hay errores durante collectstatic
```

## 🎯 Causa del Problema

Railway no está ejecutando `collectstatic` porque:
1. El `railway.yaml` puede no estar siendo detectado
2. O el comando se está ejecutando antes de que las dependencias estén instaladas

## ✨ Solución Alternativa: Script de Inicio

Si nada funciona, podemos modificar `entrypoint.sh` para ejecutar collectstatic:

```bash
#!/bin/bash
# Entrypoint script para Railway

# Usar el puerto proporcionado por Railway o 8080 por defecto
PORT=${PORT:-8080}

echo "🚀 Iniciando servidor en puerto $PORT"
echo "📦 Recolectando archivos estáticos..."

# Ejecutar collectstatic
python manage.py collectstatic --noinput

echo "✅ Archivos estáticos recolectados"

# Iniciar daphne
exec daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
```

Luego:
```bash
git add entrypoint.sh
git commit -m "Add: collectstatic en entrypoint.sh"
git push
```

## 📞 Si Nada Funciona

Como último recurso, podemos servir los archivos estáticos directamente desde Django en producción (no recomendado pero funcional):

En `settings.py`:
```python
# Solo para debugging
if os.environ.get('RAILWAY_ENVIRONMENT'):
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
```

---

**Recomendación**: Intenta primero la Opción 1 (Redeploy desde Dashboard)
