from django.conf import settings

def webpush_settings(request):
    """Añade la configuración de WEBPUSH al contexto de la plantilla."""
    return {'WEBPUSH_SETTINGS': settings.WEBPUSH_SETTINGS}
