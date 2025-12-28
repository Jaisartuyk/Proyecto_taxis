"""
Vista temporal para admin_dashboard hasta que se apliquen las migraciones de Fase 3
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def admin_dashboard(request):
    """
    Dashboard para administradores de cooperativa.
    Por ahora redirige al dashboard del conductor hasta que se implementen las migraciones.
    """
    # Verificar que el usuario sea admin
    if request.user.role != 'admin':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    # Por ahora, mostrar un mensaje simple
    context = {
        'user': request.user,
        'message': 'Panel de administración de cooperativa en construcción. Por favor usa /admin/ para gestionar usuarios y organizaciones.'
    }
    
    return render(request, 'admin_dashboard_temp.html', context)
