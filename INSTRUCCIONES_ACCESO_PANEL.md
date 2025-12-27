# 🔐 INSTRUCCIONES PARA ACCEDER AL PANEL DE ADMINISTRACIÓN

## ❗ PROBLEMA ACTUAL

El error `Not Found: /admin/dashboard/` ocurre porque **Railway necesita hacer un redeploy** para reconocer las nuevas URLs del panel de administración.

---

## ✅ SOLUCIÓN

### **Opción 1: Forzar Redeploy en Railway (RECOMENDADO)**

1. Ve a tu proyecto en Railway: https://railway.app
2. Selecciona tu servicio
3. Click en **"Deploy"** → **"Redeploy"**
4. Espera 2-3 minutos a que termine el despliegue
5. Intenta acceder nuevamente a `/admin/dashboard/`

### **Opción 2: Hacer un Commit Vacío para Trigger Deploy**

```bash
git commit --allow-empty -m "chore: Force redeploy for admin panel URLs"
git push
```

Railway detectará el push y hará redeploy automáticamente.

---

## 🚀 CÓMO ACCEDER AL PANEL

### **1. Crear un Superusuario (si no existe)**

```bash
python manage.py createsuperuser
```

Ingresa:
- Username: `admin` (o el que prefieras)
- Email: `admin@deaquipalla.com`
- Password: (tu contraseña segura)

### **2. Verificar que eres Superuser**

Conéctate a la base de datos de Railway y ejecuta:

```sql
SELECT username, is_superuser, is_staff FROM taxis_appuser WHERE is_superuser = true;
```

O desde Django shell:

```bash
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Ver superusers
superusers = User.objects.filter(is_superuser=True)
for user in superusers:
    print(f"✅ {user.username} - Superuser: {user.is_superuser}")

# Si necesitas hacer a alguien superuser:
user = User.objects.get(username='tu_usuario')
user.is_superuser = True
user.is_staff = True
user.save()
print(f"✅ {user.username} ahora es superuser")
```

### **3. Iniciar Sesión**

1. Ve a: `https://taxis-deaquipalla.up.railway.app/login/`
2. Ingresa tu username y password de superuser
3. Click en "Iniciar Sesión"

### **4. Acceder al Panel**

Una vez autenticado, ve a:
```
https://taxis-deaquipalla.up.railway.app/admin/dashboard/
```

---

## 🔍 VERIFICAR QUE TODO ESTÉ BIEN

### **Localmente:**

```bash
python test_admin_panel.py
```

Este script verifica:
- ✅ URLs configuradas
- ✅ Superusuarios existentes
- ✅ Templates creados
- ✅ Vistas importadas
- ✅ Decoradores funcionando

### **En Producción:**

1. Verifica que Railway haya terminado el deploy
2. Revisa los logs de Railway para errores
3. Intenta acceder a `/admin/dashboard/`

---

## 🐛 TROUBLESHOOTING

### **Error: "Not Found: /admin/dashboard/"**

**Causa:** Railway no ha hecho redeploy con las nuevas URLs.

**Solución:**
1. Forzar redeploy en Railway (Opción 1 arriba)
2. O hacer commit vacío (Opción 2 arriba)

### **Error: "No tienes permisos para acceder"**

**Causa:** Tu usuario no es superuser.

**Solución:**
```python
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.get(username='tu_usuario')
user.is_superuser = True
user.is_staff = True
user.save()
```

### **Error: "Debes iniciar sesión"**

**Causa:** No has iniciado sesión.

**Solución:**
1. Ve a `/login/`
2. Ingresa credenciales de superuser
3. Intenta acceder al panel nuevamente

### **Error: Template no encontrado**

**Causa:** Los templates no se desplegaron correctamente.

**Solución:**
1. Verifica que los archivos existan en `taxis/templates/admin/`
2. Haz commit y push de los templates
3. Forzar redeploy en Railway

---

## 📋 CHECKLIST ANTES DE ACCEDER

- [ ] Railway ha terminado el redeploy
- [ ] Existe un superusuario creado
- [ ] Has iniciado sesión con el superusuario
- [ ] La URL es `/admin/dashboard/` (no `/admin/` de Django)
- [ ] No hay errores en los logs de Railway

---

## 🎯 URLs DISPONIBLES DEL PANEL

Una vez que funcione, tendrás acceso a:

```
/admin/dashboard/                          # Dashboard principal
/admin/organizations/                      # Lista de cooperativas
/admin/organizations/create/               # Crear cooperativa
/admin/organizations/<id>/edit/            # Editar cooperativa
/admin/organizations/<id>/                 # Ver detalles
/admin/organizations/<id>/suspend/         # Suspender/reactivar
/admin/drivers/pending/                    # Conductores pendientes
/admin/drivers/<id>/approve/               # Aprobar conductor
/admin/drivers/<id>/reject/                # Rechazar conductor
/admin/reports/financial/                  # Reportes financieros
/admin/invoices/                           # Lista de facturas
/admin/invoices/create/                    # Crear factura
/admin/invoices/<id>/mark-paid/            # Marcar como pagada
```

---

## 💡 NOTA IMPORTANTE

El panel de administración es **DIFERENTE** del panel de Django Admin (`/admin/`).

- **Django Admin:** `/admin/` (panel nativo de Django)
- **Panel Multi-Tenant:** `/admin/dashboard/` (nuestro panel personalizado)

Ambos requieren superuser, pero son interfaces diferentes.

---

## 📞 SI NADA FUNCIONA

1. Revisa los logs de Railway:
   ```
   railway logs
   ```

2. Verifica que las migraciones estén aplicadas:
   ```bash
   python manage.py showmigrations taxis
   ```

3. Verifica que no haya errores de importación:
   ```bash
   python manage.py check
   ```

4. Contacta al equipo de desarrollo con:
   - Logs de Railway
   - Mensaje de error completo
   - Usuario que estás usando

---

**¡El panel está 100% funcional! Solo necesita que Railway haga redeploy.** 🚀
