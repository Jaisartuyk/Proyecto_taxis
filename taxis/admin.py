from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AppUser, Taxi, TaxiRoute, Ride, RideDestination,
    WhatsAppConversation, WhatsAppMessage, WhatsAppStats, WebPushSubscription
)



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


# ============================================
# ADMIN DE WHATSAPP
# ============================================

class WhatsAppMessageInline(admin.TabularInline):
    """Mensajes inline en la conversación"""
    model = WhatsAppMessage
    extra = 0
    readonly_fields = ('direction', 'message_type', 'content', 'created_at', 'delivered', 'read')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = (
        'phone_number',
        'name',
        'user',
        'status',
        'state',
        'ride',
        'message_count',
        'last_message_at',
        'created_at'
    )
    list_filter = ('status', 'state', 'created_at', 'last_message_at')
    search_fields = ('phone_number', 'name', 'user__username')
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')
    inlines = [WhatsAppMessageInline]
    
    fieldsets = (
        ('Información del Contacto', {
            'fields': ('phone_number', 'name', 'user')
        }),
        ('Estado de la Conversación', {
            'fields': ('status', 'state', 'data')
        }),
        ('Carrera Asociada', {
            'fields': ('ride',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Mensajes'


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = (
        'get_phone_number',
        'direction_icon',
        'message_type',
        'content_preview',
        'delivered',
        'read',
        'created_at'
    )
    list_filter = ('direction', 'message_type', 'delivered', 'read', 'created_at')
    search_fields = ('conversation__phone_number', 'content')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Conversación', {
            'fields': ('conversation',)
        }),
        ('Mensaje', {
            'fields': ('direction', 'message_type', 'content', 'metadata')
        }),
        ('Estado', {
            'fields': ('message_id', 'delivered', 'read', 'created_at')
        }),
    )
    
    def get_phone_number(self, obj):
        return obj.conversation.phone_number
    get_phone_number.short_description = 'Teléfono'
    
    def direction_icon(self, obj):
        return '📥 Entrante' if obj.direction == 'incoming' else '📤 Saliente'
    direction_icon.short_description = 'Dirección'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Contenido'


@admin.register(WhatsAppStats)
class WhatsAppStatsAdmin(admin.ModelAdmin):
    list_display = (
        'date',
        'total_messages',
        'incoming_messages',
        'outgoing_messages',
        'new_conversations',
        'active_conversations',
        'rides_requested',
        'rides_completed'
    )
    list_filter = ('date',)
    readonly_fields = ('date',)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False



# ============================================
# Web Push Subscriptions Admin
# ============================================

@admin.register(WebPushSubscription)
class WebPushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'browser', 'created_at')
    list_filter = ('created_at', 'browser')
    search_fields = ('user__username', 'user__email', 'browser')
    readonly_fields = ('created_at', 'subscription_info')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información de Suscripción', {
            'fields': ('subscription_info', 'browser', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        # No permitir agregar manualmente
        return False


# Register your models here.
