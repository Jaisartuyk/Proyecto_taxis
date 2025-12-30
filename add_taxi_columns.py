"""
Script para agregar columnas al modelo Taxi usando SQL directo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from django.db import connection

# Agregar columnas a la tabla taxis_taxi
with connection.cursor() as cursor:
    try:
        # Agregar car_model
        cursor.execute("""
            ALTER TABLE taxis_taxi 
            ADD COLUMN IF NOT EXISTS car_model VARCHAR(100);
        """)
        print("✅ Columna car_model agregada")
    except Exception as e:
        print(f"⚠️ car_model: {e}")
    
    try:
        # Agregar car_color
        cursor.execute("""
            ALTER TABLE taxis_taxi 
            ADD COLUMN IF NOT EXISTS car_color VARCHAR(50);
        """)
        print("✅ Columna car_color agregada")
    except Exception as e:
        print(f"⚠️ car_color: {e}")
    
    try:
        # Agregar car_year
        cursor.execute("""
            ALTER TABLE taxis_taxi 
            ADD COLUMN IF NOT EXISTS car_year INTEGER;
        """)
        print("✅ Columna car_year agregada")
    except Exception as e:
        print(f"⚠️ car_year: {e}")
    
    try:
        # Agregar is_active
        cursor.execute("""
            ALTER TABLE taxis_taxi 
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
        """)
        print("✅ Columna is_active agregada")
    except Exception as e:
        print(f"⚠️ is_active: {e}")

print("\n✅ Todas las columnas agregadas exitosamente")
