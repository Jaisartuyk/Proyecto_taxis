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

// ============================================
// CONFIGURACIÓN
// ============================================

const String WEBSOCKET_URL = 'wss://taxis-deaquipalla.up.railway.app/ws/audio/conductores/';
const String API_BASE_URL = 'https://taxis-deaquipalla.up.railway.app/api';

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
    
    // Solicitar permisos
    NotificationSettings settings = await messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    print('📱 Permisos de notificación: ${settings.authorizationStatus}');
    
    // Obtener token FCM
    String? token = await messaging.getToken();
    print('🔥 FCM TOKEN: $token');
    print('📋 Copia este token para registrarlo en el backend');
    
    // Manejar notificaciones en primer plano
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('📬 Notificación recibida: ${message.notification?.title}');
      // TODO: Mostrar notificación local
    });
    
  } catch (e) {
    print('❌ Error inicializando Firebase: $e');
  }
  
  // Inicializar servicio en segundo plano
  await initializeService();
  
  runApp(const MyApp());
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
        
        // Escuchar mensajes del servidor
        channel?.stream.listen(
          (message) {
            print("📨 WebSocket - Mensaje recibido: $message");
            // TODO: Procesar mensajes del servidor
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

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Obtener token FCM
    String? token = await FirebaseMessaging.instance.getToken();
    setState(() {
      _fcmToken = token;
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
