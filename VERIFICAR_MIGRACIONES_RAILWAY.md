# Cómo Verificar Migraciones en Railway

## 🔍 Método 1: Revisar Logs de Railway (Recomendado)

### Paso 1: Acceder a Railway Dashboard

1. Ve a [railway.app](https://railway.app)
2. Inicia sesión en tu cuenta
3. Selecciona tu proyecto

### Paso 2: Revisar Logs del Último Deployment

1. En el dashboard de tu proyecto, haz clic en **"Deployments"** (o "Despliegues")
2. Selecciona el deployment más reciente (el que acabas de hacer push)
3. Haz clic en **"View Logs"** o **"Ver Logs"**

### Paso 3: Buscar en los Logs

Busca estas líneas en los logs:

```
============================================================
APLICANDO MIGRACIONES DE BASE DE DATOS
============================================================
[INFO] Este paso actualiza la estructura de la base de datos
[INFO] Se ejecuta automáticamente en cada despliegue

[EJECUTANDO] Aplicando migraciones de base de datos (AUTOMATICO)
Operations to perform:
  Apply all migrations: taxis
Running migrations:
  Applying taxis.0018_chatmessage_message_type... OK
  Applying taxis.0018_chatmessage_media_url... OK
  Applying taxis.0018_chatmessage_thumbnail_url... OK
  Applying taxis.0018_chatmessage_metadata... OK
```

### ✅ Señales de Éxito

- Ver `Applying taxis.XXXX... OK` para cada migración
- Ver `[OK] Aplicando migraciones de base de datos (AUTOMATICO) - Completado`
- No ver errores como `django.db.utils.OperationalError` o `django.db.utils.ProgrammingError`

### ❌ Señales de Error

- Ver `django.db.utils.OperationalError`
- Ver `django.db.utils.ProgrammingError`
- Ver `No such column` o `column does not exist`
- Ver `relation already exists` (puede ser normal si la migración ya se aplicó)

## 🔍 Método 2: Usar Railway CLI

### Instalar Railway CLI (si no lo tienes)

```bash
npm i -g @railway/cli
```

O descargar desde: https://railway.app/cli

### Conectar a tu Proyecto

```bash
railway login
railway link
```

### Ejecutar Comando de Verificación

```bash
# Ver migraciones aplicadas
railway run python manage.py showmigrations

# Ver migraciones pendientes
railway run python manage.py showmigrations --list | grep '\[ \]'
```

### Verificar Estado de la Base de Datos

```bash
# Conectarse a la base de datos PostgreSQL
railway run python manage.py dbshell

# Dentro de la shell de PostgreSQL, ejecutar:
\d taxis_chatmessage

# Esto mostrará la estructura de la tabla, incluyendo los nuevos campos:
# - message_type
# - media_url
# - thumbnail_url
# - metadata
```

## 🔍 Método 3: Verificar desde el Código (API/Django Shell)

### Opción A: Crear una Vista de Verificación Temporal

Agregar a `taxis/views.py`:

```python
@login_required
def verify_migrations(request):
    """Vista temporal para verificar migraciones"""
    from django.db import connection
    from .models import ChatMessage
    
    try:
        # Verificar que el modelo tiene los nuevos campos
        fields = [f.name for f in ChatMessage._meta.get_fields()]
        
        has_message_type = 'message_type' in fields
        has_media_url = 'media_url' in fields
        has_thumbnail_url = 'thumbnail_url' in fields
        has_metadata = 'metadata' in fields
        
        # Verificar en la base de datos directamente
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'taxis_chatmessage'
            """)
            db_columns = [row[0] for row in cursor.fetchall()]
        
        return JsonResponse({
            'model_fields': fields,
            'db_columns': db_columns,
            'migration_status': {
                'message_type': has_message_type and 'message_type' in db_columns,
                'media_url': has_media_url and 'media_url' in db_columns,
                'thumbnail_url': has_thumbnail_url and 'thumbnail_url' in db_columns,
                'metadata': has_metadata and 'metadata' in db_columns,
            },
            'all_ok': all([
                has_message_type and 'message_type' in db_columns,
                has_media_url and 'media_url' in db_columns,
                has_thumbnail_url and 'thumbnail_url' in db_columns,
                has_metadata and 'metadata' in db_columns,
            ])
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
```

Agregar a `taxis/urls.py`:

```python
path('verify-migrations/', views.verify_migrations, name='verify_migrations'),
```

Luego visitar: `https://tu-proyecto.railway.app/verify-migrations/`

### Opción B: Usar Django Admin

1. Ve a `https://tu-proyecto.railway.app/admin/`
2. Inicia sesión como admin
3. Ve a **Taxis** → **Chat Messages**
4. Intenta crear un nuevo mensaje
5. Verifica que aparezcan los campos:
   - Message type
   - Media URL
   - Thumbnail URL
   - Metadata

## 🔍 Método 4: Verificar desde la Base de Datos Directamente

### Usando Railway Dashboard

1. Ve a tu proyecto en Railway
2. Haz clic en la base de datos PostgreSQL
3. Haz clic en **"Data"** o **"Query"**
4. Ejecuta esta consulta:

```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'taxis_chatmessage'
ORDER BY ordinal_position;
```

Deberías ver los nuevos campos:
- `message_type` (character varying)
- `media_url` (character varying)
- `thumbnail_url` (character varying)
- `metadata` (jsonb)

### Verificar con una Consulta de Prueba

```sql
-- Ver estructura de la tabla
\d taxis_chatmessage

-- O en Railway Query:
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'taxis_chatmessage'
AND column_name IN ('message_type', 'media_url', 'thumbnail_url', 'metadata');
```

## 🔍 Método 5: Probar Funcionalidad Directamente

### Probar Subida de Archivo

1. Ve a `/central-comunicacion/`
2. Selecciona un conductor
3. Haz clic en el botón 📎
4. Selecciona una imagen
5. Verifica que:
   - El archivo se suba a Cloudinary
   - El mensaje se envíe con `message_type: 'image'`
   - El mensaje se guarde en la base de datos

### Verificar en los Logs del Servidor

Después de enviar un mensaje con imagen, revisa los logs de Railway y busca:

```
Mensaje guardado en BD: Admin -> Conductor (tipo: image)
```

## 📋 Checklist de Verificación

- [ ] Logs de Railway muestran `Applying taxis.XXXX... OK`
- [ ] No hay errores de base de datos en los logs
- [ ] `showmigrations` muestra todas las migraciones como `[X]` (aplicadas)
- [ ] La tabla `taxis_chatmessage` tiene los campos nuevos
- [ ] Puedes crear un mensaje con imagen desde la interfaz
- [ ] El mensaje se guarda correctamente en la base de datos

## 🛠️ Si las Migraciones NO se Ejecutaron

### Opción 1: Ejecutar Manualmente desde Railway CLI

```bash
railway run python manage.py migrate
```

### Opción 2: Ejecutar desde Railway Dashboard

1. Ve a tu proyecto → **Deployments**
2. Haz clic en el deployment más reciente
3. Abre la terminal
4. Ejecuta: `python manage.py migrate`

### Opción 3: Verificar el Archivo railway_start.py

Asegúrate de que `railway_start.py` tenga esta línea:

```python
run_command(
    "python manage.py migrate --noinput --verbosity 1",
    "Aplicando migraciones de base de datos (AUTOMATICO)"
)
```

## 🎯 Comando Rápido de Verificación

Crea un script temporal `verify_migrations.py`:

```python
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
django.setup()

from django.db import connection
from taxis.models import ChatMessage

print("="*60)
print("VERIFICACIÓN DE MIGRACIONES")
print("="*60)

# Verificar campos en el modelo
fields = [f.name for f in ChatMessage._meta.get_fields()]
print(f"\n✅ Campos en el modelo: {len(fields)}")
print(f"   Campos: {', '.join(fields)}")

# Verificar campos en la base de datos
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'taxis_chatmessage'
        ORDER BY column_name
    """)
    db_columns = [row[0] for row in cursor.fetchall()]

print(f"\n✅ Columnas en la BD: {len(db_columns)}")
print(f"   Columnas: {', '.join(db_columns)}")

# Verificar campos nuevos
required_fields = ['message_type', 'media_url', 'thumbnail_url', 'metadata']
missing = [f for f in required_fields if f not in db_columns]

if missing:
    print(f"\n❌ Campos faltantes: {', '.join(missing)}")
    print("   ⚠️ Las migraciones NO se aplicaron correctamente")
else:
    print(f"\n✅ Todos los campos nuevos están presentes")
    print("   ✅ Las migraciones se aplicaron correctamente")

print("="*60)
```

Ejecutar en Railway:

```bash
railway run python verify_migrations.py
```

## 📝 Notas Importantes

1. **Las migraciones se ejecutan automáticamente** en cada despliegue gracias a `railway_start.py`
2. **Los logs son la mejor forma** de verificar que se ejecutaron
3. **Si hay errores**, aparecerán en los logs con el traceback completo
4. **Las migraciones son idempotentes**: ejecutarlas múltiples veces no causa problemas

## 🆘 Solución de Problemas

### Error: "relation already exists"
- **Causa**: La migración ya se aplicó anteriormente
- **Solución**: Normal, no es un error. La migración se saltará automáticamente

### Error: "column does not exist"
- **Causa**: La migración no se ejecutó
- **Solución**: Ejecutar manualmente `railway run python manage.py migrate`

### Error: "django.db.utils.OperationalError"
- **Causa**: Problema de conexión a la base de datos
- **Solución**: Verificar que `DATABASE_URL` esté configurada en Railway

