/// ========================================================
/// BOTÓN DE PÁNICO - Código de Referencia para Flutter
/// ========================================================
/// 
/// Este archivo contiene el código Dart listo para integrar
/// en la aplicación móvil del conductor.
/// 
/// CÓMO USAR:
/// 1. Copia la clase PanicService a tu proyecto Flutter
/// 2. Copia el widget PanicButton a la pantalla principal del conductor
/// 3. Asegúrate de tener las dependencias: http, geolocator
/// 
/// ENDPOINTS DEL SERVIDOR:
/// - POST /api/panic/  →  Activar alerta de pánico
///   Body: { "latitude": -0.12, "longitude": -78.56 }
///   Headers: { "Authorization": "Token <user_token>" }
///
/// RESPUESTA EXITOSA:
/// {
///   "success": true,
///   "alert_id": 1,
///   "message": "🚨 Alerta de pánico activada..."
/// }
/// ========================================================

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:geolocator/geolocator.dart';

// =====================================================
// SERVICIO DE PÁNICO
// =====================================================

class PanicService {
  final String baseUrl;
  final String token;
  
  PanicService({
    required this.baseUrl,
    required this.token,
  });
  
  /// Activar alerta de pánico
  /// Obtiene la ubicación actual y la envía al servidor
  Future<Map<String, dynamic>> activatePanic() async {
    try {
      // 1. Obtener ubicación actual
      Position position = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 5),
      );
      
      // 2. Enviar al servidor
      final response = await http.post(
        Uri.parse('$baseUrl/api/panic/'),
        headers: {
          'Authorization': 'Token $token',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'latitude': position.latitude,
          'longitude': position.longitude,
        }),
      );
      
      if (response.statusCode == 201) {
        final data = jsonDecode(response.body);
        return {
          'success': true,
          'alert_id': data['alert_id'],
          'message': data['message'],
        };
      } else {
        final error = jsonDecode(response.body);
        return {
          'success': false,
          'error': error['error'] ?? 'Error desconocido',
        };
      }
    } catch (e) {
      return {
        'success': false,
        'error': 'Error de conexión: $e',
      };
    }
  }
}


// =====================================================
// WIDGET DEL BOTÓN DE PÁNICO
// =====================================================

class PanicButton extends StatefulWidget {
  final PanicService panicService;
  
  const PanicButton({
    super.key,
    required this.panicService,
  });
  
  @override
  State<PanicButton> createState() => _PanicButtonState();
}

class _PanicButtonState extends State<PanicButton> 
    with SingleTickerProviderStateMixin {
  
  bool _isActivating = false;
  bool _isLongPressing = false;
  late AnimationController _animationController;
  late Animation<double> _scaleAnimation;
  
  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1500),
    );
    _scaleAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeInOut),
    );
    _animationController.repeat(reverse: true);
  }
  
  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }
  
  Future<void> _onPanicActivated() async {
    if (_isActivating) return;
    
    setState(() => _isActivating = true);
    
    // Vibración fuerte como feedback
    // HapticFeedback.heavyImpact();
    
    final result = await widget.panicService.activatePanic();
    
    setState(() => _isActivating = false);
    
    if (mounted) {
      if (result['success'] == true) {
        _showAlert(
          '🚨 ALERTA ENVIADA',
          result['message'] ?? 'La central y conductores cercanos han sido notificados.',
          Colors.green,
        );
      } else {
        _showAlert(
          '❌ ERROR',
          result['error'] ?? 'No se pudo enviar la alerta.',
          Colors.red,
        );
      }
    }
  }
  
  void _showAlert(String title, String message, Color color) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1a1a2e),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: Text(
          title,
          style: TextStyle(color: color, fontWeight: FontWeight.bold),
          textAlign: TextAlign.center,
        ),
        content: Text(
          message,
          style: const TextStyle(color: Colors.white70),
          textAlign: TextAlign.center,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('ENTENDIDO', style: TextStyle(color: Colors.amber)),
          ),
        ],
      ),
    );
  }
  
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onLongPressStart: (_) {
        setState(() => _isLongPressing = true);
        // Mantener presionado 2 segundos para activar
        Future.delayed(const Duration(seconds: 2), () {
          if (_isLongPressing && mounted) {
            _onPanicActivated();
            setState(() => _isLongPressing = false);
          }
        });
      },
      onLongPressEnd: (_) {
        setState(() => _isLongPressing = false);
      },
      child: AnimatedBuilder(
        animation: _scaleAnimation,
        builder: (context, child) {
          return Transform.scale(
            scale: _isLongPressing ? 1.3 : _scaleAnimation.value,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    _isActivating
                        ? Colors.orange
                        : _isLongPressing
                            ? Colors.red.shade900
                            : Colors.red,
                    Colors.red.shade900,
                  ],
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.red.withOpacity(0.5),
                    blurRadius: 20,
                    spreadRadius: 5,
                  ),
                ],
              ),
              child: Center(
                child: _isActivating
                    ? const CircularProgressIndicator(
                        color: Colors.white,
                        strokeWidth: 3,
                      )
                    : Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(
                            Icons.warning_rounded,
                            color: Colors.white,
                            size: 30,
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _isLongPressing ? 'ACTIVANDO...' : 'SOS',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
              ),
            ),
          );
        },
      ),
    );
  }
}


// =====================================================
// EJEMPLO DE USO EN LA PANTALLA DEL CONDUCTOR
// =====================================================
//
// En tu widget principal del conductor, agregar:
//
// final panicService = PanicService(
//   baseUrl: 'https://taxis-deaquipalla.up.railway.app',
//   token: userToken, // Token de autenticación del conductor
// );
//
// // En algún lugar visible de la pantalla:
// Positioned(
//   bottom: 100,
//   right: 20,
//   child: PanicButton(panicService: panicService),
// )
//
// =====================================================
// ENDPOINT PARA COMPARTIR LINK DE SEGUIMIENTO
// =====================================================
//
// POST /api/rides/{ride_id}/share/
// Headers: { "Authorization": "Token <user_token>" }
//
// Respuesta:
// {
//   "success": true,
//   "tracking_url": "https://taxis-deaquipalla.up.railway.app/track/a7h2k9l1/",
//   "token": "a7h2k9l1",
//   "expires_at": "2026-05-11T20:00:00Z"
// }
//
// El conductor o cliente puede compartir este link por WhatsApp
// para que su familia vea la ubicación del taxi en tiempo real.
