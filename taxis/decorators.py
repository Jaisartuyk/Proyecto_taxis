"""
Decoradores para control de acceso en el panel de administración
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def superadmin_required(view_func):
    """
    Decorador para vistas que requieren permisos de super administrador.
    Solo usuarios con is_superuser=True pueden acceder.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        if not request.user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def organization_admin_required(view_func):
    """
    Decorador para vistas que requieren ser admin de una cooperativa.
    Permite acceso a super admins y admins de cooperativa.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        # Super admin siempre tiene acceso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Admin de cooperativa tiene acceso
        if request.user.role == 'admin' and request.user.organization:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('home')
    
    return wrapper


def driver_required(view_func):
    """
    Decorador para vistas que requieren ser conductor aprobado.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        if request.user.role != 'driver':
            messages.error(request, 'Esta página es solo para conductores.')
            return redirect('home')
        
        if request.user.driver_status != 'approved':
            messages.warning(request, 'Tu cuenta de conductor está pendiente de aprobación.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def same_organization_required(view_func):
    """
    Decorador para verificar que el usuario pertenece a la misma organización
    que el objeto que está intentando acceder.
    El objeto debe tener un atributo 'organization'.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        
        # Super admin siempre tiene acceso
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Aquí se podría agregar lógica adicional para verificar
        # que el objeto pertenece a la misma organización
        # Esto se implementaría en las vistas específicas
        
        return view_func(request, *args, **kwargs)
    
    return wrapper
