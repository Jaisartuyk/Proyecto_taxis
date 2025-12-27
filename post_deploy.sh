#!/bin/bash
# Script de post-deploy para Railway
# Se ejecuta automáticamente después de cada despliegue

echo "=========================================="
echo "🚀 POST-DEPLOY: Iniciando verificaciones"
echo "=========================================="

# 1. Aplicar migraciones
echo ""
echo "📊 1. Aplicando migraciones..."
python manage.py migrate --noinput

# 2. Recolectar archivos estáticos
echo ""
echo "📦 2. Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# 3. Verificar panel de administración
echo ""
echo "🔍 3. Verificando panel de administración..."
python test_admin_panel.py

# 4. Verificar superusuarios
echo ""
echo "👤 4. Verificando superusuarios..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
superusers = User.objects.filter(is_superuser=True)
if superusers.exists():
    print(f"✅ Encontrados {superusers.count()} superusuario(s):")
    for user in superusers:
        print(f"   - {user.username} ({user.email})")
else:
    print("⚠️  No hay superusuarios. Crea uno con: python manage.py createsuperuser")
EOF

echo ""
echo "=========================================="
echo "✅ POST-DEPLOY: Verificaciones completadas"
echo "=========================================="
echo ""
echo "🌐 Panel de administración disponible en:"
echo "   https://taxis-deaquipalla.up.railway.app/admin/dashboard/"
echo ""
