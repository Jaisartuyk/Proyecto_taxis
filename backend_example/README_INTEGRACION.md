# Guía de Integración: Chat con Media (Cloudinary)

## 📋 Resumen

Esta guía te muestra cómo integrar el soporte de imágenes y videos en tu chat existente **sin romper nada**.

## ✅ Cambios Realizados

Los siguientes archivos ya han sido actualizados:

1. ✅ **`taxis/models.py`** - Modelo `ChatMessage` actualizado con campos de media
2. ✅ **`taxis/serializers.py`** - Serializer actualizado para incluir campos de media
3. ✅ **`taxis/consumers.py`** - Consumer de WebSocket actualizado para manejar media
4. ✅ **`taxis/views.py`** - Vistas actualizadas y función `upload_chat_media` agregada
5. ✅ **`taxis/urls.py`** - Ruta `/api/chat/upload/` agregada

## 🚀 Pasos para Completar la Integración

### Paso 1: Ejecutar Migraciones

Los nuevos campos en `ChatMessage` requieren una migración:

```bash
python manage.py makemigrations
python manage.py migrate
```

**Nota:** Los campos nuevos son opcionales (`null=True, blank=True`), así que los mensajes existentes seguirán funcionando.

### Paso 2: Verificar Configuración de Cloudinary

Asegúrate de tener estas variables de entorno configuradas (ya las tienes en Railway):

- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### Paso 3: Actualizar el Frontend (JavaScript)

Necesitas actualizar tu JavaScript para:

1. **Subir archivos** antes de enviar el mensaje
2. **Enviar campos de media** en el WebSocket
3. **Mostrar imágenes/videos** en el chat

#### Ejemplo de código JavaScript:

```javascript
// Función para subir archivo y enviar mensaje
async function sendMediaMessage(driverId, file, messageText = '') {
    try {
        // 1. Subir archivo a Cloudinary
        const formData = new FormData();
        formData.append('file', file);
        
        const uploadResponse = await fetch('/api/chat/upload/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(), // Obtener token CSRF
            },
            body: formData
        });
        
        const uploadData = await uploadResponse.json();
        
        if (!uploadData.success) {
            alert('Error subiendo archivo: ' + uploadData.error);
            return;
        }
        
        // 2. Enviar mensaje con media vía WebSocket
        const messageData = {
            type: 'chat_message',
            recipient_id: driverId,
            message: messageText, // Opcional si hay media
            message_type: uploadData.message_type, // 'image' o 'video'
            media_url: uploadData.media_url,
            thumbnail_url: uploadData.thumbnail_url,
            metadata: uploadData.metadata
        };
        
        chatSocket.send(JSON.stringify(messageData));
        
    } catch (error) {
        console.error('Error enviando media:', error);
        alert('Error enviando archivo');
    }
}

// Función para mostrar mensajes con media
function renderMessage(msg) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.is_sent ? 'sent' : 'received'}`;
    
    if (msg.message_type === 'image' && msg.media_url) {
        messageDiv.innerHTML = `
            <img src="${msg.media_url}" style="max-width: 100%; border-radius: 8px;" />
            ${msg.message ? `<div>${msg.message}</div>` : ''}
        `;
    } else if (msg.message_type === 'video' && msg.media_url) {
        messageDiv.innerHTML = `
            <video controls style="max-width: 100%; border-radius: 8px;">
                <source src="${msg.media_url}" type="video/mp4">
            </video>
            ${msg.message ? `<div>${msg.message}</div>` : ''}
        `;
    } else {
        // Mensaje de texto normal
        messageDiv.textContent = msg.message;
    }
    
    chatLog.appendChild(messageDiv);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// Manejar mensajes recibidos del WebSocket
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    if (data.type === 'chat_message') {
        renderMessage({
            message: data.message,
            message_type: data.message_type || 'text',
            media_url: data.media_url,
            thumbnail_url: data.thumbnail_url,
            metadata: data.metadata || {},
            is_sent: data.sender_id == currentUser.id
        });
    }
};
```

### Paso 4: Actualizar la App Android (Flutter)

En tu app Flutter, necesitas:

1. **Subir archivo** usando `http.MultipartRequest`
2. **Enviar mensaje** con campos de media vía WebSocket
3. **Mostrar imágenes/videos** en el chat

#### Ejemplo Flutter:

```dart
// Subir archivo
Future<Map<String, dynamic>> uploadChatMedia(File file) async {
  var request = http.MultipartRequest(
    'POST',
    Uri.parse('$baseUrl/api/chat/upload/'),
  );
  
  request.headers['Authorization'] = 'Bearer $token';
  request.files.add(
    await http.MultipartFile.fromPath('file', file.path),
  );
  
  var response = await request.send();
  var responseData = await response.stream.bytesToString();
  return jsonDecode(responseData);
}

// Enviar mensaje con media
void sendMediaMessage(int recipientId, String mediaUrl, String messageType, {String? messageText}) {
  final message = {
    'type': 'chat_message',
    'recipient_id': recipientId,
    'message': messageText ?? '',
    'message_type': messageType,
    'media_url': mediaUrl,
  };
  
  channel.sink.add(jsonEncode(message));
}

// Mostrar mensaje con media
Widget buildMessage(ChatMessage msg) {
  if (msg.messageType == 'image' && msg.mediaUrl != null) {
    return Image.network(msg.mediaUrl!);
  } else if (msg.messageType == 'video' && msg.mediaUrl != null) {
    return VideoPlayer(NetworkVideoController(Uri.parse(msg.mediaUrl!)));
  } else {
    return Text(msg.message);
  }
}
```

## 🧪 Verificación

### 1. Verificar que los mensajes de texto siguen funcionando

```bash
# Enviar un mensaje de texto normal (debe funcionar igual que antes)
```

### 2. Verificar endpoint de upload

```bash
curl -X POST http://localhost:8000/api/chat/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.jpg"
```

Debe retornar:
```json
{
  "success": true,
  "media_url": "https://res.cloudinary.com/...",
  "message_type": "image",
  "metadata": {...}
}
```

### 3. Verificar que el historial incluye campos de media

```bash
curl http://localhost:8000/api/chat_history/1/
```

Debe incluir `message_type`, `media_url`, `thumbnail_url`, `metadata` en cada mensaje.

## 🔧 Solución de Problemas

### Error: "No se proporcionó ningún archivo"

- Verifica que estás enviando el archivo con el nombre `file` en el FormData
- Verifica que el Content-Type es `multipart/form-data`

### Error: "El archivo es demasiado grande"

- El límite es 10MB. Puedes cambiarlo en `upload_chat_media`:
  ```python
  max_size = 20 * 1024 * 1024  # 20MB
  ```

### Error: "Tipo de archivo no soportado"

- Solo se aceptan imágenes (jpg, png, gif, webp) y videos (mp4, webm, mov, avi)
- Puedes agregar más tipos en `upload_chat_media`

### Los mensajes con media no se muestran

- Verifica que el WebSocket está enviando los campos `message_type`, `media_url`, etc.
- Verifica que el frontend está renderizando estos campos correctamente
- Revisa la consola del navegador para errores de JavaScript

### Error de Cloudinary

- Verifica que las variables de entorno están configuradas correctamente
- Verifica que tienes créditos en tu cuenta de Cloudinary
- Revisa los logs de Cloudinary en su dashboard

## 📝 Notas Importantes

1. **Compatibilidad hacia atrás:** Todos los campos nuevos son opcionales. Los mensajes existentes seguirán funcionando con `message_type='text'`.

2. **Límites de tamaño:** Por defecto, el límite es 10MB. Ajusta según tus necesidades.

3. **Thumbnails:** Solo se generan para videos. Las imágenes usan la URL original.

4. **Metadata:** Se guarda información adicional (dimensiones, tamaño, duración) en el campo `metadata` como JSON.

5. **Seguridad:** El endpoint `/api/chat/upload/` requiere autenticación (`@login_required`).

## ✅ Checklist Final

- [ ] Migraciones ejecutadas
- [ ] Cloudinary configurado
- [ ] Endpoint `/api/chat/upload/` funciona
- [ ] WebSocket envía campos de media
- [ ] Frontend muestra imágenes/videos
- [ ] App Android envía y recibe media
- [ ] Mensajes de texto siguen funcionando
- [ ] Historial incluye mensajes con media

## 🎉 ¡Listo!

Tu chat ahora soporta imágenes y videos tanto desde la web como desde la app Android, sin romper la funcionalidad existente.

