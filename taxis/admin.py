from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AppUser, Taxi, TaxiRoute, Ride, RideDestination,
    WhatsAppConversation, WhatsAppMessage, WhatsAppStats, WebPushSubscription,
    FCMToken, Organization, PriceNegotiation, DriverApp
)



class AppUserAdmin(UserAdmin):
    # Mostrar en la lista del panel
    list_display = (
        'username', 'first_name', 'last_name', 'email',
        'role', 'organization', 'is_active', 'is_staff'
    )

    # Filtros laterales
    list_filter = ('role', 'organization', 'is_active', 'is_staff')

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
        ('Organización y Rol', {
            'fields': ('organization', 'role')
        }),
        ('Conductor (solo si role=driver)', {
            'fields': ('driver_number', 'driver_status', 'approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Permisos', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
    )

    # Campos al agregar un nuevo usuario
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'password1', 'password2',
                'first_name', 'last_name', 'email',
                'phone_number', 'organization', 'role'
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
# FIREBASE CLOUD MESSAGING (FCM)
# ============================================

@admin.register(FCMToken)
class FCMTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'token_preview', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'token', 'device_id')
    readonly_fields = ('created_at', 'updated_at')
    
    def token_preview(self, obj):
        return f"{obj.token[:30]}..."
    token_preview.short_description = 'Token'


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
    list_display = ('user', 'created_at', 'subscription_preview')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'subscription_info')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información de Suscripción', {
            'fields': ('subscription_info', 'created_at')
        }),
    )
    
    def subscription_preview(self, obj):
        """Mostrar preview de la suscripción"""
        if obj.subscription_info:
            endpoint = obj.subscription_info.get('endpoint', '')
            if endpoint:
                return endpoint[:50] + '...' if len(endpoint) > 50 else endpoint
        return '-'
    subscription_preview.short_description = 'Endpoint'
    
    def has_add_permission(self, request):
        # No permitir agregar manualmente
        return False


# ============================================
# ADMIN DE ORGANIZATION (FASE 3)
# ============================================

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'plan',
        'commission_rate',
        'max_drivers',
        'status',
        'created_at'
    )
    list_filter = ('plan', 'status', 'created_at')
    search_fields = ('name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'description', 'logo', 'primary_color', 'secondary_color')
        }),
        ('Plan y Comisiones', {
            'fields': ('plan', 'status', 'commission_rate', 'max_drivers', 'monthly_fee')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'address', 'city', 'country')
        }),
        ('Facturación', {
            'fields': ('billing_address', 'tax_id', 'billing_email')
        }),
        ('Fechas', {
            'fields': ('trial_ends_at', 'subscription_starts_at', 'subscription_ends_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# ADMIN DE INVOICE (FASE 3)
# ============================================
# COMENTADO: El modelo Invoice aún no está implementado

# @admin.register(Invoice)
# class InvoiceAdmin(admin.ModelAdmin):
#     list_display = (
#         'invoice_number',
#         'organization',
#         'amount',
#         'status',
#         'issue_date',
#         'due_date',
#         'paid_date'
#     )
#     list_filter = ('status', 'issue_date', 'due_date')
#     search_fields = ('invoice_number', 'organization__name')
#     readonly_fields = ('invoice_number', 'created_at', 'updated_at')
#     
#     fieldsets = (
#         ('Información de la Factura', {
#             'fields': ('invoice_number', 'organization', 'period_start', 'period_end')
#         }),
#         ('Montos', {
#             'fields': ('amount', 'tax_amount', 'total_amount')
#         }),
#         ('Fechas', {
#             'fields': ('issue_date', 'due_date', 'paid_date')
#         }),
#         ('Estado', {
#             'fields': ('status', 'notes', 'created_at', 'updated_at')
#         }),
#     )
#     
#     def has_add_permission(self, request):
#         # Las facturas se crean desde el panel personalizado
#         return False


# ============================================
# ADMIN DE NEGOCIACIÓN DE PRECIOS
# ============================================

@admin.register(PriceNegotiation)
class PriceNegotiationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer',
        'organization',
        'origin_short',
        'destination_short',
        'proposed_price',
        'counter_offer_price',
        'final_price',
        'status',
        'created_at'
    )
    
    list_filter = ('status', 'organization', 'created_at')
    search_fields = ('customer__username', 'customer__first_name', 'customer__last_name', 'origin', 'destination')
    readonly_fields = ('created_at', 'updated_at', 'ride')
    
    fieldsets = (
        ('Cliente', {
            'fields': ('customer', 'organization')
        }),
        ('Detalles del Viaje', {
            'fields': (
                'origin', 'origin_latitude', 'origin_longitude',
                'destination', 'destination_latitude', 'destination_longitude'
            )
        }),
        ('Precios', {
            'fields': ('suggested_price', 'proposed_price', 'counter_offer_price', 'final_price')
        }),
        ('Estado', {
            'fields': ('status', 'responded_by', 'response_message')
        }),
        ('Carrera Creada', {
            'fields': ('ride',),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def origin_short(self, obj):
        return obj.origin[:50] + '...' if len(obj.origin) > 50 else obj.origin
    origin_short.short_description = 'Origen'
    
    def destination_short(self, obj):
        return obj.destination[:50] + '...' if len(obj.destination) > 50 else obj.destination
    destination_short.short_description = 'Destino'
    
    def has_add_permission(self, request):
        # Las negociaciones se crean desde el frontend
        return False


# ============================================
# ADMIN DE APLICACIÓN MÓVIL PARA CONDUCTORES
# ============================================

@admin.register(DriverApp)
class DriverAppAdmin(admin.ModelAdmin):
    list_display = (
        'version',
        'is_latest',
        'is_active',
        'file_size_display',
        'downloads_count',
        'min_android_version',
        'uploaded_by',
        'created_at'
    )
    
    list_filter = ('is_active', 'is_latest', 'created_at')
    search_fields = ('version', 'release_notes')
    readonly_fields = ('file_size', 'downloads_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Información de la Versión', {
            'fields': ('version', 'min_android_version', 'release_notes')
        }),
        ('Archivo APK', {
            'fields': ('apk_file', 'file_size')
        }),
        ('Estado', {
            'fields': ('is_active', 'is_latest')
        }),
        ('Estadísticas', {
            'fields': ('downloads_count', 'uploaded_by'),
            'classes': ('collapse',)
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Muestra el tamaño del archivo en MB"""
        return f"{obj.get_file_size_mb()} MB"
    file_size_display.short_description = 'Tamaño'
    
    def save_model(self, request, obj, form, change):
        """Asigna el usuario que sube el APK"""
        if not change:  # Solo al crear
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# Register your models here.
