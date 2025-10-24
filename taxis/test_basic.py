"""
Tests básicos para el sistema de taxis
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import AppUser, Taxi, Ride, Rating
from .whatsapp_agent_ai import whatsapp_agent_ai
from .ai_assistant_simple import simple_ai_assistant

User = get_user_model()


class UserModelTest(TestCase):
    """Tests para el modelo de usuario"""
    
    def setUp(self):
        self.user = AppUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='customer',
            phone_number='+573001234567'
        )
    
    def test_user_creation(self):
        """Test creación de usuario"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'customer')
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_user_str_representation(self):
        """Test representación string del usuario"""
        expected = 'Test User (customer)'
        self.assertEqual(str(self.user), expected)


class TaxiModelTest(TestCase):
    """Tests para el modelo de taxi"""
    
    def setUp(self):
        self.driver = AppUser.objects.create_user(
            username='driver',
            password='testpass123',
            first_name='Driver',
            last_name='Test',
            role='driver',
            phone_number='+573001234568'
        )
        self.taxi = Taxi.objects.create(
            user=self.driver,
            plate_number='ABC123',
            vehicle_description='Toyota Corolla 2020',
            latitude=4.6097,
            longitude=-74.0817
        )
    
    def test_taxi_creation(self):
        """Test creación de taxi"""
        self.assertEqual(self.taxi.plate_number, 'ABC123')
        self.assertEqual(self.taxi.user, self.driver)
    
    def test_taxi_str_representation(self):
        """Test representación string del taxi"""
        expected = 'ABC123 - Driver Test'
        self.assertEqual(str(self.taxi), expected)


class RideModelTest(TestCase):
    """Tests para el modelo de carrera"""
    
    def setUp(self):
        self.customer = AppUser.objects.create_user(
            username='customer',
            password='testpass123',
            first_name='Customer',
            last_name='Test',
            role='customer',
            phone_number='+573001234567'
        )
        self.driver = AppUser.objects.create_user(
            username='driver',
            password='testpass123',
            first_name='Driver',
            last_name='Test',
            role='driver',
            phone_number='+573001234568'
        )
        self.ride = Ride.objects.create(
            customer=self.customer,
            driver=self.driver,
            origin='Calle 50 #25-30',
            origin_latitude=4.6097,
            origin_longitude=-74.0817,
            price=15000.00,
            status='requested'
        )
    
    def test_ride_creation(self):
        """Test creación de carrera"""
        self.assertEqual(self.ride.customer, self.customer)
        self.assertEqual(self.ride.driver, self.driver)
        self.assertEqual(self.ride.status, 'requested')
    
    def test_ride_str_representation(self):
        """Test representación string de la carrera"""
        expected = 'Carrera de customer desde Calle 50 #25-30 (Solicitada)'
        self.assertEqual(str(self.ride), expected)


class RatingModelTest(TestCase):
    """Tests para el modelo de calificación"""
    
    def setUp(self):
        self.customer = AppUser.objects.create_user(
            username='customer',
            password='testpass123',
            first_name='Customer',
            last_name='Test',
            role='customer',
            phone_number='+573001234567'
        )
        self.driver = AppUser.objects.create_user(
            username='driver',
            password='testpass123',
            first_name='Driver',
            last_name='Test',
            role='driver',
            phone_number='+573001234568'
        )
        self.ride = Ride.objects.create(
            customer=self.customer,
            driver=self.driver,
            origin='Calle 50 #25-30',
            status='completed'
        )
        self.rating = Rating.objects.create(
            ride=self.ride,
            rater=self.customer,
            rated=self.driver,
            rating=5,
            comment='Excelente servicio'
        )
    
    def test_rating_creation(self):
        """Test creación de calificación"""
        self.assertEqual(self.rating.rating, 5)
        self.assertEqual(self.rating.comment, 'Excelente servicio')
        self.assertEqual(self.rating.stars_display, '★★★★★')
    
    def test_rating_str_representation(self):
        """Test representación string de la calificación"""
        expected = 'Customer Test calificó a Driver Test con 5 estrellas'
        self.assertEqual(str(self.rating), expected)


class ViewsTest(TestCase):
    """Tests para las vistas"""
    
    def setUp(self):
        self.client = Client()
        self.user = AppUser.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='customer',
            phone_number='+573001234567'
        )
    
    def test_home_view(self):
        """Test vista home"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_required_redirect(self):
        """Test redirección cuando se requiere login"""
        response = self.client.get('/customer-dashboard/')
        self.assertRedirects(response, '/login/?next=/customer-dashboard/')
    
    def test_customer_dashboard_authenticated(self):
        """Test dashboard de cliente autenticado"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/customer-dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_driver_dashboard_wrong_role(self):
        """Test dashboard de conductor con rol incorrecto"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/driver-dashboard/')
        self.assertRedirects(response, '/login/')


class WhatsAppAgentTest(TestCase):
    """Tests para el agente de WhatsApp"""
    
    def test_simple_ai_assistant_initialization(self):
        """Test inicialización del asistente simple"""
        self.assertIsNotNone(simple_ai_assistant)
        self.assertIsInstance(simple_ai_assistant.saludos, list)
        self.assertTrue(len(simple_ai_assistant.saludos) > 0)
    
    def test_simple_ai_greeting_response(self):
        """Test respuesta de saludo del asistente"""
        response = simple_ai_assistant.generar_respuesta_contextual(
            mensaje_usuario="Hola",
            estado_conversacion="inicio"
        )
        
        self.assertIn('respuesta', response)
        self.assertIn('accion', response)
        self.assertIn('datos_extraidos', response)
        self.assertIn('Hola', response['respuesta'])
    
    def test_simple_ai_taxi_request_response(self):
        """Test respuesta de solicitud de taxi"""
        response = simple_ai_assistant.generar_respuesta_contextual(
            mensaje_usuario="Necesito un taxi",
            estado_conversacion="inicio"
        )
        
        self.assertEqual(response['accion'], 'solicitar_origen')
        self.assertIn('taxi', response['respuesta'].lower())
    
    def test_simple_ai_help_response(self):
        """Test respuesta de ayuda"""
        response = simple_ai_assistant.generar_respuesta_contextual(
            mensaje_usuario="Ayuda",
            estado_conversacion="inicio"
        )
        
        self.assertEqual(response['accion'], 'mostrar_ayuda')
        self.assertIn('ayuda', response['respuesta'].lower())


class APITest(TestCase):
    """Tests para la API"""
    
    def setUp(self):
        self.client = Client()
        self.user = AppUser.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='customer',
            phone_number='+573001234567'
        )
    
    def test_whatsapp_webhook_get(self):
        """Test webhook de WhatsApp con GET"""
        response = self.client.get('/webhook/whatsapp/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('WhatsApp Webhook is active', data['message'])
    
    def test_whatsapp_webhook_post_invalid_json(self):
        """Test webhook de WhatsApp con JSON inválido"""
        response = self.client.post(
            '/webhook/whatsapp/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_whatsapp_send_notification_missing_data(self):
        """Test envío de notificación con datos faltantes"""
        response = self.client.post(
            '/api/whatsapp/send-notification/',
            data={'phone_number': '+573001234567'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)


class IntegrationTest(TestCase):
    """Tests de integración"""
    
    def setUp(self):
        self.client = Client()
        self.customer = AppUser.objects.create_user(
            username='customer',
            password='testpass123',
            first_name='Customer',
            last_name='Test',
            role='customer',
            phone_number='+573001234567'
        )
        self.driver = AppUser.objects.create_user(
            username='driver',
            password='testpass123',
            first_name='Driver',
            last_name='Test',
            role='driver',
            phone_number='+573001234568'
        )
        self.taxi = Taxi.objects.create(
            user=self.driver,
            plate_number='ABC123',
            vehicle_description='Toyota Corolla 2020'
        )
    
    def test_complete_ride_flow(self):
        """Test flujo completo de una carrera"""
        # 1. Cliente solicita carrera
        self.client.login(username='customer', password='testpass123')
        
        ride_data = {
            'origin': 'Calle 50 #25-30',
            'origin_latitude': '4.6097',
            'origin_longitude': '-74.0817',
            'price': '15000',
            'destinations[]': ['Aeropuerto El Dorado'],
            'destination_coords[]': ['4.7016,-74.1469']
        }
        
        response = self.client.post('/request-ride/', ride_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # 2. Verificar que la carrera se creó
        ride = Ride.objects.filter(customer=self.customer).first()
        self.assertIsNotNone(ride)
        self.assertEqual(ride.status, 'requested')
        
        # 3. Conductor acepta carrera
        self.client.login(username='driver', password='testpass123')
        
        response = self.client.post(f'/update-ride-status/{ride.id}/', {
            'status': 'in_progress'
        })
        self.assertEqual(response.status_code, 200)
        
        # 4. Verificar que la carrera fue aceptada
        ride.refresh_from_db()
        self.assertEqual(ride.status, 'in_progress')
        self.assertEqual(ride.driver, self.driver)
    
    def test_rating_system(self):
        """Test sistema de calificaciones"""
        # Crear carrera completada
        ride = Ride.objects.create(
            customer=self.customer,
            driver=self.driver,
            origin='Calle 50 #25-30',
            status='completed'
        )
        
        # Cliente califica al conductor
        self.client.login(username='customer', password='testpass123')
        
        response = self.client.post(f'/ride/{ride.id}/rate/', {
            'rating': '5',
            'comment': 'Excelente servicio'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Verificar que la calificación se creó
        rating = Rating.objects.filter(ride=ride, rater=self.customer).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.rating, 5)
        self.assertEqual(rating.comment, 'Excelente servicio')

