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

class TaxiForm(forms.ModelForm):
    class Meta:
        model = Taxi
        fields = ['plate_number', 'vehicle_description', 'latitude', 'longitude']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
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