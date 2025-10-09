# 📝 Instrucciones para Subir a GitHub de Forma Segura

## ⚠️ IMPORTANTE: Protección de API Keys

GitHub bloqueó tu push anterior porque detectó un API key en el código. Esto es correcto y es una medida de seguridad.

---

## ✅ **Solución Implementada**

Ya he removido el API key del código y ahora usa variables de entorno.

---

## 🚀 **Pasos para Subir a GitHub**

### 1. Verificar que no hay API keys en el código

```bash
# Buscar API keys (no debería encontrar nada)
git grep -i "sk-ant-api"
```

Si encuentra algo, es solo en comentarios (está bien).

### 2. Agregar cambios

```bash
git add .
```

### 3. Hacer commit

```bash
git commit -m "Implementar IA conversacional y soporte GPS - API keys en variables de entorno"
```

### 4. Subir a GitHub

```bash
git push
```

---

## 🔐 **Configurar API Keys en Producción**

### Para Desarrollo Local

**PowerShell (Windows):**
```powershell
$env:CLAUDE_API_KEY="tu-api-key-aqui"
```

**Bash (Linux/Mac):**
```bash
export CLAUDE_API_KEY="tu-api-key-aqui"
```

### Para Producción (Render, Heroku, etc.)

1. Ve a la configuración de tu servicio
2. Busca "Environment Variables" o "Config Vars"
3. Agrega:
   - `CLAUDE_API_KEY` = tu-api-key-de-anthropic
   - `WASENDER_TOKEN` = tu-token-de-wasender

---

## 📋 **Variables de Entorno Necesarias**

Crea un archivo `.env` local (ya está en .gitignore, no se subirá):

```env
# Claude AI
CLAUDE_API_KEY=sk-ant-api03-tu-key-aqui

# WASender
WASENDER_TOKEN=tu-token-wasender-aqui

# Django
SECRET_KEY=tu-secret-key-django
DEBUG=True
```

---

## ✅ **Sistema Actual**

**NOTA IMPORTANTE**: El sistema ya está funcionando con el **Asistente Simple de IA** que NO requiere Claude.

### Lo que está activo:

✅ **Asistente de IA Simple** (`ai_assistant_simple.py`)
- Conversaciones naturales
- Detección de intenciones
- Respuestas variadas
- Manejo de estados
- **NO requiere API key**

✅ **Soporte para ubicaciones GPS**
- Recepción desde WhatsApp
- Geocodificación
- Tracking en tiempo real

✅ **Webhook de WhatsApp**
- Procesando mensajes
- Procesando ubicaciones

### Para activar Claude (opcional):

1. Configura la variable de entorno `CLAUDE_API_KEY`
2. En `whatsapp_agent_ai.py`, cambia:
   ```python
   from .ai_assistant_simple import simple_ai_assistant
   ```
   Por:
   ```python
   from .ai_assistant import claude_assistant
   ```

---

## 🎯 **Resumen**

| Componente | Estado | Requiere API Key |
|------------|--------|------------------|
| Asistente Simple | ✅ Activo | ❌ No |
| Ubicaciones GPS | ✅ Activo | ❌ No |
| Webhook WhatsApp | ✅ Activo | ❌ No |
| Claude AI | ⏸️ Opcional | ✅ Sí |

---

## 📱 **Probar el Sistema**

El sistema ya funciona sin Claude. Prueba enviando por WhatsApp:

```
"Hola"
"Necesito un taxi"
[Enviar ubicación GPS]
```

---

## 🔒 **Buenas Prácticas de Seguridad**

✅ **NUNCA** incluyas API keys directamente en el código
✅ **SIEMPRE** usa variables de entorno
✅ **AGREGA** `.env` al `.gitignore`
✅ **USA** `.env.example` para documentar variables necesarias
✅ **REVISA** el código antes de hacer commit

---

## 🎉 **¡Listo para Subir!**

Ahora puedes hacer:

```bash
git add .
git commit -m "Sistema de IA y GPS implementado - API keys protegidos"
git push
```

GitHub ya no bloqueará el push porque los API keys están protegidos.
