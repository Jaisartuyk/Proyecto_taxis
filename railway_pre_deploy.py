#!/usr/bin/env python
"""
Script de pre-deploy para Railway
Ejecuta collectstatic usando storage sin compresión para evitar errores de archivos faltantes
"""
import os
import sys
import django
from django.conf import settings

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')

# Inicializar Django
django.setup()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PRE-DEPLOY: COLECTANDO ARCHIVOS ESTATICOS")
    print("="*60 + "\n")
    print("[INFO] Usando storage sin compresion para evitar errores")
    print("[INFO] La compresion se hara automaticamente en tiempo de ejecucion\n")
    
    # Guardar storage original
    original_storage = settings.STATICFILES_STORAGE
    
    try:
        # Cambiar temporalmente a storage sin compresión
        settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
        
        # Ejecutar collectstatic
        from django.core.management import call_command
        call_command('collectstatic', 
                    verbosity=1, 
                    interactive=False, 
                    ignore_patterns=['cloudinary'])
        
        print("\n[OK] Archivos estaticos recolectados correctamente")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] collectstatic fallo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restaurar storage original (aunque ya no importa)
        settings.STATICFILES_STORAGE = original_storage

