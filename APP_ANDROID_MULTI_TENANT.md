# 📱 App Android Multi-Tenant - Estrategia Completa

## 🎯 VISIÓN: Una App, Múltiples Cooperativas

### **Concepto:**
La misma app Android sirve para TODAS las cooperativas, pero cada conductor ve solo su cooperativa.

---

## 🏗️ ARQUITECTURA DE LA APP

### **Opción 1: Una Sola App Universal (RECOMENDADO)**

```
┌────────────────────────────────────────┐
│   "De Aquí Pa'llá - Conductor"        │
│        (Una sola app en Play Store)    │
└────────────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼────┐ ┌───▼────┐ ┌───▼────┐
│ Taxi Oro │ │Taxi Azul│ │Taxi Rojo│
│ (Logo 1) │ │(Logo 2) │ │(Logo 3)│
└──────────┘ └─────────┘ └─────────┘
```

**Flujo:**
1. Conductor descarga la app
2. Se registra con su cooperativa
3. La app se personaliza automáticamente:
   - Logo de su cooperativa
   - Colores de su cooperativa
   - Nombre de su cooperativa
4. Ve solo carreras de su cooperativa

**Ventajas:**
- ✅ Una sola app para mantener
- ✅ Una sola publicación en Play Store
- ✅ Actualizaciones centralizadas
- ✅ Más fácil de escalar

**Desventajas:**
- ⚠️ Todas las cooperativas comparten el nombre "De Aquí Pa'llá"
- ⚠️ Menos personalización visual

---

### **Opción 2: Apps White-Label Personalizadas**

```
Play Store:
├── "Taxi Oro - Conductor" (Logo Oro)
├── "Taxi Azul - Conductor" (Logo Azul)
└── "Taxi Rojo - Conductor" (Logo Rojo)
```

**Flujo:**
1. Cada cooperativa tiene su propia app
2. Mismo código base, diferente branding
3. Publicación separada en Play Store

**Ventajas:**
- ✅ Branding 100% personalizado
- ✅ Nombre propio en Play Store
- ✅ Logo e icono personalizados
- ✅ Más profesional para cooperativas grandes

**Desventajas:**
- ❌ Múltiples apps para mantener
- ❌ Múltiples publicaciones en Play Store ($25 × N)
- ❌ Actualizaciones más complejas

---

## 🎨 IMPLEMENTACIÓN: Opción 1 (Una Sola App)

### **Cambios en el Backend (Django):**

```python
# models.py
class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    logo_url = models.URLField()
    primary_color = models.CharField(max_length=7)
    secondary_color = models.CharField(max_length=7)
    # ... otros campos

# API para obtener info de la organización
# views.py
@api_view(['GET'])
def get_organization_info(request, org_id):
    org = Organization.objects.get(id=org_id)
    return Response({
        'id': org.id,
        'name': org.name,
        'logo_url': org.logo_url,
        'primary_color': org.primary_color,
        'secondary_color': org.secondary_color,
    })
```

### **Cambios en la App Flutter:**

#### **1. Pantalla de Selección de Cooperativa (Login):**

```dart
// lib/screens/organization_selection_screen.dart
class OrganizationSelectionScreen extends StatefulWidget {
  @override
  _OrganizationSelectionScreenState createState() => _OrganizationSelectionScreenState();
}

class _OrganizationSelectionScreenState extends State<OrganizationSelectionScreen> {
  List<Organization> _organizations = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadOrganizations();
  }

  Future<void> _loadOrganizations() async {
    try {
      final response = await http.get(
        Uri.parse('https://taxis-deaquipalla.up.railway.app/api/organizations/')
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        setState(() {
          _organizations = data.map((json) => Organization.fromJson(json)).toList();
          _loading = false;
        });
      }
    } catch (e) {
      print('Error cargando organizaciones: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Selecciona tu Cooperativa'),
      ),
      body: ListView.builder(
        padding: EdgeInsets.all(16),
        itemCount: _organizations.length,
        itemBuilder: (context, index) {
          final org = _organizations[index];
          return Card(
            margin: EdgeInsets.only(bottom: 16),
            child: ListTile(
              leading: CircleAvatar(
                backgroundImage: NetworkImage(org.logoUrl),
                radius: 30,
              ),
              title: Text(
                org.name,
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              subtitle: Text('${org.driverCount} conductores activos'),
              trailing: Icon(Icons.arrow_forward_ios),
              onTap: () => _selectOrganization(org),
            ),
          );
        },
      ),
    );
  }

  void _selectOrganization(Organization org) async {
    // Guardar organización seleccionada
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('organization_id', org.id);
    await prefs.setString('organization_name', org.name);
    await prefs.setString('organization_logo', org.logoUrl);
    await prefs.setString('primary_color', org.primaryColor);
    
    // Ir a login
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (context) => LoginScreen(organization: org),
      ),
    );
  }
}
```

#### **2. Modelo de Organización:**

```dart
// lib/models/organization.dart
class Organization {
  final int id;
  final String name;
  final String slug;
  final String logoUrl;
  final String primaryColor;
  final String secondaryColor;
  final int driverCount;

  Organization({
    required this.id,
    required this.name,
    required this.slug,
    required this.logoUrl,
    required this.primaryColor,
    required this.secondaryColor,
    required this.driverCount,
  });

  factory Organization.fromJson(Map<String, dynamic> json) {
    return Organization(
      id: json['id'],
      name: json['name'],
      slug: json['slug'],
      logoUrl: json['logo_url'],
      primaryColor: json['primary_color'],
      secondaryColor: json['secondary_color'],
      driverCount: json['driver_count'] ?? 0,
    );
  }
}
```

#### **3. Tema Dinámico:**

```dart
// lib/utils/theme_manager.dart
class ThemeManager {
  static Future<ThemeData> getOrganizationTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final primaryColorHex = prefs.getString('primary_color') ?? '#FFD700';
    final secondaryColorHex = prefs.getString('secondary_color') ?? '#000000';
    
    final primaryColor = Color(int.parse(primaryColorHex.replaceAll('#', '0xFF')));
    final secondaryColor = Color(int.parse(secondaryColorHex.replaceAll('#', '0xFF')));
    
    return ThemeData(
      primaryColor: primaryColor,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryColor,
        secondary: secondaryColor,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: primaryColor,
        foregroundColor: Colors.white,
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: primaryColor,
      ),
    );
  }
}

// lib/main.dart
class MyApp extends StatefulWidget {
  @override
  _MyAppState createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  ThemeData? _theme;

  @override
  void initState() {
    super.initState();
    _loadTheme();
  }

  Future<void> _loadTheme() async {
    final theme = await ThemeManager.getOrganizationTheme();
    setState(() {
      _theme = theme;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_theme == null) {
      return MaterialApp(
        home: Scaffold(
          body: Center(child: CircularProgressIndicator()),
        ),
      );
    }

    return MaterialApp(
      title: 'De Aquí Pa\'llá - Conductor',
      theme: _theme,
      home: SplashScreen(),
    );
  }
}
```

#### **4. Logo Dinámico en AppBar:**

```dart
// lib/widgets/organization_app_bar.dart
class OrganizationAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;

  OrganizationAppBar({required this.title});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<String>(
      future: _getOrganizationLogo(),
      builder: (context, snapshot) {
        return AppBar(
          title: Row(
            children: [
              if (snapshot.hasData)
                CircleAvatar(
                  backgroundImage: NetworkImage(snapshot.data!),
                  radius: 16,
                ),
              SizedBox(width: 8),
              Text(title),
            ],
          ),
        );
      },
    );
  }

  Future<String> _getOrganizationLogo() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('organization_logo') ?? '';
  }

  @override
  Size get preferredSize => Size.fromHeight(kToolbarHeight);
}
```

#### **5. Filtrado de Datos por Organización:**

```dart
// lib/services/ride_service.dart
class RideService {
  static Future<List<Ride>> getAvailableRides() async {
    final prefs = await SharedPreferences.getInstance();
    final orgId = prefs.getInt('organization_id');
    
    final response = await http.get(
      Uri.parse('https://taxis-deaquipalla.up.railway.app/api/rides/?organization_id=$orgId&status=requested')
    );
    
    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Ride.fromJson(json)).toList();
    }
    
    return [];
  }
}
```

---

## 📱 FLUJO COMPLETO DE LA APP

### **Primera Vez (Nuevo Conductor):**

```
1. Abrir App
   ↓
2. Pantalla de Bienvenida
   ↓
3. "Selecciona tu Cooperativa"
   - Lista de cooperativas con logos
   ↓
4. Selecciona "Taxi Oro"
   - App se personaliza con colores/logo de Taxi Oro
   ↓
5. Pantalla de Registro
   - Formulario con branding de Taxi Oro
   ↓
6. Registro Exitoso
   - Estado: Pendiente de Aprobación
   ↓
7. Espera Aprobación del Admin
   ↓
8. Admin Aprueba
   - Notificación push al conductor
   ↓
9. Conductor puede usar la app
```

### **Uso Diario (Conductor Aprobado):**

```
1. Abrir App
   - Logo de su cooperativa en splash screen
   ↓
2. Login
   - Colores de su cooperativa
   ↓
3. Dashboard
   - Ve solo carreras de su cooperativa
   - Chat con su central
   - Audio con su central
   ↓
4. Acepta Carrera
   - Solo de su cooperativa
   ↓
5. Completa Carrera
   - Comisión según plan de su cooperativa
```

---

## 🔄 SINCRONIZACIÓN Y CACHÉ

```dart
// lib/services/organization_service.dart
class OrganizationService {
  static Future<void> syncOrganizationData() async {
    final prefs = await SharedPreferences.getInstance();
    final orgId = prefs.getInt('organization_id');
    
    if (orgId == null) return;
    
    try {
      final response = await http.get(
        Uri.parse('https://taxis-deaquipalla.up.railway.app/api/organizations/$orgId/')
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Actualizar datos en caché
        await prefs.setString('organization_name', data['name']);
        await prefs.setString('organization_logo', data['logo_url']);
        await prefs.setString('primary_color', data['primary_color']);
        await prefs.setString('secondary_color', data['secondary_color']);
        
        print('✅ Datos de organización sincronizados');
      }
    } catch (e) {
      print('❌ Error sincronizando organización: $e');
    }
  }
}
```

---

## 🎨 PERSONALIZACIÓN VISUAL

### **Elementos que se Personalizan:**

1. **Logo:**
   - Splash screen
   - AppBar
   - Drawer/Menu lateral
   - Pantalla de login

2. **Colores:**
   - Color primario (botones, AppBar)
   - Color secundario (acentos)
   - Color de fondo

3. **Textos:**
   - Nombre de la cooperativa en títulos
   - Mensajes personalizados

### **Ejemplo Visual:**

```
┌─────────────────────────────────────┐
│  [Logo Taxi Oro]  TAXI ORO          │ ← AppBar con logo y nombre
├─────────────────────────────────────┤
│                                     │
│  Bienvenido a TAXI ORO              │ ← Nombre personalizado
│                                     │
│  [Carreras Disponibles: 5]          │ ← Solo de su cooperativa
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📍 Av. 9 de Octubre         │   │
│  │ 📍 Mall del Sol             │   │
│  │ 💰 $5.50                    │   │
│  │ [ACEPTAR] ← Color dorado    │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

## 🚀 PLAN DE IMPLEMENTACIÓN

### **Semana 1: Backend Multi-Tenant**
- [ ] Crear modelo `Organization`
- [ ] API para listar organizaciones
- [ ] API para obtener info de organización
- [ ] Filtrar carreras por organización

### **Semana 2: App - Selección de Cooperativa**
- [ ] Pantalla de selección de cooperativa
- [ ] Guardar organización en SharedPreferences
- [ ] Modificar login para incluir organización

### **Semana 3: App - Personalización Visual**
- [ ] Tema dinámico basado en colores
- [ ] Logo dinámico en AppBar
- [ ] Splash screen con logo de cooperativa
- [ ] Caché de datos de organización

### **Semana 4: App - Filtrado de Datos**
- [ ] Filtrar carreras por organización
- [ ] Filtrar conductores en chat
- [ ] Filtrar audio por organización
- [ ] Testing completo

---

## 💰 CONSIDERACIONES DE COSTOS

### **Opción 1: Una Sola App**
- **Costo inicial:** $25 (Google Play Developer)
- **Costo mensual:** $0
- **Actualizaciones:** Gratis

### **Opción 2: Apps White-Label**
- **Costo inicial:** $25 × N cooperativas
- **Costo mensual:** $0
- **Actualizaciones:** Más trabajo

**Recomendación:** Empezar con Opción 1, migrar a Opción 2 cuando tengas 50+ cooperativas.

---

## 🎯 VENTAJAS DEL MODELO MULTI-TENANT EN APP

1. ✅ **Una sola app para mantener**
2. ✅ **Actualizaciones centralizadas**
3. ✅ **Menor costo de desarrollo**
4. ✅ **Más fácil de escalar**
5. ✅ **Personalización suficiente**

---

## 📊 RESUMEN EJECUTIVO

| Aspecto | Solución |
|---------|----------|
| **Arquitectura** | Una app, múltiples cooperativas |
| **Personalización** | Logo, colores, nombre |
| **Datos** | Filtrados por organización |
| **Costo** | $25 una sola vez |
| **Mantenimiento** | Centralizado |
| **Escalabilidad** | Ilimitada |

---

## ✅ RESPUESTA A TU PREGUNTA:

**SÍ, la app Android está incluida en el Mes 1 de implementación multi-tenant.**

Los cambios son:
1. ✅ Pantalla de selección de cooperativa
2. ✅ Personalización visual dinámica
3. ✅ Filtrado de datos por organización
4. ✅ Caché de información

**No es complejo, es una extensión natural del backend multi-tenant.** 🚀

¿Empezamos con la implementación? 💪
