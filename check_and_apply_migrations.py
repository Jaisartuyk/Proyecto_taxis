#!/usr/bin/env python
"""
Script para verificar y aplicar migraciones en Railway
Ejecutar desde Railway Console: python check_and_apply_migrations.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
django.setup()

from django.db import connection
from django.core.management import call_command
from taxis.models import ChatMessage

print("\n" + "="*70)
print("VERIFICACIÓN Y APLICACIÓN DE MIGRACIONES")
print("="*70 + "\n")

# 1. Verificar campos requeridos en la BD
print("📋 Paso 1: Verificando columnas en la base de datos...")
try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns 
            WHERE table_name = 'taxis_chatmessage'
            AND column_name IN ('message_type', 'media_url', 'thumbnail_url', 'metadata')
            ORDER BY column_name
        """)
        db_columns = {row[0]: row[1] for row in cursor.fetchall()}
    
    required_fields = ['message_type', 'media_url', 'thumbnail_url', 'metadata']
    missing_fields = [f for f in required_fields if f not in db_columns]
    
    if missing_fields:
        print(f"❌ Faltan {len(missing_fields)} campos en la base de datos:")
        for field in missing_fields:
            print(f"   - {field}")
        print("\n📦 Aplicando migraciones...")
        print("="*70 + "\n")
        
        # Aplicar migraciones
        try:
            call_command('migrate', '--noinput', verbosity=2)
            print("\n✅ Migraciones aplicadas")
            
            # Verificar nuevamente
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'taxis_chatmessage'
                    AND column_name IN ('message_type', 'media_url', 'thumbnail_url', 'metadata')
                    ORDER BY column_name
                """)
                db_columns = {row[0]: row[1] for row in cursor.fetchall()}
            
            missing_fields = [f for f in required_fields if f not in db_columns]
            if missing_fields:
                print(f"\n❌ ERROR: Aún faltan campos después de aplicar migraciones:")
                for field in missing_fields:
                    print(f"   - {field}")
                print("\n💡 Posibles soluciones:")
                print("   1. Verifica que las migraciones existan: python manage.py showmigrations taxis")
                print("   2. Crea las migraciones: python manage.py makemigrations")
                print("   3. Aplica manualmente: python manage.py migrate")
                sys.exit(1)
            else:
                print("\n✅ Todos los campos están presentes después de aplicar migraciones")
        except Exception as e:
            print(f"\n❌ Error aplicando migraciones: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("✅ Todos los campos requeridos están presentes en la base de datos")
        for field, dtype in sorted(db_columns.items()):
            print(f"   ✅ {field}: {dtype}")
    
    # 2. Verificar que el modelo tenga los campos
    print("\n📋 Paso 2: Verificando campos en el modelo...")
    model_fields = [f.name for f in ChatMessage._meta.get_fields()]
    model_has_all = all(f in model_fields for f in required_fields)
    
    if model_has_all:
        print("✅ El modelo tiene todos los campos requeridos")
    else:
        missing_in_model = [f for f in required_fields if f not in model_fields]
        print(f"❌ Faltan campos en el modelo: {', '.join(missing_in_model)}")
        print("💡 Esto indica un problema con el código, no con las migraciones")
        sys.exit(1)
    
    # 3. Resumen final
    print("\n" + "="*70)
    print("✅ VERIFICACIÓN COMPLETA")
    print("="*70)
    print("\n✅ Base de datos: Todos los campos presentes")
    print("✅ Modelo Django: Todos los campos presentes")
    print("\n🎉 Las migraciones están correctamente aplicadas")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ Error durante la verificación: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)



