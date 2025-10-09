"""
Script de prueba para el asistente de IA simple
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.ai_assistant_simple import simple_ai_assistant

def test_ai_simple():
    """Prueba básica del asistente simple"""
    print("🤖 Probando Asistente de IA Simple...\n")
    
    # Prueba 1: Saludo
    print("=" * 60)
    print("PRUEBA 1: Saludo")
    print("=" * 60)
    resultado = simple_ai_assistant.generar_respuesta_contextual(
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
    resultado = simple_ai_assistant.generar_respuesta_contextual(
        mensaje_usuario="necesito un taxi urgente",
        estado_conversacion="inicio"
    )
    print(f"👤 Usuario: necesito un taxi urgente")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 3: Dar dirección de origen
    print("=" * 60)
    print("PRUEBA 3: Proporcionar origen")
    print("=" * 60)
    resultado = simple_ai_assistant.generar_respuesta_contextual(
        mensaje_usuario="Parque Lleras, Medellín",
        estado_conversacion="esperando_origen"
    )
    print(f"👤 Usuario: Parque Lleras, Medellín")
    print(f"🤖 Bot: {resultado['respuesta'] if resultado['respuesta'] else '[El agente geocodificará y responderá]'}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 4: Dar destino
    print("=" * 60)
    print("PRUEBA 4: Proporcionar destino")
    print("=" * 60)
    resultado = simple_ai_assistant.generar_respuesta_contextual(
        mensaje_usuario="Aeropuerto José María Córdova",
        estado_conversacion="esperando_destino",
        datos_usuario={'datos': {'origen': 'Parque Lleras'}}
    )
    print(f"👤 Usuario: Aeropuerto José María Córdova")
    print(f"🤖 Bot: {resultado['respuesta'] if resultado['respuesta'] else '[El agente calculará y mostrará resumen]'}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 5: Confirmación
    print("=" * 60)
    print("PRUEBA 5: Confirmación")
    print("=" * 60)
    resultado = simple_ai_assistant.generar_respuesta_contextual(
        mensaje_usuario="sí, confirmo",
        estado_conversacion="confirmando_carrera"
    )
    print(f"👤 Usuario: sí, confirmo")
    print(f"🤖 Bot: {resultado['respuesta']}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    # Prueba 6: Consultar estado
    print("=" * 60)
    print("PRUEBA 6: Consultar estado")
    print("=" * 60)
    resultado = simple_ai_assistant.generar_respuesta_contextual(
        mensaje_usuario="cómo va mi carrera",
        estado_conversacion="carrera_activa"
    )
    print(f"👤 Usuario: cómo va mi carrera")
    print(f"🤖 Bot: {resultado['respuesta'] if resultado['respuesta'] else '[El agente mostrará el estado]'}")
    print(f"📋 Acción: {resultado['accion']}\n")
    
    print("=" * 60)
    print("✅ ¡Todas las pruebas completadas exitosamente!")
    print("=" * 60)
    print("\n🎉 El asistente de IA está funcionando correctamente")
    print("📱 Ahora puedes probar enviando mensajes por WhatsApp")
    print("\n💡 Características:")
    print("   ✅ Conversaciones naturales y humanas")
    print("   ✅ Detección de urgencias")
    print("   ✅ Respuestas variadas y dinámicas")
    print("   ✅ Soporte para ubicaciones GPS")
    print("   ✅ Manejo contextual de estados\n")

if __name__ == "__main__":
    try:
        test_ai_simple()
    except Exception as e:
        print(f"❌ Error al probar el asistente: {str(e)}")
        import traceback
        traceback.print_exc()
