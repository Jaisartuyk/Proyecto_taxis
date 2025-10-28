#!/bin/bash
# Entrypoint script para Railway

# Usar el puerto proporcionado por Railway o 8080 por defecto
PORT=${PORT:-8080}

echo "🚀 Iniciando servidor en puerto $PORT"
echo "================================================"

# Mostrar migraciones pendientes
echo "📋 Verificando migraciones pendientes..."
python manage.py showmigrations taxis | tail -5

# Aplicar migraciones con verbose
echo "📊 Aplicando migraciones de base de datos..."
python manage.py migrate --noinput --verbosity 2

echo "✅ Migraciones aplicadas"
echo "================================================"

# Verificar tablas de WhatsApp
echo "🔍 Verificando tablas de WhatsApp..."
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute(\"SELECT tablename FROM pg_tables WHERE tablename LIKE 'taxis_whatsapp%'\"); print('Tablas WhatsApp:', [row[0] for row in cursor.fetchall()])" || echo "⚠️ No se pudieron verificar las tablas"

echo "================================================"

# Ejecutar collectstatic
echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Archivos estáticos recolectados"
echo "================================================"

# Iniciar daphne
echo "🌐 Iniciando servidor Daphne en puerto $PORT..."
exec daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
