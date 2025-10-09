"""
Test simple de Claude sin Django
"""
import anthropic
import os

# Configurar API key desde variable de entorno
api_key = os.environ.get('CLAUDE_API_KEY', '')

print("🤖 Probando Claude AI...\n")
print(f"API Key: {api_key[:20]}...{api_key[-10:]}\n")

try:
    client = anthropic.Anthropic(api_key=api_key)
    
    # Probar con Claude 3 Haiku
    print("Probando Claude 3 Haiku...")
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Di 'Hola' en español"}
        ]
    )
    
    print(f"✅ ¡Funciona! Respuesta: {response.content[0].text}\n")
    
except Exception as e:
    print(f"❌ Error: {str(e)}\n")
    
    # Intentar con otros modelos
    modelos = [
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]
    
    for modelo in modelos:
        try:
            print(f"Probando {modelo}...")
            response = client.messages.create(
                model=modelo,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Di 'Hola'"}
                ]
            )
            print(f"✅ ¡{modelo} funciona! Respuesta: {response.content[0].text}\n")
            break
        except Exception as e2:
            print(f"❌ {modelo} no funciona: {str(e2)}\n")
