#!/bin/bash
# Entrypoint script para Railway

# Usar el puerto proporcionado por Railway o 8080 por defecto
PORT=${PORT:-8080}

echo "🚀 Iniciando servidor en puerto $PORT"

# Iniciar daphne
exec daphne -b 0.0.0.0 -p $PORT taxi_project.asgi:application
