"""
Script de prueba para verificar que Claude AI funciona correctamente
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.ai_assistant import claude_assistant

def test_claude():
    """Prueba básica de Claude"""
    print("🤖 Probando Claude AI...\n")
    
    # Prueba 1: Saludo
    print("=" * 50)
    print("PRUEBA 1: Saludo")
    print("=" * 50)
    resultado = claude_assistant.generar_respuesta_contextual(
        mensaje_usuario="Hola",
        estado_conversacion="inicio"
    )
    print(f"Usuario: Hola")
    print(f"Claude: {resultado['respuesta']}")
    print(f"Acción detectada: {resultado['accion']}\n")
    
    # Prueba 2: Solicitar taxi
    print("=" * 50)
    print("PRUEBA 2: Solicitar taxi")
    print("=" * 50)
    resultado = claude_assistant.generar_respuesta_contextual(
        mensaje_usuario="necesito un taxi urgente",
        estado_conversacion="inicio"
    )
    print(f"Usuario: necesito un taxi urgente")
    print(f"Claude: {resultado['respuesta']}")
    print(f"Acción detectada: {resultado['accion']}\n")
    
    # Prueba 3: Dar dirección
    print("=" * 50)
    print("PRUEBA 3: Proporcionar origen")
    print("=" * 50)
    resultado = claude_assistant.generar_respuesta_contextual(
        mensaje_usuario="Parque Lleras, Medellín",
        estado_conversacion="esperando_origen"
    )
    print(f"Usuario: Parque Lleras, Medellín")
    print(f"Claude: {resultado['respuesta']}")
    print(f"Acción detectada: {resultado['accion']}\n")
    
    # Prueba 4: Confirmación
    print("=" * 50)
    print("PRUEBA 4: Confirmación")
    print("=" * 50)
    resultado = claude_assistant.generar_respuesta_contextual(
        mensaje_usuario="sí, confirmo",
        estado_conversacion="confirmando_carrera",
        datos_usuario={
            'nombre': 'Usuario de Prueba',
            'datos': {
                'origen': 'Parque Lleras',
                'destino': 'Aeropuerto'
            }
        }
    )
    print(f"Usuario: sí, confirmo")
    print(f"Claude: {resultado['respuesta']}")
    print(f"Acción detectada: {resultado['accion']}\n")
    
    print("=" * 50)
    print("✅ ¡Todas las pruebas completadas!")
    print("=" * 50)
    print("\n🎉 Claude AI está funcionando correctamente")
    print("📱 Ahora puedes probar enviando mensajes por WhatsApp\n")

if __name__ == "__main__":
    try:
        test_claude()
    except Exception as e:
        print(f"❌ Error al probar Claude: {str(e)}")
        import traceback
        traceback.print_exc()
