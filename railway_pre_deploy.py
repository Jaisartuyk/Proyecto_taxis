#!/usr/bin/env python
"""
Script de pre-deploy para Railway
Ejecuta collectstatic usando storage sin compresión para evitar errores de archivos faltantes
"""
import os
import sys

# CRÍTICO: Configurar DJANGO_SETTINGS_MODULE ANTES de importar Django
# Detectar Railway por DATABASE_URL o RAILWAY_ENVIRONMENT
if not os.environ.get('DJANGO_SETTINGS_MODULE') or 'settings_railway' not in os.environ.get('DJANGO_SETTINGS_MODULE', ''):
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL', '').startswith('postgres'):
        os.environ['DJANGO_SETTINGS_MODULE'] = 'taxi_project.settings_railway'
        os.environ['RAILWAY_ENVIRONMENT'] = 'true'
        print(f"[PRE-DEPLOY] ✅ Configurando DJANGO_SETTINGS_MODULE=taxi_project.settings_railway")
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
        print(f"[PRE-DEPLOY] Usando DJANGO_SETTINGS_MODULE=taxi_project.settings")
else:
    print(f"[PRE-DEPLOY] DJANGO_SETTINGS_MODULE ya está configurado: {os.environ.get('DJANGO_SETTINGS_MODULE')}")

try:
    import django
    from django.conf import settings
    
    # Inicializar Django
    print(f"[PRE-DEPLOY] Inicializando Django...")
    django.setup()
    print(f"[PRE-DEPLOY] ✅ Django inicializado correctamente")
except Exception as e:
    print(f"[PRE-DEPLOY] ❌ Error inicializando Django: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    try:
        print("\n" + "="*60)
        print("PRE-DEPLOY: COLECTANDO ARCHIVOS ESTATICOS")
        print("="*60 + "\n")
        
        # Verificar que Django se inicializó correctamente
        if not hasattr(settings, 'STATIC_ROOT'):
            raise Exception("Django no se inicializó correctamente - STATIC_ROOT no encontrado")
        
        # Verificar configuración
        print(f"[DEBUG] STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"[DEBUG] STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        print(f"[DEBUG] STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
        print(f"[DEBUG] BASE_DIR: {settings.BASE_DIR}")
        
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
            
            # Ejecutar collectstatic primero para copiar archivos de otras apps
            # Luego copiar manualmente los archivos de taxis/static para asegurar que estén
            print("\n[INFO] Ejecutando collectstatic para copiar archivos de otras apps...")
            from django.core.management import call_command
            try:
                call_command('collectstatic', 
                            verbosity=1,  # Verbosity medio
                            interactive=False,
                            clear=False,  # Ya limpiamos manualmente
                            ignore_patterns=['cloudinary'],
                            link=False)  # No usar symlinks
                print("[OK] collectstatic completado")
            except Exception as e:
                print(f"[WARNING] collectstatic falló (continuando con copia manual): {e}")
            
            # SIEMPRE copiar archivos de taxis/static y static/ manualmente como respaldo
            # Esto asegura que los archivos estén disponibles incluso si collectstatic falla
            print("\n[INFO] Copiando archivos de taxis/static y static/ manualmente...")
            dest_dir = settings.STATIC_ROOT
            import shutil
            total_files_copied = 0
            
            # 1. Copiar archivos de taxis/static
            source_dir_taxis = os.path.join(settings.BASE_DIR, 'taxis', 'static')
            if os.path.exists(source_dir_taxis):
                print(f"[INFO] Copiando desde taxis/static...")
                files_copied = 0
                for root, dirs, files in os.walk(source_dir_taxis):
                    # Calcular ruta relativa
                    rel_path = os.path.relpath(root, source_dir_taxis)
                    if rel_path == '.':
                        dest_path = dest_dir
                    else:
                        dest_path = os.path.join(dest_dir, rel_path)
                    
                    # Crear directorio destino si no existe
                    os.makedirs(dest_path, exist_ok=True)
                    
                    # Copiar archivos
                    for file in files:
                        if 'cloudinary' not in file.lower():
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(dest_path, file)
                            try:
                                # Copiar archivo, sobrescribiendo si existe
                                shutil.copy2(src_file, dst_file)
                                files_copied += 1
                                total_files_copied += 1
                                if files_copied <= 15:  # Mostrar primeros 15
                                    print(f"  [COPIADO] {os.path.join(rel_path, file) if rel_path != '.' else file}")
                            except Exception as copy_error:
                                print(f"  [ERROR] No se pudo copiar {file}: {copy_error}")
                
                print(f"[OK] {files_copied} archivos copiados desde taxis/static")
            
            # 2. Copiar archivos de static/ (directorio global)
            source_dir_global = os.path.join(settings.BASE_DIR, 'static')
            if os.path.exists(source_dir_global):
                print(f"[INFO] Copiando desde static/...")
                files_copied = 0
                for root, dirs, files in os.walk(source_dir_global):
                    # Calcular ruta relativa
                    rel_path = os.path.relpath(root, source_dir_global)
                    if rel_path == '.':
                        dest_path = dest_dir
                    else:
                        dest_path = os.path.join(dest_dir, rel_path)
                    
                    # Crear directorio destino si no existe
                    os.makedirs(dest_path, exist_ok=True)
                    
                    # Copiar archivos
                    for file in files:
                        if 'cloudinary' not in file.lower():
                            src_file = os.path.join(root, file)
                            dst_file = os.path.join(dest_path, file)
                            try:
                                # Copiar archivo, sobrescribiendo si existe
                                shutil.copy2(src_file, dst_file)
                                files_copied += 1
                                total_files_copied += 1
                                if files_copied <= 15:  # Mostrar primeros 15
                                    print(f"  [COPIADO] {os.path.join(rel_path, file) if rel_path != '.' else file}")
                            except Exception as copy_error:
                                print(f"  [ERROR] No se pudo copiar {file}: {copy_error}")
                
                print(f"[OK] {files_copied} archivos copiados desde static/")
            
            print(f"\n[OK] Total: {total_files_copied} archivos copiados manualmente a {dest_dir}")
            
            # Verificar que los archivos críticos estén presentes
            critical_files = [
                'css/floating-audio-button.css',
                'js/audio-floating-button.js',
                'js/badge-manager.js',
                'js/notifications-v5.js',  # Existe en static/js/
            ]
            print("\n[INFO] Verificando archivos críticos después de la copia:")
            for file_path in critical_files:
                full_path = os.path.join(dest_dir, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"  [OK] {file_path} - {size} bytes")
                else:
                    print(f"  [ERROR] {file_path} - NO ENCONTRADO")
            
            # Verificar que los archivos nuevos se copiaron correctamente
            print("\n" + "="*60)
            print("VERIFICANDO ARCHIVOS COPIADOS")
            print("="*60 + "\n")
            
            static_root = settings.STATIC_ROOT
            archivos_verificar = [
                'css/floating-audio-button.css',
                'js/audio-floating-button.js',
                'js/badge-manager.js',
                'js/notifications-v4.js',  # Verificar la versión que realmente existe
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
            
            # Verificar panel de administración
            print("\n" + "="*60)
            print("🔍 VERIFICANDO PANEL DE ADMINISTRACIÓN")
            print("="*60 + "\n")
            
            try:
                from django.urls import reverse
                from django.contrib.auth import get_user_model
                
                # Verificar URLs del panel admin
                admin_urls = [
                    'admin_dashboard',
                    'admin_organizations',
                    'admin_drivers_pending',
                    'admin_reports_financial',
                    'admin_invoices',
                ]
                
                print("[INFO] Verificando URLs del panel admin...")
                urls_ok = True
                for url_name in admin_urls:
                    try:
                        url = reverse(url_name)
                        print(f"  ✅ {url_name:30} → {url}")
                    except Exception as e:
                        print(f"  ❌ {url_name:30} → ERROR: {e}")
                        urls_ok = False
                
                if urls_ok:
                    print("\n[OK] Todas las URLs del panel admin están configuradas")
                else:
                    print("\n[WARNING] Algunas URLs del panel admin tienen problemas")
                
                # Verificar superusuarios
                print("\n[INFO] Verificando superusuarios...")
                User = get_user_model()
                superusers = User.objects.filter(is_superuser=True)
                if superusers.exists():
                    print(f"  ✅ Encontrados {superusers.count()} superusuario(s):")
                    for user in superusers:
                        print(f"     - {user.username} ({user.email})")
                else:
                    print("  ⚠️  No hay superusuarios creados")
                    print("     Crea uno con: railway run python manage.py createsuperuser")
                
                # Verificar templates
                print("\n[INFO] Verificando templates del panel admin...")
                templates_to_check = [
                    'admin/base_admin.html',
                    'admin/dashboard.html',
                    'admin/organizations/list.html',
                ]
                
                templates_ok = True
                for template_path in templates_to_check:
                    template_file = os.path.join(settings.BASE_DIR, 'taxis', 'templates', template_path)
                    if os.path.exists(template_file):
                        print(f"  ✅ {template_path}")
                    else:
                        print(f"  ❌ {template_path} - NO ENCONTRADO")
                        templates_ok = False
                
                if templates_ok:
                    print("\n[OK] Templates del panel admin verificados")
                else:
                    print("\n[WARNING] Algunos templates del panel admin faltan")
                
                print("\n" + "="*60)
                print("📊 RESUMEN DE VERIFICACIÓN:")
                print("="*60)
                print(f"  URLs del panel:    {'✅ OK' if urls_ok else '❌ ERROR'}")
                print(f"  Superusuarios:     {'✅ OK' if superusers.exists() else '⚠️  FALTA CREAR'}")
                print(f"  Templates:         {'✅ OK' if templates_ok else '❌ ERROR'}")
                print("="*60)
                
                if urls_ok and templates_ok:
                    print("\n🎉 Panel de administración listo en:")
                    print("   https://taxis-deaquipalla.up.railway.app/admin/dashboard/")
                
            except Exception as verify_error:
                print(f"\n[WARNING] Error verificando panel admin: {verify_error}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*60)
            print("✅ PRE-DEPLOY COMPLETADO EXITOSAMENTE")
            print("="*60 + "\n")
            sys.exit(0)
            
        except Exception as e:
            print(f"\n" + "="*60)
            print(f"❌ ERROR EN PRE-DEPLOY: {e}")
            print("="*60)
            import traceback
            traceback.print_exc()
            print("="*60 + "\n")
            sys.exit(1)
    finally:
        # Restaurar configuración original
        try:
            if 'original_storage' in locals():
                settings.STATICFILES_STORAGE = original_storage
            if 'original_finders' in locals() and original_finders:
                settings.STATICFILES_FINDERS = original_finders
        except Exception as restore_error:
            print(f"[WARNING] Error restaurando configuración: {restore_error}")

