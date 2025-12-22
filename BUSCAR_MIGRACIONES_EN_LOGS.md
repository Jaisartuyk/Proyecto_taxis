# Cómo Buscar las Migraciones en los Logs de Railway

## 🔍 Dónde Buscar

Los logs que compartiste muestran solo el **PRE-DEPLOY** (collectstatic). Las migraciones se ejecutan **DESPUÉS**, en el **START COMMAND**.

## 📋 Pasos para Encontrar las Migraciones

### 1. En Railway Dashboard

1. Ve a tu proyecto → **Deployments**
2. Selecciona el deployment más reciente
3. Haz clic en **"View Logs"** o **"Ver Logs"**
4. **Desplázate hacia abajo** en los logs (las migraciones están DESPUÉS del pre-deploy)

### 2. Buscar Texto Específico

En los logs, busca estas palabras clave:

- `APLICANDO MIGRACIONES`
- `migrate --noinput`
- `Applying taxis`
- `Operations to perform`
- `Running migrations`

### 3. Ubicación en los Logs

El orden de ejecución es:

```
1. PRE-DEPLOY (collectstatic) ← Lo que ya viste
   ↓
2. START COMMAND (railway_start.py) ← Aquí están las migraciones
   ↓
3. Iniciar servidor (Daphne)
```

## 🔍 Qué Deberías Ver

Si las migraciones se ejecutaron, deberías ver algo como:

```
============================================================
APLICANDO MIGRACIONES DE BASE DE DATOS
============================================================
[INFO] Este paso actualiza la estructura de la base de datos
[INFO] Se ejecuta automáticamente en cada despliegue

[EJECUTANDO] Aplicando migraciones de base de datos (AUTOMATICO)
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, taxis
Running migrations:
  Applying taxis.0018_chatmessage_message_type... OK
  Applying taxis.0018_chatmessage_media_url... OK
  Applying taxis.0018_chatmessage_thumbnail_url... OK
  Applying taxis.0018_chatmessage_metadata... OK

[OK] Aplicando migraciones de base de datos (AUTOMATICO) - Completado

============================================================
VERIFICANDO ESTADO DE MIGRACIONES
============================================================
taxis
 [X] 0017_chatmessage
 [X] 0018_chatmessage_message_type
 [X] 0018_chatmessage_media_url
 [X] 0018_chatmessage_thumbnail_url
 [X] 0018_chatmessage_metadata

[INFO] Migraciones aplicadas: 5
[OK] Todas las migraciones están aplicadas
```

## ⚠️ Si NO Ves las Migraciones

### Posible Causa 1: El Deployment Aún Está en Progreso

- Espera a que termine el deployment
- Los logs se actualizan en tiempo real
- Las migraciones aparecen después del pre-deploy

### Posible Causa 2: El Deployment Falló Antes de Llegar a las Migraciones

- Revisa si hay errores en los logs
- Busca mensajes de error en rojo
- Verifica que el deployment esté "Active" (no "Failed")

### Posible Causa 3: Las Migraciones Ya Se Aplicaron en un Deployment Anterior

- Si las migraciones ya se aplicaron, Django las saltará
- Verás: `No migrations to apply`
- Esto es normal y correcto

## ✅ Verificación Rápida

### Opción 1: Ejecutar el Script de Verificación

```bash
railway run python verify_migrations.py
```

Esto te dirá inmediatamente si los campos están en la BD.

### Opción 2: Verificar desde la Interfaz

1. Ve a `/central-comunicacion/`
2. Selecciona un conductor
3. Intenta subir una imagen con el botón 📎
4. Si funciona, las migraciones están aplicadas

### Opción 3: Verificar en la Base de Datos

En Railway Dashboard → PostgreSQL → Query:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'taxis_chatmessage'
AND column_name IN ('message_type', 'media_url', 'thumbnail_url', 'metadata');
```

Si ves los 4 campos, las migraciones están aplicadas.

## 🎯 Resumen

**Los logs que compartiste muestran solo el PRE-DEPLOY.**

**Las migraciones aparecen DESPUÉS, en la sección START COMMAND.**

**Desplázate hacia abajo en los logs** o busca `APLICANDO MIGRACIONES` para encontrarlas.


