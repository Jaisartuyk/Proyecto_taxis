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

from .models import Organization, AppUser, Ride, Invoice
from .forms import OrganizationForm, DriverApprovalForm, InvoiceForm
from .decorators import superadmin_required
from django.utils.decorators import method_decorator


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
            
            # Facturas pendientes
            try:
                context['pending_invoices'] = Invoice.objects.filter(
                    status='pending'
                ).select_related('organization')[:5]
            except:
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

@method_decorator(superadmin_required, name='dispatch')
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


@method_decorator(superadmin_required, name='dispatch')
class OrganizationCreateView(CreateView):
    """Crear nueva cooperativa"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'admin/organizations/create.html'
    success_url = reverse_lazy('admin_organizations')
    
    def form_valid(self, form):
        messages.success(self.request, f'Cooperativa "{form.instance.name}" creada exitosamente.')
        return super().form_valid(form)


@method_decorator(superadmin_required, name='dispatch')
class OrganizationUpdateView(UpdateView):
    """Editar cooperativa existente"""
    model = Organization
    form_class = OrganizationForm
    template_name = 'admin/organizations/edit.html'
    success_url = reverse_lazy('admin_organizations')
    
    def form_valid(self, form):
        messages.success(self.request, f'Cooperativa "{form.instance.name}" actualizada exitosamente.')
        return super().form_valid(form)


@method_decorator(superadmin_required, name='dispatch')
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


@method_decorator(superadmin_required, name='dispatch')
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

@method_decorator(superadmin_required, name='dispatch')
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


@method_decorator(superadmin_required, name='dispatch')
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


@method_decorator(superadmin_required, name='dispatch')
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
# REPORTES FINANCIEROS
# ============================================

@method_decorator(superadmin_required, name='dispatch')
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
# GESTIÓN DE FACTURAS
# ============================================

@method_decorator(superadmin_required, name='dispatch')
class InvoiceListView(ListView):
    """Lista de facturas"""
    model = Invoice
    template_name = 'admin/invoices/list.html'
    context_object_name = 'invoices'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Invoice.objects.all().select_related('organization')
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-issued_at')


@method_decorator(superadmin_required, name='dispatch')
class InvoiceCreateView(CreateView):
    """Crear nueva factura"""
    model = Invoice
    form_class = InvoiceForm
    template_name = 'admin/invoices/create.html'
    success_url = reverse_lazy('admin_invoices')
    
    def form_valid(self, form):
        # Generar número de factura automático
        year = timezone.now().year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=f'INV-{year}'
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1
        
        form.instance.invoice_number = f'INV-{year}-{new_num:04d}'
        
        # Calcular total
        form.instance.total_amount = form.instance.subscription_fee + form.instance.commission_amount
        
        messages.success(self.request, f'Factura {form.instance.invoice_number} creada exitosamente.')
        return super().form_valid(form)


@method_decorator(superadmin_required, name='dispatch')
class InvoiceMarkPaidView(TemplateView):
    """Marcar factura como pagada"""
    
    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, pk=pk)
        invoice.mark_as_paid()
        
        messages.success(request, f'Factura {invoice.invoice_number} marcada como pagada.')
        return redirect('admin_invoices')
