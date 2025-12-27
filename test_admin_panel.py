"""
Script para verificar que el panel de administración esté correctamente configurado
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from taxis.models import Organization

User = get_user_model()

print("=" * 60)
print("VERIFICACIÓN DEL PANEL DE ADMINISTRACIÓN")
print("=" * 60)

# 1. Verificar URLs
print("\n1. Verificando URLs del panel admin...")
admin_urls = [
    'admin_dashboard',
    'admin_organizations',
    'admin_organization_create',
    'admin_drivers_pending',
    'admin_reports_financial',
    'admin_invoices',
    'admin_invoice_create',
]

for url_name in admin_urls:
    try:
        url = reverse(url_name)
        print(f"   ✅ {url_name:30} → {url}")
    except Exception as e:
        print(f"   ❌ {url_name:30} → ERROR: {e}")

# 2. Verificar superusuarios
print("\n2. Verificando superusuarios...")
superusers = User.objects.filter(is_superuser=True)
if superusers.exists():
    for user in superusers:
        print(f"   ✅ Superuser encontrado: {user.username} (ID: {user.id})")
else:
    print("   ⚠️  No hay superusuarios creados")
    print("   💡 Crea uno con: python manage.py createsuperuser")

# 3. Verificar organizaciones
print("\n3. Verificando organizaciones...")
orgs = Organization.objects.all()
if orgs.exists():
    for org in orgs:
        print(f"   ✅ Organización: {org.name} (Plan: {org.get_plan_display()})")
else:
    print("   ⚠️  No hay organizaciones creadas")

# 4. Verificar templates
print("\n4. Verificando templates...")
import os
from django.conf import settings

templates_to_check = [
    'admin/base_admin.html',
    'admin/dashboard.html',
    'admin/organizations/list.html',
    'admin/organizations/create.html',
    'admin/drivers/approval_list.html',
    'admin/reports/financial.html',
    'admin/invoices/list.html',
]

for template_path in templates_to_check:
    # Buscar en todos los directorios de templates
    found = False
    for template_dir in settings.TEMPLATES[0]['DIRS']:
        full_path = os.path.join(template_dir, template_path)
        if os.path.exists(full_path):
            print(f"   ✅ {template_path}")
            found = True
            break
    
    # También buscar en app templates
    if not found:
        app_template_path = os.path.join('taxis', 'templates', template_path)
        if os.path.exists(app_template_path):
            print(f"   ✅ {template_path}")
            found = True
    
    if not found:
        print(f"   ❌ {template_path} - NO ENCONTRADO")

# 5. Verificar decoradores
print("\n5. Verificando decoradores...")
try:
    from taxis.decorators import superadmin_required, organization_admin_required
    print("   ✅ superadmin_required importado correctamente")
    print("   ✅ organization_admin_required importado correctamente")
except ImportError as e:
    print(f"   ❌ Error al importar decoradores: {e}")

# 6. Verificar vistas
print("\n6. Verificando vistas del panel admin...")
try:
    from taxis import admin_views
    views_to_check = [
        'SuperAdminDashboardView',
        'OrganizationListView',
        'OrganizationCreateView',
        'DriverApprovalListView',
        'FinancialReportsView',
        'InvoiceListView',
    ]
    
    for view_name in views_to_check:
        if hasattr(admin_views, view_name):
            print(f"   ✅ {view_name}")
        else:
            print(f"   ❌ {view_name} - NO ENCONTRADA")
except ImportError as e:
    print(f"   ❌ Error al importar admin_views: {e}")

print("\n" + "=" * 60)
print("RESUMEN:")
print("=" * 60)
print("\n✅ Si todos los checks están en verde, el panel está listo.")
print("⚠️  Si hay warnings, revisa las secciones marcadas.")
print("❌ Si hay errores, corrige los problemas antes de continuar.")
print("\n📝 Para acceder al panel:")
print("   1. Asegúrate de tener un superusuario creado")
print("   2. Inicia sesión con ese usuario")
print("   3. Ve a: /admin/dashboard/")
print("\n" + "=" * 60)
