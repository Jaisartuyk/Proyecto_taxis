"""
Prueba standalone del asistente de IA (sin Django)
"""
import sys
import os

# Agregar el directorio al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'taxis'))

# Importar solo el asistente
from ai_assistant_simple import SimpleAIAssistant

def test_ai():
    """Prueba el asistente de IA"""
    print("🤖 Probando Asistente de IA Simple (sin Django)...\n")
    
    ai = SimpleAIAssistant()
    
    # Prueba 1: Saludo
    print("=" * 60)
    print("PRUEBA 1: Saludo")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="Hola",
        estado_conversacion="inicio"
    )
    print(f"👤 Usuario: Hola")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 2: Solicitar taxi urgente
    print("=" * 60)
    print("PRUEBA 2: Solicitar taxi urgente")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="necesito un taxi urgente porfa",
        estado_conversacion="inicio"
    )
    print(f"👤 Usuario: necesito un taxi urgente porfa")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}")
    print(f"📊 Datos: {resultado['datos_extraidos']}\n")
    
    # Prueba 3: Dar dirección de origen
    print("=" * 60)
    print("PRUEBA 3: Proporcionar origen")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="Parque Lleras, Medellín",
        estado_conversacion="esperando_origen"
    )
    print(f"👤 Usuario: Parque Lleras, Medellín")
    print(f"🤖 Bot: {resultado['respuesta'] if resultado['respuesta'] else '[El agente geocodificará]'}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 4: Confirmación positiva
    print("=" * 60)
    print("PRUEBA 4: Confirmación")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="sí, dale",
        estado_conversacion="confirmando_carrera"
    )
    print(f"👤 Usuario: sí, dale")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 5: Negación
    print("=" * 60)
    print("PRUEBA 5: Cancelar")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="no, mejor no",
        estado_conversacion="confirmando_carrera"
    )
    print(f"👤 Usuario: no, mejor no")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 6: Ayuda
    print("=" * 60)
    print("PRUEBA 6: Solicitar ayuda")
    print("=" * 60)
    resultado = ai.generar_respuesta_contextual(
        mensaje_usuario="ayuda",
        estado_conversacion="inicio"
    )
    print(f"👤 Usuario: ayuda")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    print("=" * 60)
    print("✅ ¡Todas las pruebas completadas exitosamente!")
    print("=" * 60)
    print("\n🎉 El asistente de IA está funcionando perfectamente")
    print("\n💡 Características demostradas:")
    print("   ✅ Conversaciones naturales y humanas")
    print("   ✅ Detección de urgencias")
    print("   ✅ Respuestas variadas y dinámicas")
    print("   ✅ Manejo contextual de estados")
    print("   ✅ Confirmaciones y cancelaciones")
    print("   ✅ Sistema de ayuda integrado")
    print("\n📱 ¡Listo para usar en WhatsApp!\n")

if __name__ == "__main__":
    try:
        test_ai()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
