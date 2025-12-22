# Guía de Despliegue en Railway con Migraciones Automáticas

## ✅ Configuración Actual

Tu proyecto ya está configurado para ejecutar migraciones automáticamente cuando se hace push a Railway.

### Archivos de Configuración

1. **`railway.yaml`** - Configura el comando de inicio
2. **`railway_start.py`** - Ejecuta migraciones antes de iniciar el servidor
3. **`railway_pre_deploy.py`** - Ejecuta collectstatic antes del despliegue

## 🔄 Flujo de Despliegue Automático

Cuando haces push a tu repositorio conectado a Railway:

1. **Railway detecta el push** → Inicia el build
2. **Pre-deploy** → Ejecuta `railway_pre_deploy.py` (collectstatic)
3. **Start Command** → Ejecuta `railway_start.py` que:
   - ✅ Ejecuta `python manage.py migrate --noinput` (línea 50)
   - ✅ Verifica archivos estáticos
   - ✅ Inicia el servidor con Daphne

## 📋 Pasos para Hacer Push y Actualizar la Base de Datos

### 1. Crear las Migraciones Localmente (si aún no lo hiciste)

```bash
python manage.py makemigrations
```

Esto creará un archivo en `taxis/migrations/` con los nuevos campos de media.

### 2. Verificar las Migraciones

```bash
python manage.py showmigrations
```

Deberías ver algo como:
```
taxis
 [X] 0017_chatmessage
 [ ] 0018_chatmessage_message_type  # Nueva migración
```

### 3. Hacer Commit de las Migraciones

```bash
git add taxis/migrations/
git add taxis/models.py
git add taxis/consumers.py
git add taxis/views.py
git add taxis/urls.py
git add taxis/serializers.py
git add railway_start.py
git commit -m "Agregar soporte de media al chat (imágenes/videos)"
```

### 4. Hacer Push a Railway

```bash
git push origin main
# o
git push origin master
```

### 5. Railway Ejecutará Automáticamente

Railway detectará el push y:
1. ✅ Construirá la aplicación
2. ✅ Ejecutará `railway_pre_deploy.py` (collectstatic)
3. ✅ Ejecutará `railway_start.py` que incluye:
   - `python manage.py migrate --noinput` ← **Esto actualiza la BD**
   - Inicia el servidor

## 🔍 Verificar que las Migraciones se Ejecutaron

Después del push, revisa los logs de Railway:

1. Ve a tu proyecto en Railway
2. Abre la pestaña "Deployments"
3. Haz clic en el deployment más reciente
4. Revisa los logs y busca:

```
[EJECUTANDO] Aplicando migraciones de base de datos (AUTOMATICO)
Operations to perform:
  Apply all migrations: taxis
Running migrations:
  Applying taxis.0018_chatmessage_message_type... OK
```

## ⚠️ Si las Migraciones No se Ejecutan Automáticamente

Si por alguna razón las migraciones no se ejecutan, puedes ejecutarlas manualmente desde Railway:

### Opción 1: Desde Railway CLI

```bash
railway run python manage.py migrate
```

### Opción 2: Desde el Dashboard de Railway

1. Ve a tu proyecto en Railway
2. Abre la pestaña "Deployments"
3. Haz clic en "View Logs"
4. Abre la terminal
5. Ejecuta: `python manage.py migrate`

### Opción 3: Agregar como Variable de Entorno

Puedes agregar un comando personalizado en Railway:

1. Ve a tu proyecto → Settings → Variables
2. Agrega: `RAILWAY_RUN_MIGRATIONS=true`
3. Modifica `railway_start.py` para verificar esta variable

## 🛠️ Mejoras Opcionales

### Agregar Verificación de Migraciones Pendientes

Puedes mejorar `railway_start.py` para mostrar qué migraciones se aplicarán:

```python
# En railway_start.py, después de la línea 50
print("\n[INFO] Migraciones aplicadas exitosamente")
print("[INFO] Verificando estado de la base de datos...")
subprocess.run(
    "python manage.py showmigrations --list",
    shell=True,
    capture_output=False,
    text=True
)
```

### Agregar Rollback en Caso de Error

Si una migración falla, puedes agregar lógica de rollback (opcional):

```python
# En railway_start.py
try:
    run_command(
        "python manage.py migrate --noinput --verbosity 1",
        "Aplicando migraciones de base de datos (AUTOMATICO)"
    )
except Exception as e:
    print(f"[ERROR] Migración falló: {e}")
    print("[INFO] Revisa los logs para más detalles")
    sys.exit(1)
```

## ✅ Checklist Antes de Hacer Push

- [ ] Migraciones creadas localmente (`makemigrations`)
- [ ] Migraciones probadas localmente (`migrate`)
- [ ] Archivos de migración agregados a Git
- [ ] Cambios en modelos/views/consumers agregados a Git
- [ ] `railway_start.py` está actualizado
- [ ] Repositorio conectado a Railway
- [ ] Variables de entorno configuradas en Railway (DATABASE_URL, etc.)

## 🎯 Resumen

**Tu configuración actual ya ejecuta migraciones automáticamente** cuando haces push. Solo necesitas:

1. ✅ Crear las migraciones localmente
2. ✅ Hacer commit de los cambios
3. ✅ Hacer push a tu repositorio
4. ✅ Railway ejecutará las migraciones automáticamente

No necesitas hacer nada adicional. Railway ejecutará `railway_start.py` que ya incluye el comando `migrate`.

