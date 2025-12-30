// ============================================
// PANTALLA DE PERFIL COMPLETA
// ============================================
// Archivo: lib/screens/profile_screen.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/user_profile.dart';
import '../services/profile_service.dart';

class ProfileScreen extends StatefulWidget {
  final ProfileService profileService;

  const ProfileScreen({
    Key? key,
    required this.profileService,
  }) : super(key: key);

  @override
  _ProfileScreenState createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  UserProfile? _profile;
  NotificationSettings? _notificationSettings;
  bool _isLoading = true;
  final ImagePicker _imagePicker = ImagePicker();

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  Future<void> _loadProfile() async {
    setState(() => _isLoading = true);

    final profile = await widget.profileService.getProfile();
    final settings = await widget.profileService.getNotificationSettings();

    setState(() {
      _profile = profile;
      _notificationSettings = settings;
      _isLoading = false;
    });
  }

  Future<void> _pickAndUploadImage() async {
    try {
      final XFile? image = await _imagePicker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 800,
        maxHeight: 800,
        imageQuality: 85,
      );

      if (image != null) {
        // Mostrar loading
        showDialog(
          context: context,
          barrierDismissible: false,
          builder: (context) => const Center(
            child: CircularProgressIndicator(),
          ),
        );

        final result = await widget.profileService.updateProfilePicture(
          File(image.path),
        );

        Navigator.pop(context); // Cerrar loading

        if (result['success'] == true) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('✅ Foto actualizada exitosamente'),
              backgroundColor: Colors.green,
            ),
          );
          _loadProfile(); // Recargar perfil
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('❌ ${result['error']}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      }
    } catch (e) {
      print('Error al seleccionar imagen: $e');
    }
  }

  void _showEditProfileDialog() {
    final firstNameController =
        TextEditingController(text: _profile?.firstName);
    final lastNameController = TextEditingController(text: _profile?.lastName);
    final phoneController = TextEditingController(text: _profile?.phoneNumber);
    final emailController = TextEditingController(text: _profile?.email);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('✏️ Editar Perfil'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: firstNameController,
                decoration: const InputDecoration(
                  labelText: 'Nombre',
                  prefixIcon: Icon(Icons.person),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: lastNameController,
                decoration: const InputDecoration(
                  labelText: 'Apellido',
                  prefixIcon: Icon(Icons.person_outline),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: phoneController,
                decoration: const InputDecoration(
                  labelText: 'Teléfono',
                  prefixIcon: Icon(Icons.phone),
                ),
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  prefixIcon: Icon(Icons.email),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);

              // Mostrar loading
              showDialog(
                context: context,
                barrierDismissible: false,
                builder: (context) => const Center(
                  child: CircularProgressIndicator(),
                ),
              );

              final result = await widget.profileService.updateProfile(
                firstName: firstNameController.text,
                lastName: lastNameController.text,
                phoneNumber: phoneController.text,
                email: emailController.text,
              );

              Navigator.pop(context); // Cerrar loading

              if (result['success'] == true) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('✅ Perfil actualizado exitosamente'),
                    backgroundColor: Colors.green,
                  ),
                );
                _loadProfile(); // Recargar perfil
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('❌ ${result['error']}'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  void _showEditVehicleDialog() {
    if (_profile?.role != 'driver') return;

    final plateController =
        TextEditingController(text: _profile?.driverInfo?.plateNumber);
    final modelController =
        TextEditingController(text: _profile?.driverInfo?.carModel);
    final colorController =
        TextEditingController(text: _profile?.driverInfo?.carColor);
    final yearController = TextEditingController(
        text: _profile?.driverInfo?.carYear?.toString() ?? '');

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('🚗 Editar Vehículo'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: plateController,
                decoration: const InputDecoration(
                  labelText: 'Placa',
                  prefixIcon: Icon(Icons.credit_card),
                ),
                textCapitalization: TextCapitalization.characters,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: modelController,
                decoration: const InputDecoration(
                  labelText: 'Modelo',
                  prefixIcon: Icon(Icons.directions_car),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: colorController,
                decoration: const InputDecoration(
                  labelText: 'Color',
                  prefixIcon: Icon(Icons.palette),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: yearController,
                decoration: const InputDecoration(
                  labelText: 'Año',
                  prefixIcon: Icon(Icons.calendar_today),
                ),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);

              // Mostrar loading
              showDialog(
                context: context,
                barrierDismissible: false,
                builder: (context) => const Center(
                  child: CircularProgressIndicator(),
                ),
              );

              final result = await widget.profileService.updateVehicle(
                plateNumber: plateController.text,
                carModel: modelController.text,
                carColor: colorController.text,
                carYear: int.tryParse(yearController.text),
              );

              Navigator.pop(context); // Cerrar loading

              if (result['success'] == true) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('✅ Vehículo actualizado exitosamente'),
                    backgroundColor: Colors.green,
                  ),
                );
                _loadProfile(); // Recargar perfil
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('❌ ${result['error']}'),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: const Text('Guardar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_profile == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Mi Perfil')),
        body: const Center(
          child: Text('Error al cargar perfil'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Perfil'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadProfile,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadProfile,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // ============================================
            // FOTO DE PERFIL
            // ============================================
            Center(
              child: Stack(
                children: [
                  CircleAvatar(
                    radius: 60,
                    backgroundImage: _profile!.profilePicture != null
                        ? NetworkImage(_profile!.profilePicture!)
                        : null,
                    child: _profile!.profilePicture == null
                        ? Text(
                            _profile!.firstName.isNotEmpty
                                ? _profile!.firstName[0].toUpperCase()
                                : '?',
                            style: const TextStyle(fontSize: 40),
                          )
                        : null,
                  ),
                  Positioned(
                    bottom: 0,
                    right: 0,
                    child: CircleAvatar(
                      radius: 20,
                      backgroundColor: Theme.of(context).primaryColor,
                      child: IconButton(
                        icon: const Icon(Icons.camera_alt,
                            size: 20, color: Colors.white),
                        onPressed: _pickAndUploadImage,
                      ),
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 16),

            // Nombre completo
            Center(
              child: Text(
                _profile!.fullName,
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),

            Center(
              child: Text(
                '@${_profile!.username}',
                style: TextStyle(
                  fontSize: 16,
                  color: Colors.grey[600],
                ),
              ),
            ),

            const SizedBox(height: 8),

            // Rol
            Center(
              child: Chip(
                label: Text(
                  _profile!.role == 'driver'
                      ? '🚗 Conductor'
                      : _profile!.role == 'customer'
                          ? '👤 Cliente'
                          : _profile!.role,
                ),
                backgroundColor: Colors.blue[100],
              ),
            ),

            const SizedBox(height: 24),

            // ============================================
            // INFORMACIÓN PERSONAL
            // ============================================
            _buildSectionCard(
              title: '👤 Información Personal',
              children: [
                _buildInfoTile(
                  icon: Icons.phone,
                  label: 'Teléfono',
                  value: _profile!.phoneNumber,
                ),
                _buildInfoTile(
                  icon: Icons.email,
                  label: 'Email',
                  value: _profile!.email,
                ),
                if (_profile!.nationalId != null)
                  _buildInfoTile(
                    icon: Icons.badge,
                    label: 'Cédula',
                    value: _profile!.nationalId!,
                  ),
                const SizedBox(height: 8),
                ElevatedButton.icon(
                  onPressed: _showEditProfileDialog,
                  icon: const Icon(Icons.edit),
                  label: const Text('Editar Perfil'),
                  style: ElevatedButton.styleFrom(
                    minimumSize: const Size(double.infinity, 45),
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // ============================================
            // VEHÍCULO (Solo conductores)
            // ============================================
            if (_profile!.role == 'driver')
              _buildSectionCard(
                title: '🚗 Mi Vehículo',
                children: [
                  _buildInfoTile(
                    icon: Icons.credit_card,
                    label: 'Placa',
                    value: _profile!.driverInfo?.plateNumber ?? 'No registrado',
                  ),
                  _buildInfoTile(
                    icon: Icons.directions_car,
                    label: 'Modelo',
                    value: _profile!.driverInfo?.carModel ?? 'No registrado',
                  ),
                  _buildInfoTile(
                    icon: Icons.palette,
                    label: 'Color',
                    value: _profile!.driverInfo?.carColor ?? 'No registrado',
                  ),
                  if (_profile!.driverInfo?.carYear != null)
                    _buildInfoTile(
                      icon: Icons.calendar_today,
                      label: 'Año',
                      value: _profile!.driverInfo!.carYear.toString(),
                    ),
                  const SizedBox(height: 8),
                  ElevatedButton.icon(
                    onPressed: _showEditVehicleDialog,
                    icon: const Icon(Icons.edit),
                    label: const Text('Editar Vehículo'),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 45),
                    ),
                  ),
                ],
              ),

            if (_profile!.role == 'driver') const SizedBox(height: 16),

            // ============================================
            // NOTIFICACIONES
            // ============================================
            _buildSectionCard(
              title: '🔔 Notificaciones',
              children: [
                if (_notificationSettings != null) ...[
                  _buildSwitchTile(
                    icon: Icons.notifications_active,
                    label: 'Notificaciones Push',
                    value: _notificationSettings!.pushEnabled,
                    onChanged: (value) {
                      // TODO: Implementar actualización
                    },
                  ),
                  _buildSwitchTile(
                    icon: Icons.directions_car,
                    label: 'Notificaciones de Carreras',
                    value: _notificationSettings!.rideNotifications,
                    onChanged: (value) {
                      // TODO: Implementar actualización
                    },
                  ),
                  _buildSwitchTile(
                    icon: Icons.chat,
                    label: 'Notificaciones de Chat',
                    value: _notificationSettings!.chatNotifications,
                    onChanged: (value) {
                      // TODO: Implementar actualización
                    },
                  ),
                  _buildSwitchTile(
                    icon: Icons.mic,
                    label: 'Notificaciones de Audio',
                    value: _notificationSettings!.audioNotifications,
                    onChanged: (value) {
                      // TODO: Implementar actualización
                    },
                  ),
                ] else
                  const Center(child: CircularProgressIndicator()),
              ],
            ),

            const SizedBox(height: 16),

            // ============================================
            // ORGANIZACIÓN
            // ============================================
            if (_profile!.organization != null)
              _buildSectionCard(
                title: '🏢 Mi Cooperativa',
                children: [
                  ListTile(
                    leading: _profile!.organization!.logo != null
                        ? Image.network(
                            _profile!.organization!.logo!,
                            width: 40,
                            height: 40,
                          )
                        : const Icon(Icons.business, size: 40),
                    title: Text(
                      _profile!.organization!.name,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),

            const SizedBox(height: 16),

            // ============================================
            // AYUDA Y SOPORTE
            // ============================================
            _buildSectionCard(
              title: '❓ Ayuda y Soporte',
              children: [
                ListTile(
                  leading: const Icon(Icons.help_outline),
                  title: const Text('Preguntas Frecuentes'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: Navegar a FAQ
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.support_agent),
                  title: const Text('Contactar Soporte'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: Abrir chat de soporte
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.phone),
                  title: const Text('WhatsApp'),
                  subtitle: const Text('+57 XXX XXX XXXX'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    // TODO: Abrir WhatsApp
                  },
                ),
              ],
            ),

            const SizedBox(height: 24),

            // ============================================
            // CERRAR SESIÓN
            // ============================================
            ElevatedButton.icon(
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Cerrar Sesión'),
                    content: const Text(
                        '¿Estás seguro que deseas cerrar sesión?'),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Cancelar'),
                      ),
                      ElevatedButton(
                        onPressed: () {
                          // TODO: Implementar logout
                          Navigator.pop(context);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.red,
                        ),
                        child: const Text('Cerrar Sesión'),
                      ),
                    ],
                  ),
                );
              },
              icon: const Icon(Icons.logout),
              label: const Text('Cerrar Sesión'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.red,
                minimumSize: const Size(double.infinity, 50),
              ),
            ),

            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionCard({
    required String title,
    required List<Widget> children,
  }) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            const Divider(),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildInfoTile({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: Colors.grey[600]),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSwitchTile({
    required IconData icon,
    required String label,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return SwitchListTile(
      secondary: Icon(icon),
      title: Text(label),
      value: value,
      onChanged: onChanged,
    );
  }
}
