"""
Script para generar iconos PWA desde el logo existente
Requiere: pip install Pillow
"""

from PIL import Image
import os

def generate_pwa_icons():
    """Genera los iconos necesarios para la PWA desde el logo existente"""
    
    # Ruta del logo original
    logo_path = 'taxis/static/imagenes/logo1.png'
    output_dir = 'taxis/static/imagenes/'
    
    # Verificar que el logo existe
    if not os.path.exists(logo_path):
        print(f"❌ Error: No se encontró el logo en {logo_path}")
        return
    
    try:
        # Abrir la imagen original
        img = Image.open(logo_path)
        print(f"✅ Logo cargado: {logo_path}")
        print(f"   Tamaño original: {img.size}")
        
        # Convertir a RGBA si no lo está
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Tamaños requeridos para PWA
        sizes = [
            (192, 192, 'icon-192x192.png'),
            (512, 512, 'icon-512x512.png'),
            (96, 96, 'icon-96x96.png'),
            (144, 144, 'icon-144x144.png'),
            (256, 256, 'icon-256x256.png'),
        ]
        
        print("\n📦 Generando iconos...")
        
        for width, height, filename in sizes:
            # Redimensionar manteniendo la proporción
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            # Guardar el icono
            output_path = os.path.join(output_dir, filename)
            resized.save(output_path, 'PNG', optimize=True)
            
            print(f"   ✓ {filename} ({width}x{height})")
        
        print("\n✅ ¡Todos los iconos generados exitosamente!")
        print(f"📁 Ubicación: {output_dir}")
        
        # Información adicional
        print("\n📋 Próximos pasos:")
        print("1. Verifica que los iconos se vean bien")
        print("2. Opcionalmente, crea un screenshot de la app (540x720)")
        print("3. Actualiza el manifest.json si es necesario")
        print("4. Prueba la instalación de la PWA")
        
    except Exception as e:
        print(f"❌ Error al generar iconos: {str(e)}")
        print("\nAsegúrate de tener Pillow instalado:")
        print("   pip install Pillow")

if __name__ == '__main__':
    print("🎨 Generador de Iconos PWA - De Aquí Pa'llá")
    print("=" * 50)
    generate_pwa_icons()
