# Actualización de Flutter para Chat con Media

## 📋 Resumen del Estado Actual

Revisando `MAIN_DART_COMPLETO.dart`, encontré:

✅ **Ya implementado:**
- Lista de mensajes (`_chatMessages`)
- Carga de mensajes desde el servidor (`_loadChatMessages`)
- Conexión WebSocket para recibir mensajes (`_connectChatWebSocket`)
- Manejo de mensajes recibidos vía WebSocket

❌ **Falta implementar:**
- UI completa del chat (pantalla de chat)
- Función para enviar mensajes
- Soporte para subir archivos (imágenes/videos)
- Mostrar imágenes/videos en el chat
- Botón para seleccionar archivos

## 🔧 Cambios Necesarios

### 1. Agregar Dependencias en `pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  # ... dependencias existentes ...
  
  # NUEVAS DEPENDENCIAS PARA MEDIA
  image_picker: ^1.0.4  # Para seleccionar imágenes/videos
  http: ^1.1.0  # Ya deberías tenerla
  cached_network_image: ^3.3.0  # Para mostrar imágenes desde URL
  video_player: ^2.7.0  # Para reproducir videos
```

### 2. Actualizar `_loadChatMessages` para incluir campos de media

**Ubicación:** Línea ~825 en `MAIN_DART_COMPLETO.dart`

**Cambio necesario:**
```dart
// El backend ahora devuelve campos adicionales:
// message_type, media_url, thumbnail_url, metadata
// Estos campos ya están en la respuesta, solo necesitas usarlos
```

### 3. Actualizar `_connectChatWebSocket` para recibir campos de media

**Ubicación:** Línea ~786 en `MAIN_DART_COMPLETO.dart`

**Cambio necesario:**
```dart
if (data['type'] == 'chat_message') {
  print('✅ Nuevo mensaje de chat recibido por WebSocket: ${data['message']}');
  // Agregar mensaje a la lista CON CAMPOS DE MEDIA
  if (mounted) {
    setState(() {
      _chatMessages.add({
        'sender_id': data['sender_id'],
        'sender_name': data['sender_name'] ?? 'Desconocido',
        'message': data['message'] ?? '',
        'timestamp': DateTime.now().toString(),
        'is_sent': false,
        // NUEVOS CAMPOS DE MEDIA
        'message_type': data['message_type'] ?? 'text',
        'media_url': data['media_url'],
        'thumbnail_url': data['thumbnail_url'],
        'metadata': data['metadata'] ?? {},
      });
    });
  }
}
```

### 4. Agregar Función para Subir Archivos

**Agregar después de `_loadChatMessages` (línea ~900):**

```dart
// ============================================
// FUNCIÓN: SUBIR ARCHIVO A CLOUDINARY
// ============================================

Future<Map<String, dynamic>?> _uploadChatMedia(File file) async {
  try {
    print('📤 Subiendo archivo: ${file.path}');
    
    // Crear request multipart
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('$API_BASE_URL/chat/upload/'),
    );
    
    // Agregar archivo
    request.files.add(
      await http.MultipartFile.fromPath('file', file.path),
    );
    
    // Enviar request
    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      print('✅ Archivo subido exitosamente: ${data['media_url']}');
      return data;
    } else {
      print('❌ Error subiendo archivo: ${response.statusCode}');
      print('   Respuesta: ${response.body}');
      return null;
    }
  } catch (e) {
    print('❌ Excepción subiendo archivo: $e');
    return null;
  }
}
```

### 5. Agregar Función para Enviar Mensajes

**Agregar después de `_uploadChatMedia`:**

```dart
// ============================================
// FUNCIÓN: ENVIAR MENSAJE DE CHAT
// ============================================

Future<void> _sendChatMessage({
  required String driverId,
  String? messageText,
  File? mediaFile,
  String? messageType,
  String? mediaUrl,
  String? thumbnailUrl,
  Map<String, dynamic>? metadata,
}) async {
  try {
    if (_chatChannel == null || _chatChannel!.closeCode != null) {
      print('⚠️ WebSocket no conectado, reconectando...');
      _connectChatWebSocket(driverId);
      await Future.delayed(const Duration(seconds: 1));
    }
    
    // Preparar mensaje
    final message = {
      'type': 'chat_message',
      'recipient_id': '1', // ID del admin (central)
      'message': messageText ?? '',
      'message_type': messageType ?? 'text',
    };
    
    // Agregar campos de media si existen
    if (mediaUrl != null) {
      message['media_url'] = mediaUrl;
      if (thumbnailUrl != null) {
        message['thumbnail_url'] = thumbnailUrl;
      }
      if (metadata != null) {
        message['metadata'] = metadata;
      }
    }
    
    // Enviar por WebSocket
    _chatChannel?.sink.add(jsonEncode(message));
    
    // Agregar mensaje a la lista localmente (para feedback inmediato)
    if (mounted) {
      setState(() {
        _chatMessages.add({
          'sender_id': driverId,
          'sender_name': 'Yo',
          'message': messageText ?? '',
          'timestamp': DateTime.now().toString(),
          'is_sent': true,
          'message_type': messageType ?? 'text',
          'media_url': mediaUrl,
          'thumbnail_url': thumbnailUrl,
          'metadata': metadata ?? {},
        });
      });
    }
    
    print('✅ Mensaje enviado: ${messageText ?? '(con media)'}');
  } catch (e) {
    print('❌ Error enviando mensaje: $e');
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ Error enviando mensaje: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
```

### 6. Crear Pantalla de Chat Completa

**Crear nuevo archivo: `lib/chat_screen.dart`**

```dart
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:video_player/video_player.dart';
import 'dart:io';

class ChatScreen extends StatefulWidget {
  final String driverId;
  final List<Map<String, dynamic>> initialMessages;
  final Function(String, String?, File?) onSendMessage;
  final Function(String) onUploadFile;

  const ChatScreen({
    Key? key,
    required this.driverId,
    required this.initialMessages,
    required this.onSendMessage,
    required this.onUploadFile,
  }) : super(key: key);

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  List<Map<String, dynamic>> _messages = [];
  final ImagePicker _picker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _messages = List.from(widget.initialMessages);
  }

  Future<void> _pickImage() async {
    final XFile? image = await _picker.pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );
    
    if (image != null) {
      final file = File(image.path);
      widget.onUploadFile(file.path);
    }
  }

  Future<void> _pickVideo() async {
    final XFile? video = await _picker.pickVideo(
      source: ImageSource.gallery,
    );
    
    if (video != null) {
      final file = File(video.path);
      widget.onUploadFile(file.path);
    }
  }

  void _showMediaOptions() {
    showModalBottomSheet(
      context: context,
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Galería de Fotos'),
              onTap: () {
                Navigator.pop(context);
                _pickImage();
              },
            ),
            ListTile(
              leading: const Icon(Icons.video_library),
              title: const Text('Galería de Videos'),
              onTap: () {
                Navigator.pop(context);
                _pickVideo();
              },
            ),
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Tomar Foto'),
              onTap: () async {
                Navigator.pop(context);
                final XFile? image = await _picker.pickImage(
                  source: ImageSource.camera,
                  imageQuality: 85,
                );
                if (image != null) {
                  widget.onUploadFile(image.path);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  void _sendMessage() {
    final text = _messageController.text.trim();
    if (text.isNotEmpty) {
      widget.onSendMessage(widget.driverId, text, null);
      _messageController.clear();
    }
  }

  Widget _buildMessage(Map<String, dynamic> message) {
    final isSent = message['is_sent'] == true;
    final messageType = message['message_type'] ?? 'text';
    final mediaUrl = message['media_url'];
    final messageText = message['message'] ?? '';

    return Align(
      alignment: isSent ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isSent ? Colors.blue : Colors.grey[300],
          borderRadius: BorderRadius.circular(16),
        ),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.7,
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Mostrar media si existe
            if (mediaUrl != null && messageType == 'image')
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: CachedNetworkImage(
                  imageUrl: mediaUrl,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  placeholder: (context, url) => const CircularProgressIndicator(),
                  errorWidget: (context, url, error) => const Icon(Icons.error),
                ),
              ),
            
            if (mediaUrl != null && messageType == 'video')
              _buildVideoPlayer(mediaUrl),
            
            // Mostrar texto si existe
            if (messageText.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  messageText,
                  style: TextStyle(
                    color: isSent ? Colors.white : Colors.black,
                  ),
                ),
              ),
            
            // Timestamp
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                _formatTimestamp(message['timestamp']),
                style: TextStyle(
                  fontSize: 10,
                  color: isSent ? Colors.white70 : Colors.black54,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildVideoPlayer(String videoUrl) {
    // Implementación básica - puedes usar video_player para mejor control
    return GestureDetector(
      onTap: () {
        // Abrir video en pantalla completa
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => Scaffold(
              appBar: AppBar(title: const Text('Video')),
              body: Center(
                child: VideoPlayerWidget(videoUrl: videoUrl),
              ),
            ),
          ),
        );
      },
      child: Container(
        height: 200,
        decoration: BoxDecoration(
          color: Colors.black,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Stack(
          alignment: Alignment.center,
          children: [
            CachedNetworkImage(
              imageUrl: message['thumbnail_url'] ?? '',
              width: double.infinity,
              fit: BoxFit.cover,
            ),
            const Icon(Icons.play_circle_filled, size: 50, color: Colors.white),
          ],
        ),
      ),
    );
  }

  String _formatTimestamp(String? timestamp) {
    if (timestamp == null) return '';
    try {
      final date = DateTime.parse(timestamp);
      return '${date.hour.toString().padLeft(2, '0')}:${date.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return timestamp;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chat con Central'),
        backgroundColor: Colors.orange,
      ),
      body: Column(
        children: [
          // Lista de mensajes
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return _buildMessage(_messages[index]);
              },
            ),
          ),
          
          // Input de mensaje
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.grey.withOpacity(0.2),
                  spreadRadius: 1,
                  blurRadius: 4,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                // Botón de adjuntar
                IconButton(
                  icon: const Icon(Icons.attach_file),
                  onPressed: _showMediaOptions,
                  color: Colors.orange,
                ),
                
                // Input de texto
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: const InputDecoration(
                      hintText: 'Escribe un mensaje...',
                      border: InputBorder.none,
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                
                // Botón de enviar
                IconButton(
                  icon: const Icon(Icons.send),
                  onPressed: _sendMessage,
                  color: Colors.orange,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}

// Widget para reproducir video
class VideoPlayerWidget extends StatefulWidget {
  final String videoUrl;

  const VideoPlayerWidget({Key? key, required this.videoUrl}) : super(key: key);

  @override
  State<VideoPlayerWidget> createState() => _VideoPlayerWidgetState();
}

class _VideoPlayerWidgetState extends State<VideoPlayerWidget> {
  VideoPlayerController? _controller;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.networkUrl(Uri.parse(widget.videoUrl))
      ..initialize().then((_) {
        setState(() {});
        _controller?.play();
      });
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const Center(child: CircularProgressIndicator());
    }
    return AspectRatio(
      aspectRatio: _controller!.value.aspectRatio,
      child: VideoPlayer(_controller!),
    );
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
}
```

### 7. Integrar ChatScreen en el Widget Principal

**En `MAIN_DART_COMPLETO.dart`, agregar botón para abrir chat:**

```dart
// En el build method, agregar botón de chat
ElevatedButton.icon(
  icon: const Icon(Icons.chat),
  label: const Text('Abrir Chat'),
  onPressed: _isServiceRunning
      ? () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ChatScreen(
                driverId: _driverIdController.text.trim(),
                initialMessages: _chatMessages,
                onSendMessage: (driverId, messageText, file) async {
                  if (file != null) {
                    // Subir archivo primero
                    final uploadResult = await _uploadChatMedia(file);
                    if (uploadResult != null) {
                      await _sendChatMessage(
                        driverId: driverId,
                        messageText: messageText,
                        messageType: uploadResult['message_type'],
                        mediaUrl: uploadResult['media_url'],
                        thumbnailUrl: uploadResult['thumbnail_url'],
                        metadata: uploadResult['metadata'],
                      );
                    }
                  } else {
                    // Enviar solo texto
                    await _sendChatMessage(
                      driverId: driverId,
                      messageText: messageText,
                    );
                  }
                },
                onUploadFile: (filePath) async {
                  final file = File(filePath);
                  final uploadResult = await _uploadChatMedia(file);
                  if (uploadResult != null) {
                    await _sendChatMessage(
                      driverId: _driverIdController.text.trim(),
                      messageType: uploadResult['message_type'],
                      mediaUrl: uploadResult['media_url'],
                      thumbnailUrl: uploadResult['thumbnail_url'],
                      metadata: uploadResult['metadata'],
                    );
                  }
                },
              ),
            ),
          );
        }
      : null,
  style: ElevatedButton.styleFrom(
    backgroundColor: Colors.orange,
    foregroundColor: Colors.white,
  ),
),
```

## ✅ Checklist de Implementación

- [ ] Agregar dependencias en `pubspec.yaml`
- [ ] Actualizar `_loadChatMessages` para usar campos de media
- [ ] Actualizar `_connectChatWebSocket` para recibir campos de media
- [ ] Agregar función `_uploadChatMedia`
- [ ] Agregar función `_sendChatMessage`
- [ ] Crear `ChatScreen` widget
- [ ] Integrar `ChatScreen` en el widget principal
- [ ] Probar subida de imágenes
- [ ] Probar subida de videos
- [ ] Probar envío de mensajes de texto
- [ ] Verificar que los mensajes se muestran correctamente

## 🎯 Resumen

El código Flutter actual tiene la base para el chat, pero falta:
1. **UI completa del chat** - Crear `ChatScreen`
2. **Envío de mensajes** - Agregar `_sendChatMessage`
3. **Subida de archivos** - Agregar `_uploadChatMedia`
4. **Mostrar media** - Actualizar widgets para mostrar imágenes/videos

Con estos cambios, el chat en Flutter tendrá la misma funcionalidad que la versión web.

