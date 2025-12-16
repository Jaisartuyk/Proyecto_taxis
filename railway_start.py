#!/usr/bin/env python
"""
Script de despliegue para Railway
Ejecuta collectstatic con logging visible y luego inicia el servidor
"""
import os
import sys
import subprocess

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(command, shell=True, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"\n❌ Error en: {description}")
        sys.exit(result.returncode)
    else:
        print(f"\n✅ {description} - Completado")
    
    return result.returncode

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 INICIANDO DESPLIEGUE EN RAILWAY")
    print("="*60 + "\n")
    
    # 1. Collectstatic (con verbosidad para debug)
    run_command(
        # IMPORTANTE (Railway): verbosity alta puede disparar el rate limit de logs (500 logs/s)
        # porque collectstatic imprime miles de líneas (Copying/Deleting/Post-processed).
        "python manage.py collectstatic --noinput --verbosity 0",
        "Recopilando archivos estáticos (collectstatic, silencioso)"
    )
    
    # 2. Migraciones
    run_command(
        "python manage.py migrate --noinput",
        "Aplicando migraciones de base de datos"
    )
    
    # 3. Iniciar servidor
    print("\n" + "="*60)
    print("🌐 INICIANDO SERVIDOR DAPHNE")
    print("="*60 + "\n")
    
    port = os.environ.get('PORT', '8080')
    os.execvp('daphne', ['daphne', '-b', '0.0.0.0', '-p', port, 'taxi_project.asgi:application'])
