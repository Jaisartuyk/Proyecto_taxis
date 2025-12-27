from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import AppUser, Taxi, TaxiRoute, Ride
from django.contrib.auth import get_user_model

User = get_user_model()

class RideFilterForm(forms.Form):
    STATUS_CHOICES = [('', 'Todos')] + Ride.STATUS_CHOICES
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, label="Estado")
    driver = forms.ModelChoiceField(
        queryset=User.objects.filter(role='driver'),
        required=False,
        label="Conductor",
    )
    start_date = forms.DateField(required=False, label="Fecha inicio", widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, label="Fecha fin", widget=forms.DateInput(attrs={'type': 'date'}))



class DriverRegistrationForm(UserCreationForm):
    class Meta:
        model = AppUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'phone_number', 'national_id', 'profile_picture', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = 'driver'  # Rol predeterminado para conductores
        self.fields['role'].widget = forms.HiddenInput()  # Escondemos el campo del formulario

class CustomerRegistrationForm(UserCreationForm):
    class Meta:
        model = AppUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'phone_number', 'profile_picture', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].initial = 'customer'  # Rol predeterminado para clientes
        self.fields['role'].widget = forms.HiddenInput()  # Escondemos el campo del formulario

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = AppUser
        fields = ['first_name', 'last_name', 'phone_number', 'national_id', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class DriverProfileForm(forms.ModelForm):
    class Meta:
        model = AppUser
        fields = ['first_name', 'last_name', 'phone_number', 'national_id', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class TaxiRouteForm(forms.ModelForm):
    class Meta:
        model = TaxiRoute
        fields = ['is_available', 'passenger_1', 'passenger_2', 'passenger_3', 'passenger_4']
        widgets = {
            'passenger_1': forms.TextInput(attrs={'class': 'form-control', 'id': 'passenger_1'}),
            'passenger_2': forms.TextInput(attrs={'class': 'form-control', 'id': 'passenger_2'}),
            'passenger_3': forms.TextInput(attrs={'class': 'form-control', 'id': 'passenger_3'}),
            'passenger_4': forms.TextInput(attrs={'class': 'form-control', 'id': 'passenger_4'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TaxiForm(forms.ModelForm):
    class Meta:
        model = Taxi
        fields = ['plate_number', 'vehicle_description', 'latitude', 'longitude']
        widgets = {
            'latitude': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            }),
            'longitude': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            }),
        }

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']  # Asegúrate de incluir 'email'
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),  # Opcional: Solo lectura
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }

# ============================================
# FORMULARIOS FASE 3: PANEL DE ADMINISTRACIÓN
# ============================================

from .models import Organization, Invoice

class OrganizationForm(forms.ModelForm):
    """Formulario para crear/editar cooperativas"""
    class Meta:
        model = Organization
        fields = [
            'name', 'slug', 'description',
            'logo', 'primary_color', 'secondary_color',
            'phone', 'email', 'address', 'city',
            'plan', 'max_drivers', 'monthly_fee', 'commission_rate',
            'billing_email', 'billing_address', 'tax_id',
            'welcome_message'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'billing_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'welcome_message': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'plan': forms.Select(attrs={'class': 'form-control'}),
            'max_drivers': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'billing_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DriverApprovalForm(forms.ModelForm):
    """Formulario para aprobar/rechazar conductores"""
    approval_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label="Notas de aprobación"
    )
    
    class Meta:
        model = AppUser
        fields = ['driver_status', 'driver_number']
        widgets = {
            'driver_status': forms.Select(attrs={'class': 'form-control'}),
            'driver_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class InvoiceForm(forms.ModelForm):
    """Formulario para crear facturas"""
    class Meta:
        model = Invoice
        fields = [
            'organization', 'period_start', 'period_end',
            'subscription_fee', 'commission_amount',
            'due_date', 'notes'
        ]
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'period_start': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'period_end': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'subscription_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'commission_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

