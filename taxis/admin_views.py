"""
Vistas del Panel de Administración (Fase 3)
Panel completo para gestionar cooperativas, conductores, reportes y facturación
"""
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, datetime
from decimal import Decimal

from .models import Organization, AppUser, Ride, InvitationCode  # Invoice no existe aún
from .forms import OrganizationForm, DriverApprovalForm  # InvoiceForm no existe aún
from .decorators import superadmin_required, organization_admin_required
from django.utils.decorators import method_decorator
from django.views import View


# ============================================
# DASHBOARD PRINCIPAL
# ============================================

@method_decorator(superadmin_required, name='dispatch')
class SuperAdminDashboardView(TemplateView):
    """Dashboard principal del super admin con estadísticas globales"""
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Valores por defecto
        context['total_organizations'] = 0
        context['total_drivers'] = 0
        context['pending_drivers'] = 0
        context['rides_this_month'] = 0
        context['revenue_this_month'] = Decimal('0.00')
        context['commission_this_month'] = Decimal('0.00')
        context['recent_organizations'] = []
        context['pending_drivers_list'] = []
        context['pending_invoices'] = []
        context['stats_by_plan'] = []
        
        try:
            # Estadísticas globales
            try:
                context['total_organizations'] = Organization.objects.filter(is_active=True).count()
            except:
                context['total_organizations'] = Organization.objects.count()
            
            try:
                context['total_drivers'] = AppUser.objects.filter(
                    role='driver',
                    driver_status='approved'
                ).count()
            except:
                context['total_drivers'] = AppUser.objects.filter(role='driver').count()
            
            try:
                context['pending_drivers'] = AppUser.objects.filter(
                    role='driver',
                    driver_status='pending'
                ).count()
            except:
                context['pending_drivers'] = 0
            
            # Carreras del mes actual
            now = timezone.now()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            rides_this_month = Ride.objects.filter(
                created_at__gte=current_month_start,
                status='completed'
            )
            
            context['rides_this_month'] = rides_this_month.count()
            
            # Ingresos del mes
            try:
                revenue_data = rides_this_month.aggregate(
                    total=Sum('price'),
                    commission=Sum('commission_amount')
                )
                context['revenue_this_month'] = revenue_data['total'] or Decimal('0.00')
                context['commission_this_month'] = revenue_data['commission'] or Decimal('0.00')
            except:
                revenue_data = rides_this_month.aggregate(total=Sum('price'))
                context['revenue_this_month'] = revenue_data['total'] or Decimal('0.00')
                context['commission_this_month'] = Decimal('0.00')
            
            # Cooperativas recientes
            context['recent_organizations'] = Organization.objects.all().order_by('-created_at')[:5]
            
            # Conductores pendientes de aprobación
            try:
                context['pending_drivers_list'] = AppUser.objects.filter(
                    role='driver',
                    driver_status='pending'
                )[:10]
            except:
                context['pending_drivers_list'] = []
            
            # Facturas pendientes (Invoice no existe aún)
            # try:
            #     context['pending_invoices'] = Invoice.objects.filter(
            #         status='pending'
            #     ).select_related('organization')[:5]
            # except:
            context['pending_invoices'] = []
            
            # Estadísticas por plan
            try:
                context['stats_by_plan'] = Organization.objects.filter(
                    is_active=True
                ).values('plan').annotate(
                    count=Count('id')
                )
            except:
                context['stats_by_plan'] = Organization.objects.values('plan').annotate(
                    count=Count('id')
                )
        
        except Exception as e:
            # Si hay cualquier error, registrarlo pero no romper la página
            print(f"❌ Error en SuperAdminDashboardView: {e}")
            import traceback
            traceback.print_exc()
        
        return context


# ============================================
# GESTIÓN DE COOPERATIVAS
# ============================================

@method_decorator(organization_admin_required, name='dispatch')
class OrganizationListView(ListView):
    """Lista de todas las cooperativas"""
    model = Organization
    template_name = 'admin/organizations/list.html'
    context_object_name = 'organizations'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Organization.objects.all().annotate(
            driver_count=Count('users', filter=Q(users__role='driver')),
            active_rides=Count('rides', filter=Q(rides__status__in=['requested', 'accepted', 'in_progress']))
        )
        
        # Filtros
        plan = self.request.GET.get('plan')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if plan:
            queryset = queryset.filter(plan=plan)
        
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'suspended':
            queryset = queryset.filter(is_active=False)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(slug__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plan_choices'] = Organization.PLAN_CHOICES
        return context


@method_decorator(organization_admin_required, name='dispatch')
class OrganizationCreateView(CreateView):
    """Crear nueva cooperativa"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'admin/organizations/create.html'
    success_url = reverse_lazy('admin_organizations')
    
    def form_valid(self, form):
        messages.success(self.request, f'Cooperativa "{form.instance.name}" creada exitosamente.')
        return super().form_valid(form)


@method_decorator(organization_admin_required, name='dispatch')
class OrganizationUpdateView(UpdateView):
    """Editar cooperativa existente"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'admin/organizations/edit.html'
    success_url = reverse_lazy('admin_organizations')
    
    def form_valid(self, form):
        messages.success(self.request, f'Cooperativa "{form.instance.name}" actualizada exitosamente.')
        return super().form_valid(form)


@method_decorator(organization_admin_required, name='dispatch')
class OrganizationDetailView(DetailView):
    """Ver detalles de una cooperativa"""
    model = Organization
    template_name = 'admin/organizations/detail.html'
    context_object_name = 'organization'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.object
        
        # Estadísticas de la cooperativa
        context['driver_count'] = org.users.filter(role='driver').count()
        context['approved_drivers'] = org.users.filter(role='driver', driver_status='approved').count()
        context['pending_drivers'] = org.users.filter(role='driver', driver_status='pending').count()
        
        # Carreras
        context['total_rides'] = org.rides.count()
        context['completed_rides'] = org.rides.filter(status='completed').count()
        context['active_rides'] = org.rides.filter(status__in=['requested', 'accepted', 'in_progress']).count()
        
        # Ingresos
        revenue_data = org.rides.filter(status='completed').aggregate(
            total=Sum('price'),
            commission=Sum('commission_amount')
        )
        context['total_revenue'] = revenue_data['total'] or Decimal('0.00')
        context['total_commission'] = revenue_data['commission'] or Decimal('0.00')
        
        # Facturas
        context['invoices'] = org.invoices.all().order_by('-issued_at')[:10]
        context['pending_invoices_count'] = org.invoices.filter(status='pending').count()
        
        # Conductores recientes
        context['recent_drivers'] = org.users.filter(role='driver').order_by('-date_joined')[:10]
        
        return context


@method_decorator(organization_admin_required, name='dispatch')
class OrganizationSuspendView(TemplateView):
    """Suspender/reactivar cooperativa"""
    
    def post(self, request, pk):
        org = get_object_or_404(Organization, pk=pk)
        action = request.POST.get('action')
        
        if action == 'suspend':
            org.is_active = False
            org.suspended_at = timezone.now()
            org.suspension_reason = request.POST.get('reason', '')
            org.save()
            messages.success(request, f'Cooperativa "{org.name}" suspendida.')
        
        elif action == 'reactivate':
            org.is_active = True
            org.suspended_at = None
            org.suspension_reason = ''
            org.save()
            messages.success(request, f'Cooperativa "{org.name}" reactivada.')
        
        return redirect('admin_organization_detail', pk=pk)


# ============================================
# GESTIÓN DE CONDUCTORES
# ============================================

@method_decorator(organization_admin_required, name='dispatch')
class DriverApprovalListView(ListView):
    """Lista de conductores pendientes de aprobación"""
    model = AppUser
    template_name = 'admin/drivers/approval_list.html'
    context_object_name = 'drivers'
    paginate_by = 20
    
    def get_queryset(self):
        status = self.request.GET.get('status', 'pending')
        queryset = AppUser.objects.filter(role='driver').select_related('organization')
        
        if status:
            queryset = queryset.filter(driver_status=status)
        
        return queryset.order_by('-date_joined')


@method_decorator(organization_admin_required, name='dispatch')
class DriverApproveView(TemplateView):
    """Aprobar conductor"""
    
    def post(self, request, pk):
        driver = get_object_or_404(AppUser, pk=pk, role='driver')
        form = DriverApprovalForm(request.POST, instance=driver)
        
        if form.is_valid():
            driver = form.save(commit=False)
            driver.driver_status = 'approved'
            driver.approved_by = request.user
            driver.approved_at = timezone.now()
            driver.save()
            
            messages.success(request, f'Conductor {driver.get_full_name()} aprobado exitosamente.')
        
        return redirect('admin_drivers_pending')


@method_decorator(organization_admin_required, name='dispatch')
class DriverRejectView(TemplateView):
    """Rechazar conductor"""
    
    def post(self, request, pk):
        driver = get_object_or_404(AppUser, pk=pk, role='driver')
        reason = request.POST.get('reason', '')
        
        driver.driver_status = 'rejected'
        driver.save()
        
        # Aquí se podría enviar un email o notificación al conductor
        
        messages.warning(request, f'Conductor {driver.get_full_name()} rechazado.')
        return redirect('admin_drivers_pending')


# ============================================
# GESTIÓN DE CLIENTES
# ============================================

@method_decorator(organization_admin_required, name='dispatch')
class CustomerListView(ListView):
    """Lista de clientes de la organización"""
    model = AppUser
    template_name = 'admin/customers/list.html'
    context_object_name = 'customers'
    paginate_by = 20
    
    def get_queryset(self):
        # ✅ MULTI-TENANT: Filtrar clientes por organización
        if self.request.user.is_superuser:
            # Super admin ve TODOS los clientes
            queryset = AppUser.objects.filter(role='customer')
        elif self.request.user.organization:
            # Admin ve solo clientes de SU organización
            queryset = AppUser.objects.filter(role='customer', organization=self.request.user.organization)
        else:
            # Usuario sin organización no ve nada
            queryset = AppUser.objects.none()
        
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        return queryset.order_by('-date_joined')


# ============================================
# CÓDIGOS DE INVITACIÓN CON QR
# ============================================

@method_decorator(organization_admin_required, name='dispatch')
class InvitationCodeListView(ListView):
    """Lista de códigos de invitación de la organización"""
    model = InvitationCode
    template_name = 'admin/invitations/list.html'
    context_object_name = 'codes'
    paginate_by = 20
    
    def get_queryset(self):
        # ✅ MULTI-TENANT: Filtrar códigos por organización
        if self.request.user.is_superuser:
            queryset = InvitationCode.objects.all()
        elif self.request.user.organization:
            queryset = InvitationCode.objects.filter(organization=self.request.user.organization)
        else:
            queryset = InvitationCode.objects.none()
        
        # Filtros
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.select_related('organization', 'created_by').order_by('-created_at')


@method_decorator(organization_admin_required, name='dispatch')
class InvitationCodeCreateView(CreateView):
    """Crear nuevo código de invitación"""
    model = InvitationCode
    template_name = 'admin/invitations/create.html'
    fields = ['role', 'max_uses', 'expires_at', 'notes']
    success_url = reverse_lazy('admin_invitation_codes')
    
    def form_valid(self, form):
        # Asignar organización y creador
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        
        # Generar código único
        import random
        import string
        while True:
            code = 'TAXI-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not InvitationCode.objects.filter(code=code).exists():
                form.instance.code = code
                break
        
        messages.success(self.request, f'Código de invitación {form.instance.code} creado exitosamente.')
        return super().form_valid(form)


@method_decorator(organization_admin_required, name='dispatch')
class InvitationCodeDetailView(DetailView):
    """Ver detalles y QR del código de invitación"""
    model = InvitationCode
    template_name = 'admin/invitations/detail.html'
    context_object_name = 'code'
    
    def get_queryset(self):
        # ✅ MULTI-TENANT: Solo códigos de la organización
        if self.request.user.is_superuser:
            return InvitationCode.objects.all()
        elif self.request.user.organization:
            return InvitationCode.objects.filter(organization=self.request.user.organization)
        return InvitationCode.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generar QR code
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.object.get_qr_url())
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Convertir a base64 para mostrar en template
        img_str = base64.b64encode(buffer.getvalue()).decode()
        context['qr_image'] = f'data:image/png;base64,{img_str}'
        
        return context


@method_decorator(organization_admin_required, name='dispatch')
class InvitationCodeToggleView(View):
    """Activar/desactivar código de invitación"""
    
    def post(self, request, pk):
        # ✅ MULTI-TENANT: Solo códigos de la organización
        if request.user.is_superuser:
            code = get_object_or_404(InvitationCode, pk=pk)
        elif request.user.organization:
            code = get_object_or_404(InvitationCode, pk=pk, organization=request.user.organization)
        else:
            messages.error(request, "No tienes permiso para realizar esta acción.")
            return redirect('admin_invitation_codes')
        
        code.is_active = not code.is_active
        code.save()
        
        status = "activado" if code.is_active else "desactivado"
        messages.success(request, f'Código {code.code} {status} exitosamente.')
        return redirect('admin_invitation_codes')


# ============================================
# REPORTES FINANCIEROS
# ============================================

@method_decorator(organization_admin_required, name='dispatch')
class FinancialReportsView(TemplateView):
    """Reportes financieros globales"""
    template_name = 'admin/reports/financial.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Período seleccionado
        period = self.request.GET.get('period', 'month')
        now = timezone.now()
        
        if period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:  # week
            start_date = now - timedelta(days=7)
        
        # Carreras completadas en el período
        rides = Ride.objects.filter(
            created_at__gte=start_date,
            status='completed'
        )
        
        # Totales
        totals = rides.aggregate(
            total_rides=Count('id'),
            total_revenue=Sum('price'),
            total_commission=Sum('commission_amount')
        )
        
        context['total_rides'] = totals['total_rides'] or 0
        context['total_revenue'] = totals['total_revenue'] or Decimal('0.00')
        context['total_commission'] = totals['total_commission'] or Decimal('0.00')
        
        # Por cooperativa
        context['by_organization'] = Organization.objects.filter(
            is_active=True
        ).annotate(
            rides_count=Count('rides', filter=Q(rides__created_at__gte=start_date, rides__status='completed')),
            revenue=Sum('rides__price', filter=Q(rides__created_at__gte=start_date, rides__status='completed')),
            commission=Sum('rides__commission_amount', filter=Q(rides__created_at__gte=start_date, rides__status='completed'))
        ).order_by('-revenue')
        
        context['period'] = period
        context['start_date'] = start_date
        
        return context


# ============================================
# GESTIÓN DE FACTURAS (DESHABILITADO - Invoice no existe)
# ============================================

# @method_decorator(organization_admin_required, name='dispatch')
# class InvoiceListView(ListView):
#     """Lista de facturas"""
#     model = Invoice
#     template_name = 'admin/invoices/list.html'
#     context_object_name = 'invoices'
#     paginate_by = 20
#     
#     def get_queryset(self):
#         queryset = Invoice.objects.all().select_related('organization')
#         
#         status = self.request.GET.get('status')
#         if status:
#             queryset = queryset.filter(status=status)
#         
#         return queryset.order_by('-issued_at')


# @method_decorator(organization_admin_required, name='dispatch')
# class InvoiceCreateView(CreateView):
#     """Crear nueva factura"""
#     model = Invoice
#     form_class = InvoiceForm
#     template_name = 'admin/invoices/create.html'
#     success_url = reverse_lazy('admin_invoices')
#     
#     def form_valid(self, form):
#         # Generar número de factura automático
#         year = timezone.now().year
#         last_invoice = Invoice.objects.filter(
#             invoice_number__startswith=f'INV-{year}'
#         ).order_by('-invoice_number').first()
#         
#         if last_invoice:
#             last_num = int(last_invoice.invoice_number.split('-')[-1])
#             new_num = last_num + 1
#         else:
#             new_num = 1
#         
#         form.instance.invoice_number = f'INV-{year}-{new_num:04d}'
#         
#         # Calcular total
#         form.instance.total_amount = form.instance.subscription_fee + form.instance.commission_amount
#         
#         messages.success(self.request, f'Factura {form.instance.invoice_number} creada exitosamente.')
#         return super().form_valid(form)


# @method_decorator(organization_admin_required, name='dispatch')
# class InvoiceMarkPaidView(TemplateView):
#     """Marcar factura como pagada"""
#     
#     def post(self, request, pk):
#         invoice = get_object_or_404(Invoice, pk=pk)
#         invoice.mark_as_paid()
#         
#         messages.success(request, f'Factura {invoice.invoice_number} marcada como pagada.')
#         return redirect('admin_invoices')
