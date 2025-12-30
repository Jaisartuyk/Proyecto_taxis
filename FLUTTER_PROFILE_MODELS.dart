// ============================================
// MODELOS PARA GESTIÓN DE PERFIL
// ============================================
// Archivo: lib/models/user_profile.dart

class UserProfile {
  final int id;
  final String username;
  final String email;
  final String firstName;
  final String lastName;
  final String phoneNumber;
  final String? nationalId;
  final String role;
  final String? profilePicture;
  final Organization? organization;
  final DriverInfo? driverInfo;

  UserProfile({
    required this.id,
    required this.username,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.phoneNumber,
    this.nationalId,
    required this.role,
    this.profilePicture,
    this.organization,
    this.driverInfo,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      firstName: json['first_name'] ?? '',
      lastName: json['last_name'] ?? '',
      phoneNumber: json['phone_number'] ?? '',
      nationalId: json['national_id'],
      role: json['role'],
      profilePicture: json['profile_picture'],
      organization: json['organization'] != null
          ? Organization.fromJson(json['organization'])
          : null,
      driverInfo: json['driver_info'] != null
          ? DriverInfo.fromJson(json['driver_info'])
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'username': username,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'phone_number': phoneNumber,
      'national_id': nationalId,
      'role': role,
      'profile_picture': profilePicture,
      'organization': organization?.toJson(),
      'driver_info': driverInfo?.toJson(),
    };
  }

  String get fullName => '$firstName $lastName'.trim();
}

class Organization {
  final int id;
  final String name;
  final String? logo;

  Organization({
    required this.id,
    required this.name,
    this.logo,
  });

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(
      id: json['id'],
      name: json['name'],
      logo: json['logo'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'logo': logo,
    };
  }
}

class DriverInfo {
  final String? driverNumber;
  final String? driverStatus;
  final String? plateNumber;
  final String? carModel;
  final String? carColor;
  final int? carYear;

  DriverInfo({
    this.driverNumber,
    this.driverStatus,
    this.plateNumber,
    this.carModel,
    this.carColor,
    this.carYear,
  });

  factory DriverInfo.fromJson(Map<String, dynamic> json) {
    return DriverInfo(
      driverNumber: json['driver_number'],
      driverStatus: json['driver_status'],
      plateNumber: json['plate_number'],
      carModel: json['car_model'],
      carColor: json['car_color'],
      carYear: json['car_year'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'driver_number': driverNumber,
      'driver_status': driverStatus,
      'plate_number': plateNumber,
      'car_model': carModel,
      'car_color': carColor,
      'car_year': carYear,
    };
  }
}

class NotificationSettings {
  final bool pushEnabled;
  final bool emailEnabled;
  final bool smsEnabled;
  final bool rideNotifications;
  final bool chatNotifications;
  final bool audioNotifications;

  NotificationSettings({
    required this.pushEnabled,
    required this.emailEnabled,
    required this.smsEnabled,
    required this.rideNotifications,
    required this.chatNotifications,
    required this.audioNotifications,
  });

  factory NotificationSettings.fromJson(Map<String, dynamic> json) {
    return NotificationSettings(
      pushEnabled: json['push_enabled'] ?? true,
      emailEnabled: json['email_enabled'] ?? false,
      smsEnabled: json['sms_enabled'] ?? false,
      rideNotifications: json['ride_notifications'] ?? true,
      chatNotifications: json['chat_notifications'] ?? true,
      audioNotifications: json['audio_notifications'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'push_enabled': pushEnabled,
      'email_enabled': emailEnabled,
      'sms_enabled': smsEnabled,
      'ride_notifications': rideNotifications,
      'chat_notifications': chatNotifications,
      'audio_notifications': audioNotifications,
    };
  }
}
