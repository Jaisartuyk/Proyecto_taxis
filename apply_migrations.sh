#!/bin/bash
# Script para aplicar migraciones manualmente en Railway

echo "🔄 Aplicando migraciones de WhatsApp..."
python manage.py migrate taxis 0016 --noinput

echo "✅ Migraciones aplicadas"
echo "📊 Verificando tablas..."
python manage.py dbshell -c "\dt taxis_whatsapp*"
