#!/bin/bash
# Entrypoint script para Railway

# Usar el puerto proporcionado por Railway o 8080 por defecto
PORT=${PORT:-8080}

echo "🚀 Iniciando servidor en puerto $PORT"

# Aplicar migraciones
echo "📊 Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

echo "✅ Migraciones aplicadas"

# Ejecutar collectstatic
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Archivos estáticos recolectados"

# Iniciar daphne
echo "🌐 Iniciando servidor Daphne..."
exec daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
