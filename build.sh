#!/bin/bash
set -e

echo "🔨 Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo "✅ Build completado"
