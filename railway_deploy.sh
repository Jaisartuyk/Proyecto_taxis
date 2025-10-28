#!/bin/bash
# Script de despliegue para Railway

echo "🚀 Iniciando despliegue en Railway..."

# Recolectar archivos estáticos
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Aplicar migraciones
echo "🔄 Aplicando migraciones..."
python manage.py migrate --noinput

echo "✅ Despliegue completado!"
echo "🌐 La aplicación está lista para servir"
