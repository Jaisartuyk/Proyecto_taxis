# 🤖 Integración de Claude AI - Conversaciones Naturales

## 🌟 Nueva Funcionalidad

Hemos integrado **Claude 3.5 Sonnet** de Anthropic para hacer las conversaciones por WhatsApp mucho más naturales, humanas y fluidas.

---

## ✨ Características de la IA

### 🗣️ Conversaciones Naturales
- ✅ Respuestas humanas y empáticas
- ✅ Comprensión de contexto
- ✅ Lenguaje coloquial colombiano
- ✅ Uso apropiado de emojis
- ✅ Manejo de ambigüedades

### 📍 Soporte para Ubicaciones GPS
- ✅ Recepción de ubicaciones en tiempo real desde WhatsApp
- ✅ Geocodificación inversa automática
- ✅ Visualización en la central en tiempo real
- ✅ Tracking de clientes durante la carrera

### 🧠 Inteligencia Contextual
- ✅ Recuerda el contexto de la conversación
- ✅ Detecta intenciones automáticamente
- ✅ Extrae datos de mensajes naturales
- ✅ Maneja múltiples flujos de conversación

---

## 🔧 Configuración

### 1. Instalar Dependencias

```bash
pip install anthropic==0.39.0
```

O instalar todas las dependencias:

```bash
pip install -r requirements.txt
```

### 2. API Key de Claude

Para usar Claude, necesitas configurar tu API Key como variable de entorno:

**Windows (PowerShell):**
```powershell
$env:CLAUDE_API_KEY="tu-api-key-de-anthropic"
```

**Linux/Mac:**
```bash
export CLAUDE_API_KEY="tu-api-key-de-anthropic"
```

**O crear un archivo `.env`:**
```
CLAUDE_API_KEY=tu-api-key-de-anthropic
```

**Nota**: Por seguridad, NUNCA incluyas API keys directamente en el código.

### 3. Modelo Utilizado

Estamos usando **Claude 3.5 Sonnet** (`claude-3-5-sonnet-20241022`), el modelo más reciente y avanzado de Anthropic.

---

## 💬 Ejemplos de Conversaciones Naturales

### Ejemplo 1: Solicitud Casual

```
👤 Usuario: Hola, necesito un taxi
🤖 Bot: ¡Hola! 👋 Claro que sí, con gusto te ayudo. ¿Desde dónde te vamos a recoger? Puedes escribir la dirección o enviarme tu ubicación 📍

👤 Usuario: Estoy en el parque lleras
🤖 Bot: Perfecto, te vamos a recoger en Parque Lleras, Medellín ✅
       ¿Y a dónde te llevamos?

👤 Usuario: al aeropuerto porfa
🤖 Bot: ¡Listo! 🎉
       
       📍 Origen: Parque Lleras, Medellín
       🎯 Destino: Aeropuerto José María Córdova
       📏 Distancia: 28.5 km
       💰 Tarifa estimada: $76,250 COP
       🚕 Conductor: Juan Pérez
       
       ¿Confirmas esta carrera? Responde SÍ para confirmar 😊
```

### Ejemplo 2: Con Ubicación GPS

```
👤 Usuario: [Envía ubicación GPS]
🤖 Bot: ✅ Perfecto, te vamos a recoger en:
       📍 Calle 10 #43-50, El Poblado, Medellín
       
       Ahora, ¿a dónde te llevamos? Puedes escribir la dirección o enviar otra ubicación 🗺️

👤 Usuario: [Envía ubicación de destino]
🤖 Bot: ¡Excelente! 🎉
       
       📍 Origen: Calle 10 #43-50, El Poblado
       🎯 Destino: Centro Comercial Santa Fe
       📏 Distancia: 5.2 km
       💰 Tarifa estimada: $18,000 COP
       ⏱️ Tiempo de llegada: 5-10 minutos
       🚕 Conductor: María González
       
       ¿Confirmas? Responde SÍ 😊
```

### Ejemplo 3: Conversación Natural

```
👤 Usuario: Buenas, me podrías ayudar?
🤖 Bot: ¡Claro que sí! 😊 Estoy aquí para ayudarte. ¿Necesitas solicitar un taxi?

👤 Usuario: si porfa, es urgente
🤖 Bot: Entiendo que es urgente, vamos rápido entonces 🚀
       ¿Desde dónde te recogemos?

👤 Usuario: calle 50 con carrera 25
🤖 Bot: Perfecto, Calle 50 con Carrera 25 ✅
       ¿Y a dónde vas?

👤 Usuario: necesito ir a la clínica las vegas
🤖 Bot: Entendido, te llevamos a Clínica Las Vegas 🏥
       
       Aquí está el resumen:
       📍 Origen: Calle 50 #25, Medellín
       🎯 Destino: Clínica Las Vegas
       📏 Distancia: 3.8 km
       💰 Tarifa: $14,500 COP
       🚕 Conductor: Carlos Ramírez
       
       ¿Confirmamos? Responde SÍ
```

---

## 📍 Ubicaciones en Tiempo Real

### Cómo Funciona

1. **Cliente envía ubicación GPS desde WhatsApp**
   - El usuario comparte su ubicación actual
   - El sistema la recibe automáticamente

2. **Geocodificación Inversa**
   - Convierte coordenadas en dirección legible
   - Muestra la dirección al usuario para confirmar

3. **Visualización en Central**
   - La ubicación se envía en tiempo real a la central
   - Los operadores pueden ver la ubicación en el mapa
   - Se actualiza continuamente durante la carrera

4. **Tracking Durante la Carrera**
   - El cliente puede enviar su ubicación actualizada
   - La central ve el movimiento en tiempo real
   - Útil para coordinar con el conductor

### Formato de Ubicación

WhatsApp envía las ubicaciones en este formato:

```json
{
  "locationMessage": {
    "degreesLatitude": 6.2442,
    "degreesLongitude": -75.5812
  }
}
```

El sistema lo procesa automáticamente y:
- Obtiene la dirección
- Guarda las coordenadas
- Envía a la central para visualización
- Continúa con el flujo de solicitud

---

## 🎯 Acciones que Claude Detecta

Claude puede detectar automáticamente estas intenciones:

| Intención | Ejemplos de Mensajes |
|-----------|---------------------|
| **Solicitar Carrera** | "necesito un taxi", "quiero pedir una carrera", "me ayudas con un taxi" |
| **Consultar Estado** | "cómo va mi carrera", "dónde está el taxi", "cuánto falta" |
| **Cancelar** | "quiero cancelar", "ya no necesito el taxi", "cancela la carrera" |
| **Ver Carreras** | "mis carreras", "qué carreras tengo activas", "muéstrame mis viajes" |
| **Ayuda** | "ayuda", "qué puedes hacer", "cómo funciona" |
| **Confirmación** | "sí", "ok", "dale", "confirmo", "listo" |
| **Negación** | "no", "cancelar", "mejor no" |

---

## 🔄 Flujo de Conversación

```
┌─────────────────┐
│  Usuario saluda │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Claude detecta intención│
│ y responde naturalmente │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────┐
│ ¿Solicitar carrera?  │
└────┬─────────────────┘
     │ Sí
     ▼
┌──────────────────────┐
│ Solicitar origen     │
│ (texto o GPS)        │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Geocodificar origen  │
│ Confirmar con usuario│
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Solicitar destino    │
│ (texto o GPS)        │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Calcular distancia   │
│ y tarifa estimada    │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Buscar taxista       │
│ más cercano          │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Mostrar resumen      │
│ Solicitar confirmación│
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Crear carrera        │
│ Notificar conductor  │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────┐
│ Carrera activa       │
│ Tracking en tiempo   │
│ real disponible      │
└──────────────────────┘
```

---

## 🎨 Personalidad del Bot

Claude está configurado con esta personalidad:

- **Amigable y Cálido**: Saluda con entusiasmo, usa emojis
- **Profesional**: Proporciona información clara y precisa
- **Empático**: Entiende urgencias y situaciones especiales
- **Colombiano**: Usa expresiones locales cuando es apropiado
- **Eficiente**: Va al grano pero sin ser brusco
- **Paciente**: Maneja confusiones y pide aclaraciones amablemente

---

## 🔍 Monitoreo y Logs

### Logs de Claude

```bash
# Logs de conversación
📤 Enviando mensaje a +573001234567: ¡Hola! 👋 Claro que sí...
✅ Mensaje enviado exitosamente
💬 Procesando mensaje de +573001234567: necesito un taxi
Claude respondió: ¡Hola! 👋 Claro que sí, con gusto...
✅ Mensaje procesado. Acción: solicitar_origen
```

### Logs de Ubicaciones GPS

```bash
📍 Ubicación GPS recibida de +573001234567: 6.2442, -75.5812
📍 Ubicación enviada a central: +573001234567 - origen
✅ Mensaje procesado exitosamente
```

---

## 🚀 Ventajas de Claude AI

### vs Sistema de Comandos Tradicional

| Característica | Comandos | Claude AI |
|----------------|----------|-----------|
| **Naturalidad** | "Escribe MENU" | "Hola, ¿qué necesitas?" |
| **Flexibilidad** | Comandos exactos | Entiende variaciones |
| **Contexto** | Sin memoria | Recuerda conversación |
| **Errores** | "Comando no válido" | "¿Podrías aclarar?" |
| **Experiencia** | Robótica | Humana |

### Beneficios

1. **Mejor UX**: Los usuarios hablan naturalmente
2. **Menos Fricción**: No necesitan aprender comandos
3. **Mayor Conversión**: Más usuarios completan solicitudes
4. **Menos Soporte**: Claude maneja dudas automáticamente
5. **Escalable**: Claude aprende de cada conversación

---

## 💡 Tips para Mejores Resultados

### Para Usuarios

1. **Sé Natural**: Habla como lo harías con una persona
2. **Ubicaciones GPS**: Úsalas para mayor precisión
3. **Confirma**: Revisa el resumen antes de confirmar
4. **Sé Específico**: Direcciones completas funcionan mejor

### Para Operadores

1. **Monitorea Logs**: Revisa conversaciones para mejorar
2. **Feedback**: Reporta respuestas que se pueden mejorar
3. **Ubicaciones**: Usa el tracking para coordinar mejor
4. **Personalización**: Ajusta la personalidad según necesidad

---

## 🔒 Seguridad y Privacidad

- ✅ API Key segura (mover a .env en producción)
- ✅ Conversaciones no se almacenan en Anthropic
- ✅ Datos de ubicación encriptados en tránsito
- ✅ Cumplimiento con GDPR y regulaciones locales

---

## 📊 Métricas Recomendadas

Monitorea estas métricas para optimizar:

1. **Tasa de Conversión**: % de conversaciones que resultan en carrera
2. **Tiempo Promedio**: Tiempo desde saludo hasta confirmación
3. **Errores de Geocodificación**: % de direcciones no encontradas
4. **Satisfacción**: Feedback de usuarios sobre la IA
5. **Uso de GPS**: % de usuarios que usan ubicaciones vs texto

---

## 🎯 Próximos Pasos

1. **Instalar dependencias**: `pip install -r requirements.txt`
2. **Reiniciar servidor**: `python manage.py runserver`
3. **Probar conversación**: Envía "Hola" por WhatsApp
4. **Enviar ubicación GPS**: Comparte tu ubicación
5. **Monitorear logs**: Observa cómo Claude responde

---

## 🆘 Solución de Problemas

### Claude no responde

```bash
# Verificar que anthropic esté instalado
pip list | grep anthropic

# Reinstalar si es necesario
pip install anthropic==0.39.0
```

### Error de API Key

```python
# Verificar en ai_assistant.py
CLAUDE_API_KEY = "sk-ant-api03-..."
```

### Ubicaciones no se procesan

```bash
# Verificar logs
# Buscar: "📍 Ubicación GPS recibida"
# Si no aparece, revisar formato del webhook
```

---

## 🎉 ¡Listo!

**El sistema ahora cuenta con:**
- 🤖 IA conversacional con Claude
- 📍 Soporte para ubicaciones GPS
- 🗺️ Tracking en tiempo real
- 💬 Conversaciones naturales y humanas

**¡Pruébalo ahora y experimenta la diferencia!** ✨
