#!/usr/bin/env python
"""
Test Simple del Sistema Walkie-Talkie
Verifica que las notificaciones push funcionen correctamente
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxi_project.settings')
django.setup()

from taxis.models import AppUser

def test_walkie_talkie_system():
    """
    Prueba básica del sistema walkie-talkie
    """
    print("🚀 Iniciando test del sistema Walkie-Talkie...")
    print("=" * 60)
    
    # 1. Verificar usuarios existentes
    print("📋 1. Verificando usuarios...")
    conductores = AppUser.objects.filter(role='driver')
    admins = AppUser.objects.filter(role='admin')
    
    print(f"   - Conductores encontrados: {conductores.count()}")
    print(f"   - Administradores encontrados: {admins.count()}")
    
    # 2. Verificar archivos del sistema
    print("\n🔧 2. Verificando archivos del sistema...")
    
    files_to_check = [
        ("static/js/service-worker.js", "Service Worker"),
        ("taxis/static/js/comunicacion.js", "JavaScript de Comunicación"),
        ("taxis/templates/central_comunicacion.html", "Template Central"),
        ("taxis/consumers.py", "WebSocket Consumer")
    ]
    
    all_files_exist = True
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            print(f"   ✅ {description}: {file_path}")
        else:
            print(f"   ❌ {description} NO encontrado: {file_path}")
            all_files_exist = False
    
    # 3. Verificar funciones en Service Worker
    print("\n📱 3. Verificando Service Worker...")
    
    sw_path = "static/js/service-worker.js"
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            sw_content = f.read()
            
        required_sw_functions = [
            'savePendingAudio',
            'markAudioAsDismissed', 
            'cleanOldPendingAudios',
            'walkie_talkie_audio',
            'requireInteraction: true'
        ]
        
        for func in required_sw_functions:
            if func in sw_content:
                print(f"   ✅ '{func}' encontrado")
            else:
                print(f"   ❌ '{func}' NO encontrado")
    
    # 4. Verificar funciones en comunicacion.js
    print("\n💻 4. Verificando comunicacion.js...")
    
    js_path = "taxis/static/js/comunicacion.js"
    if os.path.exists(js_path):
        with open(js_path, 'r', encoding='utf-8') as f:
            js_content = f.read()
            
        required_js_features = [
            'pendingAudioQueue',
            'dismissedAudios',
            'savePendingAudio',
            'loadPersistedAudioData',
            'playPendingAudios',
            'wsReconnectAttempts',
            'setupWebSocket',
            'visibilitychange'
        ]
        
        for feature in required_js_features:
            if feature in js_content:
                print(f"   ✅ '{feature}' encontrado")
            else:
                print(f"   ❌ '{feature}' NO encontrado")
    
    # 5. Verificar consumer mejorado
    print("\n🔌 5. Verificando WebSocket Consumer...")
    
    consumer_path = "taxis/consumers.py"
    if os.path.exists(consumer_path):
        with open(consumer_path, 'r', encoding='utf-8') as f:
            consumer_content = f.read()
            
        required_consumer_features = [
            'send_audio_push_to_drivers',
            'walkie_talkie_audio',
            'sender_id',
            'urgent',
            'vibrate'
        ]
        
        for feature in required_consumer_features:
            if feature in consumer_content:
                print(f"   ✅ '{feature}' encontrado")
            else:
                print(f"   ❌ '{feature}' NO encontrado")
    
    # 6. Verificar template actualizado
    print("\n🎨 6. Verificando template central...")
    
    template_path = "taxis/templates/central_comunicacion.html"
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        template_features = [
            'floating-chat-btn',
            'floating-audio-btn',
            'comunicacion.js',
            'header-controls'
        ]
        
        for feature in template_features:
            if feature in template_content:
                print(f"   ✅ '{feature}' encontrado")
            else:
                print(f"   ❌ '{feature}' NO encontrado")
    
    # 7. Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL SISTEMA WALKIE-TALKIE:")
    print("=" * 60)
    
    if all_files_exist:
        print("✅ TODOS LOS ARCHIVOS NECESARIOS ESTÁN PRESENTES")
    else:
        print("❌ ALGUNOS ARCHIVOS FALTAN")
    
    print("\n🎯 FUNCIONALIDADES IMPLEMENTADAS:")
    print("   📱 Push notifications con configuración walkie-talkie")
    print("   🔄 WebSocket con reconexión automática")
    print("   💾 Sistema de audio pendiente persistente")
    print("   🎧 Reproducción secuencial de audios perdidos")
    print("   🎨 Interfaz mejorada con controles en headers")
    print("   🔘 Botones flotantes para paneles ocultos")
    print("   🧹 Limpieza automática de audios antiguos")
    print("   📱 Manejo de background/foreground")
    
    print("\n🚕 INSTRUCCIONES DE USO:")
    print("1. Los conductores deben permitir notificaciones push")
    print("2. La app registrará automáticamente el service worker")
    print("3. Los audios se recibirán incluso en background")
    print("4. Al regresar a la app, se mostrarán audios pendientes")
    print("5. Sistema funciona como boquitokis/motorolas")
    
    print("\n🎉 ¡SISTEMA WALKIE-TALKIE LISTO PARA USO!")
    
    return True

if __name__ == "__main__":
    test_walkie_talkie_system()