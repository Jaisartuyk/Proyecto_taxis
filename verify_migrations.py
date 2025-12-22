#!/usr/bin/env python
"""
Script para verificar que las migraciones se aplicaron correctamente en Railway
Ejecutar: railway run python verify_migrations.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
django.setup()

from django.db import connection
from taxis.models import ChatMessage

print("\n" + "="*60)
print("VERIFICACIÓN DE MIGRACIONES - CHAT CON MEDIA")
print("="*60 + "\n")

# Verificar campos en el modelo
print("📋 Verificando campos en el modelo ChatMessage...")
fields = [f.name for f in ChatMessage._meta.get_fields()]
print(f"   Total de campos: {len(fields)}")
print(f"   Campos: {', '.join(sorted(fields))}\n")

# Verificar campos en la base de datos
print("📋 Verificando columnas en la base de datos...")
try:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'taxis_chatmessage'
            ORDER BY column_name
        """)
        db_columns = cursor.fetchall()
    
    print(f"   Total de columnas: {len(db_columns)}")
    column_names = [col[0] for col in db_columns]
    print(f"   Columnas: {', '.join(sorted(column_names))}\n")
    
    # Verificar campos nuevos requeridos
    required_fields = {
        'message_type': 'character varying',
        'media_url': 'character varying',
        'thumbnail_url': 'character varying',
        'metadata': 'jsonb'
    }
    
    print("="*60)
    print("VERIFICACIÓN DE CAMPOS NUEVOS")
    print("="*60 + "\n")
    
    all_ok = True
    for field_name, expected_type in required_fields.items():
        # Buscar en la base de datos
        found = False
        actual_type = None
        for col in db_columns:
            if col[0] == field_name:
                found = True
                actual_type = col[1]
                break
        
        # Verificar en el modelo
        in_model = field_name in fields
        
        status = "✅" if (found and in_model) else "❌"
        print(f"{status} {field_name}:")
        print(f"   En modelo: {'✅' if in_model else '❌'}")
        print(f"   En BD: {'✅' if found else '❌'}")
        if found:
            print(f"   Tipo BD: {actual_type}")
            if actual_type != expected_type:
                print(f"   ⚠️ Tipo esperado: {expected_type}")
        print()
        
        if not (found and in_model):
            all_ok = False
    
    print("="*60)
    if all_ok:
        print("✅ TODAS LAS MIGRACIONES SE APLICARON CORRECTAMENTE")
        print("="*60)
        sys.exit(0)
    else:
        print("❌ ALGUNAS MIGRACIONES NO SE APLICARON")
        print("="*60)
        print("\n💡 Solución:")
        print("   Ejecuta: railway run python manage.py migrate")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error verificando migraciones: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

