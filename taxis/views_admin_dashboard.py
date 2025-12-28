"""
Vista temporal para admin_dashboard hasta que se apliquen las migraciones de Fase 3
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .decorators import organization_admin_required


@organization_admin_required
def admin_dashboard(request):
    """
    Dashboard para administradores de cooperativa.
    Accesible por:
    - Super admins (is_superuser=True)
    - Admins de cooperativa (role='admin' y tiene organization)
    """
    # Determinar si es super admin o admin de cooperativa
    is_super_admin = request.user.is_superuser
    
    context = {
        'user': request.user,
        'is_super_admin': is_super_admin,
        'organization': request.user.organization if not is_super_admin else None,
        'message': 'Panel de administración de cooperativa. Usa /admin/ para gestionar usuarios y organizaciones, o /superadmin/dashboard/ para el panel completo (solo super admins).'
    }
    
    return render(request, 'admin_dashboard_temp.html', context)
