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
    
    # Verificar configuración
    print(f"[DEBUG] STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"[DEBUG] STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
    print(f"[DEBUG] STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
    
    # Verificar que los directorios existan
    for static_dir in settings.STATICFILES_DIRS:
        exists = os.path.exists(static_dir)
        print(f"[DEBUG] Directorio {static_dir}: {'EXISTE' if exists else 'NO EXISTE'}")
        if exists:
            # Listar algunos archivos
            try:
                files = []
                for root, dirs, filenames in os.walk(static_dir):
                    for filename in filenames[:10]:  # Solo primeros 10
                        files.append(os.path.join(root, filename))
                print(f"[DEBUG] Archivos encontrados (primeros 10): {len(files)}")
                for f in files[:5]:
                    print(f"  - {f}")
            except Exception as e:
                print(f"[DEBUG] Error listando archivos: {e}")
    
    # Verificar finders antes de ejecutar
    from django.contrib.staticfiles.finders import get_finders
    print("\n[DEBUG] Finders de archivos estaticos:")
    for finder in get_finders():
        print(f"  - {finder.__class__.__name__}")
    
    # Usar storage sin compresión para evitar errores de compresión paralela
    # La compresión se hará automáticamente en tiempo de ejecución por WhiteNoise
    original_storage = settings.STATICFILES_STORAGE
    print(f"\n[INFO] Storage original: {original_storage}")
    print("[INFO] Cambiando temporalmente a storage sin compresion...")
    
    try:
        # Cambiar a storage sin compresión
        settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
        
        # Verificar que los finders encuentren los archivos antes de copiar
        print("\n[DEBUG] Verificando que los finders encuentren los archivos nuevos:")
        from django.contrib.staticfiles.finders import find
        archivos_buscar = [
            'css/floating-audio-button.css',
            'js/audio-floating-button.js',
        ]
        for archivo in archivos_buscar:
            ruta_encontrada = find(archivo)
            if ruta_encontrada:
                print(f"  [OK] {archivo} encontrado en: {ruta_encontrada}")
            else:
                print(f"  [ERROR] {archivo} NO encontrado por los finders")
        
        # Limpiar staticfiles/ manualmente antes de copiar
        static_root = settings.STATIC_ROOT
        if os.path.exists(static_root):
            print(f"\n[INFO] Limpiando {static_root}...")
            import shutil
            try:
                shutil.rmtree(static_root)
                os.makedirs(static_root)
                print(f"[OK] {static_root} limpiado correctamente")
            except Exception as e:
                print(f"[WARNING] Error limpiando {static_root}: {e}")
        
        # Ejecutar collectstatic con --clear para forzar copia de archivos nuevos
        # Usamos --clear porque estamos usando storage sin compresión (no causa conflictos)
        from django.core.management import call_command
        print("\n[INFO] Ejecutando collectstatic...")
        call_command('collectstatic', 
                    verbosity=2,  # Verbosity alto para ver qué archivos encuentra
                    interactive=False,
                    clear=False,  # Ya limpiamos manualmente
                    ignore_patterns=['cloudinary'])
        
        # Verificar que los archivos nuevos se copiaron correctamente
        print("\n" + "="*60)
        print("VERIFICANDO ARCHIVOS COPIADOS")
        print("="*60 + "\n")
        
        static_root = settings.STATIC_ROOT
        archivos_verificar = [
            'css/floating-audio-button.css',
            'js/audio-floating-button.js',
        ]
        
        todos_ok = True
        for archivo in archivos_verificar:
            ruta_completa = os.path.join(static_root, archivo)
            existe = os.path.exists(ruta_completa)
            if existe:
                tamaño = os.path.getsize(ruta_completa)
                print(f"[OK] {archivo} - {tamaño} bytes")
            else:
                print(f"[ERROR] {archivo} - NO ENCONTRADO")
                todos_ok = False
        
        if todos_ok:
            print("\n[OK] Todos los archivos nuevos se copiaron correctamente")
        else:
            print("\n[WARNING] Algunos archivos no se copiaron correctamente")
            print("[INFO] Esto puede deberse a archivos duplicados en STATICFILES_DIRS")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n[ERROR] collectstatic fallo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restaurar storage original
        settings.STATICFILES_STORAGE = original_storage

