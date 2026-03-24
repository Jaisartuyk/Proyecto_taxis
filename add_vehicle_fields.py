"""
Script para agregar campos de vehículo a la tabla taxis_appuser
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings_railway')
django.setup()

from django.db import connection

def add_vehicle_fields():
    """Agregar campos de vehículo si no existen"""
    with connection.cursor() as cursor:
        # Lista de campos a agregar
        fields_to_add = [
            ("vehicle_brand", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_brand varchar(50) NULL;"),
            ("vehicle_color", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_color varchar(30) NULL;"),
            ("vehicle_model", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_model varchar(50) NULL;"),
            ("vehicle_photo_front", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_photo_front varchar(255) NULL;"),
            ("vehicle_photo_interior", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_photo_interior varchar(255) NULL;"),
            ("vehicle_photo_rear", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_photo_rear varchar(255) NULL;"),
            ("vehicle_photo_side", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_photo_side varchar(255) NULL;"),
            ("vehicle_plate", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_plate varchar(20) NULL;"),
            ("vehicle_year", "ALTER TABLE taxis_appuser ADD COLUMN IF NOT EXISTS vehicle_year integer NULL;"),
        ]
        
        print("🚗 Agregando campos de vehículo a taxis_appuser...")
        
        for field_name, sql in fields_to_add:
            try:
                cursor.execute(sql)
                print(f"✅ Campo '{field_name}' agregado correctamente")
            except Exception as e:
                print(f"⚠️ Error agregando campo '{field_name}': {e}")
        
        print("\n✅ Proceso completado!")
        print("Ahora puedes marcar la migración como aplicada con:")
        print("python manage.py migrate taxis 0025 --fake")

if __name__ == '__main__':
    add_vehicle_fields()
