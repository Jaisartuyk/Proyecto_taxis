from django.conf import settings

def webpush_settings(request):
    """Añade la configuración de WEBPUSH al contexto de la plantilla."""
    return {'WEBPUSH_SETTINGS': settings.WEBPUSH_SETTINGS}


def organization_context(request):
    """Añade la organización del usuario al contexto global."""
    if request.user.is_authenticated and hasattr(request.user, 'organization'):
        return {
            'user_organization': request.user.organization
        }
    return {}
