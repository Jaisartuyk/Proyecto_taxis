// ============================================
// MAIN.DART COMPLETO - APP CONDUCTOR
// Taxi "De Aquí Pa'llá"
// ============================================

import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_background_service/flutter_background_service.dart';
import 'package:flutter_background_service_android/flutter_background_service_android.dart';
import 'package:location/location.dart' as loc;
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:http/http.dart' as http;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

// ============================================
// CONFIGURACIÓN
// ============================================

const String WEBSOCKET_URL = 'wss://taxis-deaquipalla.up.railway.app/ws/audio/conductores/';
const String CHAT_WEBSOCKET_URL = 'wss://taxis-deaquipalla.up.railway.app/ws/chat/';
const String API_BASE_URL = 'https://taxis-deaquipalla.up.railway.app/api';
const String FCM_REGISTER_URL = 'https://taxis-deaquipalla.up.railway.app/api/register-fcm-token/';

// ============================================
// HANDLER PARA NOTIFICACIONES EN BACKGROUND
// ============================================
// Esta función DEBE ser top-level (fuera de cualquier clase)
// y DEBE tener la anotación @pragma('vm:entry-point')

@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // IMPORTANTE: Inicializar Firebase si no está inicializado
  await Firebase.initializeApp();
  
  print('📬 [BACKGROUND] Notificación recibida cuando la app está cerrada:');
  print('   Título: ${message.notification?.title}');
  print('   Cuerpo: ${message.notification?.body}');
  print('   Data: ${message.data}');
  
  // Si es un mensaje de chat, guardarlo localmente para que aparezca cuando se abra la app
  if (message.data['type'] == 'chat_message') {
    print('💬 Guardando mensaje de chat recibido en background...');
    // Los mensajes se cargarán desde el servidor cuando se abra la app
    // No necesitamos guardarlos localmente porque el servidor los tiene
  }
}

// ============================================
// MAIN - PUNTO DE ENTRADA
// ============================================

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  try {
    await Firebase.initializeApp();
    print('✅ Firebase inicializado correctamente');
    
    // Configurar FCM
    FirebaseMessaging messaging = FirebaseMessaging.instance;
    
    // ⚠️ IMPORTANTE: Registrar el handler para notificaciones en background
    // Esto permite recibir notificaciones cuando la app está completamente cerrada
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    print('✅ Handler de background registrado');
    
    // Solicitar permisos
    NotificationSettings settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );
    print('📱 Permisos de notificación: ${settings.authorizationStatus}');
    
    // Obtener token FCM
    String? token = await messaging.getToken();
    print('🔥 FCM TOKEN: $token');
    print('📋 Token FCM obtenido, se registrará cuando el usuario ingrese su ID');
    
    // Manejar notificaciones en primer plano (app abierta)
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('📬 [FOREGROUND] Notificación recibida: ${message.notification?.title}');
      print('   Cuerpo: ${message.notification?.body}');
      print('   Data: ${message.data}');
      // Mostrar notificación local cuando la app está abierta
      _showLocalNotification(message);
    });
    
    // Manejar cuando el usuario toca una notificación y abre la app (app en background)
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('👆 [TAPPED] Usuario tocó la notificación (app en background): ${message.notification?.title}');
      print('   Data: ${message.data}');
      // Esperar un momento para que la app esté lista antes de navegar
      Future.delayed(const Duration(milliseconds: 300), () {
        _handleNotificationTap(message);
      });
    });
    
    // Verificar si la app fue abierta desde una notificación (cuando estaba cerrada)
    RemoteMessage? initialMessage = await messaging.getInitialMessage();
    if (initialMessage != null) {
      print('🚀 [INITIAL] App abierta desde notificación (app estaba cerrada): ${initialMessage.notification?.title}');
      print('   Data: ${initialMessage.data}');
      
      // Si es un mensaje de chat, guardar el driverId si está en los datos
      if (initialMessage.data['type'] == 'chat_message') {
        print('💬 Notificación de chat detectada, se cargarán mensajes al conectar');
        // El driverId se obtendrá cuando el usuario ingrese su ID
      }
      
      // Esperar a que la app esté completamente inicializada antes de navegar
      // Esto evita la pantalla negra
      Future.delayed(const Duration(milliseconds: 1000), () {
        _handleNotificationTap(initialMessage);
      });
    }
    
  } catch (e) {
    print('❌ Error inicializando Firebase: $e');
  }
  
  // Inicializar servicio en segundo plano
  await initializeService();
  
  runApp(const MyApp());
}

// ============================================
// FUNCIONES AUXILIARES PARA NOTIFICACIONES
// ============================================

// Instancia global de FlutterLocalNotifications
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

// Inicializar notificaciones locales
Future<void> _initializeLocalNotifications() async {
  const AndroidInitializationSettings initializationSettingsAndroid =
      AndroidInitializationSettings('@mipmap/ic_launcher');
  
  const DarwinInitializationSettings initializationSettingsIOS =
      DarwinInitializationSettings(
    requestAlertPermission: true,
    requestBadgePermission: true,
    requestSoundPermission: true,
  );
  
  const InitializationSettings initializationSettings = InitializationSettings(
    android: initializationSettingsAndroid,
    iOS: initializationSettingsIOS,
  );
  
  await flutterLocalNotificationsPlugin.initialize(
    initializationSettings,
    onDidReceiveNotificationResponse: (NotificationResponse response) {
      print('👆 Notificación local tocada: ${response.payload}');
    },
  );
  
  // Crear canal de notificaciones para Android
  const AndroidNotificationChannel channel = AndroidNotificationChannel(
    'high_importance_channel', // id
    'Notificaciones Importantes', // name
    description: 'Este canal se usa para notificaciones importantes',
    importance: Importance.high,
    playSound: true,
  );
  
  await flutterLocalNotificationsPlugin
      .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);
}

// Mostrar notificación local cuando la app está en primer plano
Future<void> _showLocalNotification(RemoteMessage message) async {
  const AndroidNotificationDetails androidPlatformChannelSpecifics =
      AndroidNotificationDetails(
    'high_importance_channel',
    'Notificaciones Importantes',
    channelDescription: 'Este canal se usa para notificaciones importantes',
    importance: Importance.high,
    priority: Priority.high,
    showWhen: true,
    playSound: true,
  );
  
  const DarwinNotificationDetails iOSPlatformChannelSpecifics =
      DarwinNotificationDetails(
    presentAlert: true,
    presentBadge: true,
    presentSound: true,
  );
  
  const NotificationDetails platformChannelSpecifics = NotificationDetails(
    android: androidPlatformChannelSpecifics,
    iOS: iOSPlatformChannelSpecifics,
  );
  
  await flutterLocalNotificationsPlugin.show(
    message.hashCode,
    message.notification?.title ?? 'Nueva notificación',
    message.notification?.body ?? '',
    platformChannelSpecifics,
    payload: message.data.toString(),
  );
}

// Global NavigatorKey para navegar desde cualquier lugar (incluyendo handlers de notificaciones)
final GlobalKey<NavigatorState> navigatorKey = GlobalKey<NavigatorState>();

// Manejar cuando el usuario toca una notificación
void _handleNotificationTap(RemoteMessage message) {
  print('📱 Procesando tap en notificación...');
  print('   Tipo: ${message.data['type']}');
  print('   Sender: ${message.data['sender_name']}');
  print('   Data completa: ${message.data}');
  
  // Esperar a que la app esté completamente inicializada antes de navegar
  Future.delayed(const Duration(milliseconds: 500), () {
    final navigator = navigatorKey.currentState;
    if (navigator == null) {
      print('⚠️ Navigator no está disponible aún, reintentando...');
      Future.delayed(const Duration(milliseconds: 1000), () {
        _handleNotificationTap(message);
      });
      return;
    }
    
    // Navegar según el tipo de notificación
    if (message.data['type'] == 'chat_message') {
      print('💬 Navegando a pantalla de chat...');
      // Si tienes una pantalla de chat específica, navega allí
      // Por ahora, solo mostramos un mensaje
      // TODO: Implementar navegación a ChatScreen cuando esté disponible
      print('   📝 Nota: La pantalla de chat se abrirá cuando el usuario conecte el servicio');
    } else {
      print('📱 Tipo de notificación no manejado: ${message.data['type']}');
    }
  });
}

// ============================================
// SERVICIO EN SEGUNDO PLANO
// ============================================

Future<void> initializeService() async {
  final service = FlutterBackgroundService();
  
  await service.configure(
    androidConfiguration: AndroidConfiguration(
      onStart: onStart,
      autoStart: false,
      isForegroundMode: true,
      notificationChannelId: 'taxi_conductor_channel',
      initialNotificationTitle: 'Taxi Conductor',
      initialNotificationContent: 'Servicio iniciado',
      foregroundServiceNotificationId: 888,
    ),
    iosConfiguration: IosConfiguration(
      autoStart: false,
      onForeground: onStart,
      onBackground: onIosBackground,
    ),
  );
}

@pragma('vm:entry-point')
bool onIosBackground(ServiceInstance service) {
  return true;
}

@pragma('vm:entry-point')
void onStart(ServiceInstance service) async {
  if (service is AndroidServiceInstance) {
    service.on('setAsForeground').listen((event) {
      service.setAsForegroundService();
    });
    service.on('setAsBackground').listen((event) {
      service.setAsBackgroundService();
    });
  }

  WebSocketChannel? channel;
  WebSocketChannel? chatChannel;
  StreamSubscription? locationSubscription;
  final location = loc.Location();
  final AudioRecorder audioRecorder = AudioRecorder();
  String driverId = "conductor_default";

  // ============================================
  // EVENTO: CONECTAR WEBSOCKET
  // ============================================
  
  service.on('connect').listen((event) async {
    if (channel == null || channel?.closeCode != null) {
      
      // Obtener ID del conductor
      if (event != null && event['driverId'] != null && event['driverId'].isNotEmpty) {
        driverId = event['driverId'];
      }
      
      try {
        // Conectar WebSocket
        channel = WebSocketChannel.connect(Uri.parse(WEBSOCKET_URL));
        service.invoke('update_status', {
          'connected': true,
          'message': 'Conectado al servidor'
        });
        
        // Escuchar mensajes del servidor (audio y ubicación)
        channel?.stream.listen(
          (message) {
            print("📨 WebSocket - Mensaje recibido: $message");
            try {
              final data = jsonDecode(message);
              if (data['type'] == 'chat_message') {
                print("💬 Mensaje de chat recibido por WebSocket de audio");
                // Notificar al servicio que hay un nuevo mensaje
                service.invoke('new_chat_message', data);
              }
            } catch (e) {
              print("⚠️ Error procesando mensaje WebSocket: $e");
            }
          },
          onDone: () {
            print("🔴 WebSocket - Conexión cerrada");
            service.invoke('update_status', {
              'connected': false,
              'message': 'Desconectado'
            });
            locationSubscription?.cancel();
            channel = null;
          },
          onError: (error) {
            print("❌ WebSocket - Error: $error");
            service.invoke('update_status', {
              'connected': false,
              'message': 'Error de conexión'
            });
            locationSubscription?.cancel();
            channel = null;
          },
        );

        // ============================================
        // ENVIAR UBICACIÓN EN TIEMPO REAL
        // ============================================
        
        locationSubscription = location.onLocationChanged.listen(
          (loc.LocationData currentLocation) {
            if (channel != null && channel?.closeCode == null) {
              final locationData = {
                "type": "driver_location_update",
                "driverId": driverId,
                "latitude": currentLocation.latitude,
                "longitude": currentLocation.longitude,
              };
              channel?.sink.add(jsonEncode(locationData));
              print("📍 Ubicación enviada: ${currentLocation.latitude}, ${currentLocation.longitude}");
            }
          },
        );

      } catch (e) {
        print("❌ Error al conectar WebSocket: $e");
        service.invoke('update_status', {
          'connected': false,
          'message': 'Error al conectar'
        });
      }
    }
  });

  // ============================================
  // EVENTO: DESCONECTAR WEBSOCKET
  // ============================================
  
  service.on('disconnect').listen((event) {
    locationSubscription?.cancel();
    channel?.sink.close();
    channel = null;
    service.invoke('update_status', {
      'connected': false,
      'message': 'Desconectado'
    });
  });

  // ============================================
  // EVENTO: DETENER SERVICIO
  // ============================================
  
  service.on('stopService').listen((event) {
    service.stopSelf();
  });

  // ============================================
  // EVENTO: INICIAR GRABACIÓN DE AUDIO
  // ============================================
  
  service.on('start_recording').listen((event) async {
    print("🎤 Iniciando grabación de audio...");
    
    // Verificar permiso de micrófono
    var micStatus = await Permission.microphone.status;
    if (micStatus.isGranted) {
      print("✅ Permiso de micrófono concedido");
      
      final tempDir = await getTemporaryDirectory();
      final path = '${tempDir.path}/audio.m4a';
      const config = RecordConfig(encoder: AudioEncoder.opus);
      
      await audioRecorder.start(config, path: path);
      print("🎙️ Grabación iniciada en: $path");
    } else {
      print("❌ Permiso de micrófono DENEGADO");
    }
  });

  // ============================================
  // EVENTO: DETENER GRABACIÓN Y ENVIAR AUDIO
  // ============================================
  
  service.on('stop_recording').listen((event) async {
    print("⏹️ Deteniendo grabación de audio...");
    
    final path = await audioRecorder.stop();
    
    if (path != null) {
      print("✅ Grabación detenida. Archivo: $path");
      
      final audioBytes = await getAudioBytes(path);
      
      if (audioBytes.isNotEmpty) {
        final audioBase64 = base64Encode(audioBytes);
        
        if (channel != null && channel?.closeCode == null) {
          print("📤 Enviando audio al servidor...");
          
          final audioData = {
            "type": "driver_audio_message",
            "senderId": driverId,
            "senderRole": "Driver",
            "audio": audioBase64,
          };
          
          channel?.sink.add(jsonEncode(audioData));
          print("✅ Audio enviado correctamente");
        } else {
          print("❌ WebSocket no conectado. No se pudo enviar el audio");
        }
      } else {
        print("❌ El archivo de audio está vacío");
      }
    } else {
      print("❌ No se pudo obtener la ruta del archivo de audio");
    }
  });
}

// ============================================
// FUNCIÓN: LEER BYTES DEL ARCHIVO DE AUDIO
// ============================================

Future<List<int>> getAudioBytes(String path) async {
  final file = File(path);
  if (await file.exists()) {
    return await file.readAsBytes();
  }
  return [];
}

// ============================================
// APP PRINCIPAL
// ============================================

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: "Taxi De Aquí Pa'llá",
      navigatorKey: navigatorKey, // IMPORTANTE: Para navegar desde handlers de notificaciones
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.orange),
        useMaterial3: true,
        fontFamily: 'Poppins',
      ),
      home: const DriverHomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

// ============================================
// PANTALLA PRINCIPAL DEL CONDUCTOR
// ============================================

class DriverHomePage extends StatefulWidget {
  const DriverHomePage({super.key});

  @override
  State<DriverHomePage> createState() => _DriverHomePageState();
}

class _DriverHomePageState extends State<DriverHomePage> {
  bool _isConnected = false;
  String _statusMessage = "Desconectado";
  bool _isServiceRunning = false;
  String? _fcmToken;
  final _driverIdController = TextEditingController();
  List<Map<String, dynamic>> _chatMessages = []; // Lista de mensajes de chat

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Inicializar notificaciones locales
    await _initializeLocalNotifications();
    
    // Obtener token FCM
    String? token = await FirebaseMessaging.instance.getToken();
    print('🔑 Token FCM obtenido: ${token != null ? "${token.substring(0, 30)}..." : "null"}');
    setState(() {
      _fcmToken = token;
    });
    
    if (token == null) {
      print('⚠️ ADVERTENCIA: No se pudo obtener el token FCM. Las notificaciones push no funcionarán.');
    }
    
    // NO registrar el token aquí porque el driverId aún no está disponible
    // El token se registrará cuando el usuario conecte el servicio
    
    // Escuchar actualizaciones del token FCM (puede cambiar)
    FirebaseMessaging.instance.onTokenRefresh.listen((newToken) {
      print('🔄 Token FCM actualizado: $newToken');
      if (mounted) {
        setState(() {
          _fcmToken = newToken;
        });
        // Re-registrar el nuevo token si hay un driverId
        if (_driverIdController.text.isNotEmpty) {
          _registerFCMToken(newToken, _driverIdController.text);
        }
      }
    });

    // Escuchar actualizaciones del servicio
    final service = FlutterBackgroundService();
    service.on('update_status').listen((event) {
      if (mounted) {
        setState(() {
          _isConnected = event!['connected'];
          _statusMessage = event['message'];
        });
      }
    });

    // Verificar si el servicio está corriendo
    service.isRunning().then((running) {
      if (mounted) {
        setState(() {
          _isServiceRunning = running;
        });
      }
    });
  }

  @override
  void dispose() {
    _driverIdController.dispose();
    super.dispose();
  }

  void _toggleService() {
    final service = FlutterBackgroundService();
    
    if (_isServiceRunning) {
      // Desconectar servicio
      service.invoke('disconnect');
      service.invoke('stopService');
    } else {
      // Validar que el ID no esté vacío
      if (_driverIdController.text.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Por favor ingresa tu ID de conductor'),
            backgroundColor: Colors.red,
          ),
        );
        return;
      }
      
      final driverId = _driverIdController.text.trim();
      
      // IMPORTANTE: Registrar token FCM PRIMERO (antes de conectar)
      print('🔍 [DEBUG] Verificando condiciones para registrar token FCM:');
      print('   - Token FCM: ${_fcmToken != null ? "${_fcmToken!.substring(0, 30)}..." : "null"}');
      print('   - driverId: "$driverId" (longitud: ${driverId.length})');
      
      if (_fcmToken != null && driverId.isNotEmpty) {
        print('✅ [PASO 1] Condiciones OK - Registrando token FCM...');
        await _registerFCMToken(_fcmToken!, driverId);
        // Esperar un momento para que el token se registre en el servidor
        await Future.delayed(const Duration(milliseconds: 500));
      } else {
        print('❌ [PASO 1] No se puede registrar token FCM:');
        if (_fcmToken == null) {
          print('   ⚠️ Token FCM: null - No se obtuvo el token de Firebase');
          print('   💡 Solución: Verifica que Firebase esté correctamente configurado');
        }
        if (driverId.isEmpty) {
          print('   ⚠️ driverId: vacío - El usuario no ingresó su ID');
        }
      }
      
      // PASO 2: Cargar mensajes desde el servidor (los que llegaron mientras la app estaba cerrada)
      print('📜 [PASO 2] Cargando mensajes que llegaron mientras la app estaba cerrada...');
      await _loadChatMessages(driverId);
      
      // PASO 3: Conectar WebSocket de chat (para recibir mensajes en tiempo real)
      print('💬 [PASO 3] Conectando WebSocket de chat...');
      _connectChatWebSocket(driverId);
      
      // Iniciar servicio
      service.startService();
      service.invoke('connect', {'driverId': _driverIdController.text});
    }
    
    setState(() {
      _isServiceRunning = !_isServiceRunning;
    });
  }

  void _showFCMToken() {
    if (_fcmToken != null) {
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Token FCM'),
          content: SelectableText(_fcmToken!),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cerrar'),
            ),
          ],
        ),
      );
    }
  }

  // ============================================
  // FUNCIÓN: REGISTRAR TOKEN FCM EN BACKEND
  // ============================================
  
  Future<void> _registerFCMToken(String token, String driverId) async {
    try {
      print('📱 Registrando token FCM para conductor: $driverId');
      
      if (driverId.isEmpty) {
        print('⚠️ driverId está vacío, no se puede registrar el token');
        return;
      }
      
      // Enviar el driverId tal cual (puede ser ID numérico o username)
      // El backend ahora acepta ambos formatos
      final payload = {
        'token': token,
        'platform': 'android',
        'user_id': driverId, // Puede ser ID numérico (11) o username ("carlos")
      };
      
      print('📤 Enviando payload: $payload');
      
      final response = await http.post(
        Uri.parse(FCM_REGISTER_URL),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode(payload),
      );
      
      print('📥 Respuesta del servidor: ${response.statusCode}');
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        final responseData = jsonDecode(response.body);
        print('✅ Token FCM registrado exitosamente!');
        print('   Usuario: ${responseData['username'] ?? driverId}');
        print('   Mensaje: ${responseData['message'] ?? 'OK'}');
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ Token FCM registrado para ${responseData['username'] ?? driverId}'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } else {
        final errorBody = response.body;
        print('❌ Error registrando token FCM: ${response.statusCode}');
        print('📄 Respuesta: $errorBody');
        
        // Intentar parsear el error para mostrar un mensaje más claro
        String errorMessage = 'Error ${response.statusCode}';
        try {
          final errorData = jsonDecode(errorBody);
          errorMessage = errorData['error'] ?? errorData['message'] ?? errorMessage;
          print('   Error detallado: $errorMessage');
        } catch (e) {
          print('   Error (texto plano): $errorBody');
        }
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('⚠️ $errorMessage'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 4),
            ),
          );
        }
      }
    } catch (e) {
      print('❌ Excepción al registrar token FCM: $e');
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Error: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  // ============================================
  // FUNCIÓN: CONECTAR WEBSOCKET DE CHAT
  // ============================================
  
  WebSocketChannel? _chatChannel;
  
  void _connectChatWebSocket(String driverId) {
    try {
      // Obtener el ID numérico del conductor
      int? userId;
      try {
        userId = int.parse(driverId);
      } catch (e) {
        // Si no es numérico, buscar por username (esto requeriría una API adicional)
        print('⚠️ driverId no es numérico, usando directamente: $driverId');
        userId = null;
      }
      
      // URL del WebSocket de chat: /ws/chat/{user_id}/
      final chatUrl = userId != null 
          ? '$CHAT_WEBSOCKET_URL$userId/'
          : '$CHAT_WEBSOCKET_URL$driverId/';
      
      print('💬 Conectando WebSocket de chat: $chatUrl');
      
      _chatChannel = WebSocketChannel.connect(Uri.parse(chatUrl));
      
      _chatChannel?.stream.listen(
        (message) {
          print('💬 Mensaje de chat recibido: $message');
          try {
            final data = jsonDecode(message);
            if (data['type'] == 'chat_message') {
              print('✅ Nuevo mensaje de chat recibido por WebSocket: ${data['message']}');
              // Agregar mensaje a la lista
              if (mounted) {
                setState(() {
                  _chatMessages.add({
                    'sender_id': data['sender_id'],
                    'sender_name': data['sender_name'] ?? 'Desconocido',
                    'message': data['message'],
                    'timestamp': DateTime.now().toString(),
                    'is_sent': false,
                  });
                });
              }
            }
          } catch (e) {
            print('⚠️ Error procesando mensaje de chat: $e');
          }
        },
        onDone: () {
          print('🔴 WebSocket de chat desconectado');
          _chatChannel = null;
        },
        onError: (error) {
          print('❌ Error en WebSocket de chat: $error');
          _chatChannel = null;
        },
      );
      
      print('✅ WebSocket de chat conectado');
    } catch (e) {
      print('❌ Error conectando WebSocket de chat: $e');
    }
  }

  // ============================================
  // FUNCIÓN: CARGAR MENSAJES DESDE EL SERVIDOR
  // ============================================
  
  Future<void> _loadChatMessages(String driverId) async {
    try {
      if (driverId.isEmpty) {
        print('⚠️ driverId está vacío, no se pueden cargar mensajes');
        return;
      }
      
      // El backend ahora acepta tanto ID numérico como username
      final url = '$API_BASE_URL/driver/chat_history/$driverId/';
      print('📡 Cargando mensajes desde: $url');
      
      final response = await http.get(
        Uri.parse(url),
        headers: {'Content-Type': 'application/json'},
      );
      
      print('📥 Respuesta: ${response.statusCode}');
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final messages = data['messages'] as List;
        print('✅ ${messages.length} mensajes cargados desde el servidor');
        
        // Guardar mensajes en la lista
        if (mounted) {
          setState(() {
            _chatMessages = List<Map<String, dynamic>>.from(messages);
          });
        }
        
        // Mostrar en logs
        for (var msg in messages) {
          final isSent = msg['is_sent'] == true;
          final sender = msg['sender_name'] ?? 'Desconocido';
          final messageText = msg['message'] ?? '';
          final timestamp = msg['timestamp'] ?? '';
          print('   ${isSent ? "📤" : "📥"} $sender: $messageText ($timestamp)');
        }
        
        // Mostrar notificación al usuario
        if (mounted && messages.isNotEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('✅ ${messages.length} mensajes cargados'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 2),
            ),
          );
        }
      } else {
        print('❌ Error cargando mensajes: ${response.statusCode}');
        print('   Respuesta: ${response.body}');
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('⚠️ Error: ${response.statusCode}'),
              backgroundColor: Colors.orange,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      }
    } catch (e) {
      print('❌ Excepción cargando mensajes: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ Error: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Taxi De Aquí Pa\'llá'),
        backgroundColor: Colors.orange,
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications),
            onPressed: _showFCMToken,
            tooltip: 'Ver Token FCM',
          ),
        ],
      ),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              // Logo
              const Icon(
                Icons.local_taxi,
                size: 100,
                color: Colors.orange,
              ),
              const SizedBox(height: 20),
              
              // Título
              const Text(
                'Panel del Conductor',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 40),
              
              // Campo de ID del conductor
              TextField(
                controller: _driverIdController,
                enabled: !_isServiceRunning,
                decoration: const InputDecoration(
                  labelText: 'ID del Conductor',
                  border: OutlineInputBorder(),
                  hintText: 'Ej: conductor_007',
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 30),
              
              // Estado de conexión
              const Text(
                'Estado de Conexión:',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 10),
              
              Chip(
                label: Text(
                  _statusMessage,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                backgroundColor: _isConnected ? Colors.green : Colors.red,
                avatar: Icon(
                  _isConnected ? Icons.check_circle : Icons.cancel,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 40),
              
              // Botón de conectar/desconectar
              ElevatedButton.icon(
                icon: Icon(
                  _isServiceRunning
                      ? Icons.stop_circle_outlined
                      : Icons.play_circle_outline,
                ),
                label: Text(
                  _isServiceRunning
                      ? 'Desconectar Servicio'
                      : 'Conectar Servicio',
                ),
                onPressed: _toggleService,
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      _isServiceRunning ? Colors.red : Colors.green,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 30,
                    vertical: 15,
                  ),
                  textStyle: const TextStyle(fontSize: 18),
                ),
              ),
              const SizedBox(height: 60),
              
              // Instrucciones para el botón de audio
              const Text(
                'Pulsar y mantener para hablar',
                style: TextStyle(
                  color: Colors.grey,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 20),
              
              // Botón de audio (walkie-talkie)
              GestureDetector(
                onLongPressStart: (_) {
                  if (_isServiceRunning) {
                    FlutterBackgroundService().invoke('start_recording');
                    // Feedback visual
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('🎤 Grabando...'),
                        duration: Duration(milliseconds: 500),
                      ),
                    );
                  }
                },
                onLongPressEnd: (_) {
                  if (_isServiceRunning) {
                    FlutterBackgroundService().invoke('stop_recording');
                  }
                },
                child: Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    color: _isServiceRunning ? Colors.blue : Colors.grey,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        spreadRadius: 2,
                        blurRadius: 8,
                        offset: const Offset(0, 3),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.mic,
                    color: Colors.white,
                    size: 60,
                  ),
                ),
              ),
              const SizedBox(height: 20),
              
              // Información adicional
              if (_fcmToken != null)
                Padding(
                  padding: const EdgeInsets.only(top: 20),
                  child: Text(
                    'Token FCM: ${_fcmToken!.substring(0, 20)}...',
                    style: const TextStyle(
                      fontSize: 12,
                      color: Colors.grey,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
