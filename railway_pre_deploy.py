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
    print("\n[DEBUG] Finders de archivos estaticos ANTES del cambio:")
    for finder in get_finders():
        print(f"  - {finder.__class__.__name__}")
    
    # Usar storage sin compresión para evitar errores de compresión paralela
    # La compresión se hará automáticamente en tiempo de ejecución por WhiteNoise
    original_storage = settings.STATICFILES_STORAGE
    original_finders = settings.STATICFILES_FINDERS.copy() if hasattr(settings, 'STATICFILES_FINDERS') else None
    
    print(f"\n[INFO] Storage original: {original_storage}")
    print(f"[INFO] Finders originales: {original_finders}")
    print("[INFO] Cambiando temporalmente a storage sin compresion y desactivando AppDirectoriesFinder...")
    
    try:
        # Cambiar a storage sin compresión
        settings.STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
        
        # FORZAR configuración para evitar duplicados
        # Vaciar STATICFILES_DIRS y usar solo AppDirectoriesFinder
        settings.STATICFILES_DIRS = []
        settings.STATICFILES_FINDERS = [
            'django.contrib.staticfiles.finders.AppDirectoriesFinder',
        ]
        
        # Verificar que el cambio se aplicó
        print(f"[DEBUG] STATICFILES_DIRS después del cambio: {settings.STATICFILES_DIRS}")
        print(f"[DEBUG] STATICFILES_FINDERS después del cambio: {settings.STATICFILES_FINDERS}")
        
        # Verificar que el cambio se aplicó
        print("\n[DEBUG] Finders de archivos estaticos DESPUES del cambio:")
        for finder in get_finders():
            print(f"  - {finder.__class__.__name__}")
        
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
        
        # Verificar qué archivos encuentra el finder antes de ejecutar collectstatic
        print("\n[DEBUG] Verificando qué archivos encuentra AppDirectoriesFinder:")
        from django.contrib.staticfiles.finders import get_finders
        from django.contrib.staticfiles.storage import staticfiles_storage
        
        finders = get_finders()
        archivos_encontrados = []
        for finder in finders:
            print(f"  - Finder: {finder.__class__.__name__}")
            try:
                # Intentar listar archivos encontrados por este finder
                if hasattr(finder, 'list'):
                    for path, storage in finder.list([]):
                        archivos_encontrados.append(path)
                        if len(archivos_encontrados) <= 10:  # Solo primeros 10
                            print(f"    - {path}")
            except Exception as e:
                print(f"    Error listando archivos: {e}")
        
        print(f"\n[DEBUG] Total de archivos encontrados por finders: {len(archivos_encontrados)}")
        
        # Ejecutar collectstatic
        from django.core.management import call_command
        print("\n[INFO] Ejecutando collectstatic...")
        try:
            result = call_command('collectstatic', 
                        verbosity=2,  # Verbosity alto para ver detalles
                        interactive=False,
                        clear=False,  # Ya limpiamos manualmente
                        ignore_patterns=['cloudinary'],
                        link=False)  # No usar symlinks
            
            # Verificar si se copiaron archivos
            import subprocess
            check_result = subprocess.run(
                ['python', 'manage.py', 'collectstatic', '--dry-run', '--verbosity', '0'],
                capture_output=True,
                text=True
            )
            if '0 static files' in check_result.stdout:
                print("\n[WARNING] collectstatic reportó 0 archivos copiados")
                print("[INFO] Intentando copiar archivos manualmente...")
                
                # Copiar archivos manualmente desde taxis/static a staticfiles/
                source_dir = os.path.join(settings.BASE_DIR, 'taxis', 'static')
                dest_dir = settings.STATIC_ROOT
                
                if os.path.exists(source_dir):
                    import shutil
                    for root, dirs, files in os.walk(source_dir):
                        # Calcular ruta relativa
                        rel_path = os.path.relpath(root, source_dir)
                        if rel_path == '.':
                            dest_path = dest_dir
                        else:
                            dest_path = os.path.join(dest_dir, rel_path)
                        
                        # Crear directorio destino si no existe
                        os.makedirs(dest_path, exist_ok=True)
                        
                        # Copiar archivos
                        for file in files:
                            if 'cloudinary' not in file:
                                src_file = os.path.join(root, file)
                                dst_file = os.path.join(dest_path, file)
                                shutil.copy2(src_file, dst_file)
                                print(f"  [COPIADO] {os.path.join(rel_path, file) if rel_path != '.' else file}")
                    
                    print(f"\n[OK] Archivos copiados manualmente a {dest_dir}")
        except Exception as e:
            print(f"\n[ERROR] Error en collectstatic: {e}")
            import traceback
            traceback.print_exc()
        
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
        # Restaurar configuración original
        settings.STATICFILES_STORAGE = original_storage
        if original_finders:
            settings.STATICFILES_FINDERS = original_finders

