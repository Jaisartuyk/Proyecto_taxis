from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AppUser, Taxi, TaxiRoute, Ride, RideDestination



class AppUserAdmin(UserAdmin):
    # Mostrar en la lista del panel
    list_display = (
        'username', 'first_name', 'last_name', 'email',
        'role', 'is_active', 'is_staff', 'telegram_chat_id',
        'last_latitude', 'last_longitude'
    )

    # Filtros laterales
    list_filter = ('role', 'is_active', 'is_staff')

    # Campos buscables
    search_fields = (
        'username', 'first_name', 'last_name', 'email',
        'phone_number', 'telegram_chat_id'
    )

    ordering = ('username',)

    # Campos en la vista de detalle del usuario
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información personal', {
            'fields': (
                'first_name', 'last_name', 'email',
                'phone_number', 'national_id', 'profile_picture',
                'telegram_chat_id', 'last_latitude', 'last_longitude'
            )
        }),
        ('Permisos', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Rol', {
            'fields': ('role',)
        }),
    )

    # Campos al agregar un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'first_name', 'last_name', 'role',
                'email', 'phone_number', 'telegram_chat_id'
            ),
        }),
    )

# Registrar el modelo personalizado
admin.site.register(AppUser, AppUserAdmin)



class TaxiAdmin(admin.ModelAdmin):
    list_display = ('user', 'plate_number', 'vehicle_description', 'latitude', 'longitude', 'updated_at')
    search_fields = ('user__username', 'plate_number', 'vehicle_description')
    list_filter = ('updated_at',)

    fieldsets = (
        (None, {
            'fields': ('user', 'plate_number', 'vehicle_description', 'latitude', 'longitude')
        }),
    )

# Registrar el modelo de Taxi en el panel de administración
admin.site.register(Taxi, TaxiAdmin)

class TaxiRouteAdmin(admin.ModelAdmin):
    list_display = ('taxi', 'is_available', 'get_passengers', 'estimated_arrival_time')  # Columnas visibles
    list_filter = ('is_available',)  # Filtros en el panel lateral
    search_fields = ('taxi__user__username',)  # Campo de búsqueda por taxista

    @admin.display(description='Pasajeros')
    def get_passengers(self, obj):
        return ", ".join([p for p in obj.passengers if p]) or "Sin asignar"

admin.site.register(TaxiRoute, TaxiRouteAdmin)



# Personalización de la visualización de Ride en el Admin
class RideAdmin(admin.ModelAdmin):
    list_display = (
        'customer',
        'driver',
        'origin',
        'origin_latitude',
        'origin_longitude',
        'start_time',
        'end_time',
        'status',
        'price',
        'created_at'
    )
    list_filter = ('status', 'driver', 'customer')
    search_fields = ('customer__username', 'driver__username', 'origin')

admin.site.register(Ride, RideAdmin)

# Personalización de la visualización de RideDestination en el Admin
class RideDestinationAdmin(admin.ModelAdmin):
    list_display = (
        'ride',
        'destination',
        'destination_latitude',
        'destination_longitude',
        'order'
    )
    list_filter = ('ride', 'order')
    search_fields = ('ride__customer__username', 'destination')

admin.site.register(RideDestination, RideDestinationAdmin)



# Register your models here.
