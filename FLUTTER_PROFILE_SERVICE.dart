// ============================================
// SERVICIO API PARA GESTIÓN DE PERFIL
// ============================================
// Archivo: lib/services/profile_service.dart

import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/user_profile.dart';

class ProfileService {
  final String baseUrl;
  final String? authToken;

  ProfileService({
    required this.baseUrl,
    this.authToken,
  });

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (authToken != null) 'Authorization': 'Bearer $authToken',
      };

  // ============================================
  // OBTENER PERFIL
  // ============================================
  Future<UserProfile?> getProfile() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/profile/'),
        headers: _headers,
      );

      print('📥 GET Profile: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return UserProfile.fromJson(data['profile']);
        }
      }
      return null;
    } catch (e) {
      print('❌ Error al obtener perfil: $e');
      return null;
    }
  }

  // ============================================
  // ACTUALIZAR PERFIL
  // ============================================
  Future<Map<String, dynamic>> updateProfile({
    String? firstName,
    String? lastName,
    String? phoneNumber,
    String? email,
  }) async {
    try {
      final body = <String, dynamic>{};
      if (firstName != null) body['first_name'] = firstName;
      if (lastName != null) body['last_name'] = lastName;
      if (phoneNumber != null) body['phone_number'] = phoneNumber;
      if (email != null) body['email'] = email;

      final response = await http.put(
        Uri.parse('$baseUrl/api/profile/update/'),
        headers: _headers,
        body: json.encode(body),
      );

      print('📤 UPDATE Profile: ${response.statusCode}');

      final data = json.decode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        return {
          'success': true,
          'message': data['message'],
          'profile': UserProfile.fromJson(data['profile']),
        };
      } else {
        return {
          'success': false,
          'error': data['error'] ?? 'Error desconocido',
        };
      }
    } catch (e) {
      print('❌ Error al actualizar perfil: $e');
      return {
        'success': false,
        'error': 'Error de conexión: $e',
      };
    }
  }

  // ============================================
  // ACTUALIZAR FOTO DE PERFIL
  // ============================================
  Future<Map<String, dynamic>> updateProfilePicture(File imageFile) async {
    try {
      var request = http.MultipartRequest(
        'PUT',
        Uri.parse('$baseUrl/api/profile/update/'),
      );

      // Headers
      if (authToken != null) {
        request.headers['Authorization'] = 'Bearer $authToken';
      }

      // Agregar imagen
      request.files.add(
        await http.MultipartFile.fromPath(
          'profile_picture',
          imageFile.path,
        ),
      );

      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);

      print('📤 UPDATE Profile Picture: ${response.statusCode}');

      final data = json.decode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        return {
          'success': true,
          'message': data['message'],
          'profile': UserProfile.fromJson(data['profile']),
        };
      } else {
        return {
          'success': false,
          'error': data['error'] ?? 'Error desconocido',
        };
      }
    } catch (e) {
      print('❌ Error al actualizar foto: $e');
      return {
        'success': false,
        'error': 'Error de conexión: $e',
      };
    }
  }

  // ============================================
  // ACTUALIZAR VEHÍCULO (Solo conductores)
  // ============================================
  Future<Map<String, dynamic>> updateVehicle({
    String? plateNumber,
    String? carModel,
    String? carColor,
    int? carYear,
  }) async {
    try {
      final body = <String, dynamic>{};
      if (plateNumber != null) body['plate_number'] = plateNumber;
      if (carModel != null) body['car_model'] = carModel;
      if (carColor != null) body['car_color'] = carColor;
      if (carYear != null) body['car_year'] = carYear;

      final response = await http.put(
        Uri.parse('$baseUrl/api/profile/vehicle/'),
        headers: _headers,
        body: json.encode(body),
      );

      print('📤 UPDATE Vehicle: ${response.statusCode}');

      final data = json.decode(response.body);

      if (response.statusCode == 200 && data['success'] == true) {
        return {
          'success': true,
          'message': data['message'],
          'vehicle': data['vehicle'],
        };
      } else {
        return {
          'success': false,
          'error': data['error'] ?? 'Error desconocido',
        };
      }
    } catch (e) {
      print('❌ Error al actualizar vehículo: $e');
      return {
        'success': false,
        'error': 'Error de conexión: $e',
      };
    }
  }

  // ============================================
  // OBTENER CONFIGURACIÓN DE NOTIFICACIONES
  // ============================================
  Future<NotificationSettings?> getNotificationSettings() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/api/profile/notifications/'),
        headers: _headers,
      );

      print('📥 GET Notification Settings: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data['success'] == true) {
          return NotificationSettings.fromJson(data['settings']);
        }
      }
      return null;
    } catch (e) {
      print('❌ Error al obtener configuración: $e');
      return null;
    }
  }
}
