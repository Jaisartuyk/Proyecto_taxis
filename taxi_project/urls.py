"""taxi_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('serviceworker.js', TemplateView.as_view(template_name='js/serviceworker.js', content_type='application/javascript'), name='serviceworker'),
    path('manifest.json', TemplateView.as_view(template_name='manifest.json', content_type='application/json'), name='manifest'),
    path('', include('taxis.urls')),

    path('api/', include('taxis.api_urls')), # Incluye las URLs de la API bajo el prefijo /api/
]
if settings.DEBUG:  # Asegúrate de que solo se sirvan archivos estáticos y multimedia en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # En producción, crear una vista personalizada para servir archivos estáticos
    # Esto funciona como fallback si WhiteNoise no los sirve
    from django.views.static import serve
    from django.urls import re_path
    import os
    
    static_root = settings.STATIC_ROOT
    static_url = settings.STATIC_URL.rstrip('/')
    
    if os.path.exists(static_root):
        # Crear una vista personalizada que sirva archivos desde STATIC_ROOT
        # Esta vista se ejecutará si WhiteNoise no encuentra el archivo
        def serve_static_fallback(request, path):
            """Vista de fallback para servir archivos estáticos si WhiteNoise no los encuentra"""
            return serve(request, path, document_root=static_root)
        
        # Agregar la ruta de fallback ANTES de las otras rutas
        # Esto asegura que se ejecute si WhiteNoise no encuentra el archivo
        urlpatterns.insert(0, re_path(
            r'^{}(?P<path>.*)$'.format(static_url),
            serve_static_fallback,
            name='static_fallback'
        ))
        print(f"[INFO] Vista de fallback de archivos estáticos configurada desde: {static_root}")
    else:
        print(f"[WARNING] STATIC_ROOT no existe: {static_root}")