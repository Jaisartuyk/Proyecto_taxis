#!/usr/bin/env python
"""
Script de diagnóstico para verificar que todo esté configurado correctamente
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

print("=" * 60)
print("🔍 DIAGNÓSTICO DEL SISTEMA")
print("=" * 60)

# 1. Verificar variables de entorno
print("\n📋 Variables de entorno:")
print(f"  DATABASE_URL: {'✅ Configurada' if os.getenv('DATABASE_URL') else '❌ Falta'}")
print(f"  REDIS_URL: {'✅ Configurada' if os.getenv('REDIS_URL') else '❌ Falta'}")
print(f"  CLAUDE_API_KEY: {'✅ Configurada' if os.getenv('CLAUDE_API_KEY') else '❌ Falta'}")
print(f"  GOOGLE_API_KEY: {'✅ Configurada' if os.getenv('GOOGLE_API_KEY') else '❌ Falta'}")

# 2. Verificar imports críticos
print("\n📦 Imports críticos:")
try:
    from taxis.ai_assistant_claude import claude_ai_assistant
    print("  ✅ ai_assistant_claude")
    print(f"     - Cliente: {'✅ Activo' if claude_ai_assistant.client else '❌ No configurado'}")
    print(f"     - Modelo: {claude_ai_assistant.model}")
except Exception as e:
    print(f"  ❌ ai_assistant_claude: {e}")

try:
    from taxis.whatsapp_agent_ai import whatsapp_agent_ai
    print("  ✅ whatsapp_agent_ai")
except Exception as e:
    print(f"  ❌ whatsapp_agent_ai: {e}")

try:
    from taxis.views import crear_carrera_desde_whatsapp
    print("  ✅ crear_carrera_desde_whatsapp")
except Exception as e:
    print(f"  ❌ crear_carrera_desde_whatsapp: {e}")

# 3. Verificar base de datos
print("\n💾 Base de datos:")
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("  ✅ Conexión exitosa")
    
    from taxis.models import WhatsAppConversation, WhatsAppMessage, WhatsAppStats
    print(f"  ✅ Modelos WhatsApp importados")
    
    # Verificar tablas
    from django.db import connection
    tables = connection.introspection.table_names()
    if 'taxis_whatsappconversation' in tables:
        print("  ✅ Tabla taxis_whatsappconversation existe")
    else:
        print("  ❌ Tabla taxis_whatsappconversation NO existe")
        
except Exception as e:
    print(f"  ❌ Error de BD: {e}")

# 4. Verificar Redis
print("\n🔴 Redis:")
try:
    import redis
    redis_url = os.getenv('REDIS_URL')
    if redis_url:
        r = redis.from_url(redis_url)
        r.ping()
        print("  ✅ Conexión exitosa")
    else:
        print("  ⚠️ REDIS_URL no configurada")
except Exception as e:
    print(f"  ❌ Error: {e}")

# 5. Verificar ASGI
print("\n🌐 ASGI:")
try:
    from taxi_project.asgi import application
    print("  ✅ ASGI application importada")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ DIAGNÓSTICO COMPLETADO")
print("=" * 60)
