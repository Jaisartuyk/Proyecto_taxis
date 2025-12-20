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
    # Esta vista se ejecutará ANTES de WhiteNoise para archivos específicos
    from django.views.static import serve
    from django.urls import re_path
    from django.http import FileResponse, Http404
    import os
    
    static_root = settings.STATIC_ROOT
    static_url = settings.STATIC_URL.rstrip('/')
    
    if os.path.exists(static_root):
        # Crear una vista personalizada que sirva archivos desde STATIC_ROOT
        # Esta vista se ejecutará ANTES de WhiteNoise para archivos específicos
        def serve_static_fallback(request, path):
            """Vista de fallback para servir archivos estáticos directamente desde STATIC_ROOT"""
            full_path = os.path.join(static_root, path)
            
            # Solo loggear archivos críticos para debugging
            is_critical = any(x in path for x in ['floating-audio-button', 'audio-floating-button', 'badge-manager', 'notifications'])
            if is_critical:
                print(f"[URLS-FALLBACK] Petición recibida: {request.path}")
                print(f"[URLS-FALLBACK] Buscando archivo: {full_path}")
                print(f"[URLS-FALLBACK] Archivo existe: {os.path.exists(full_path)}")
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Determinar content type
                ext = os.path.splitext(path)[1].lower()
                content_types = {
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.svg': 'image/svg+xml',
                    '.json': 'application/json',
                }
                content_type = content_types.get(ext, 'application/octet-stream')
                
                # Servir el archivo directamente
                try:
                    file_handle = open(full_path, 'rb')
                    response = FileResponse(file_handle, content_type=content_type)
                    response['Content-Length'] = str(os.path.getsize(full_path))
                    response['Cache-Control'] = 'public, max-age=31536000'
                    if is_critical:
                        print(f"[URLS-FALLBACK] ✅ Sirviendo archivo: {path} ({content_type})")
                    return response
                except Exception as e:
                    if is_critical:
                        print(f"[URLS-FALLBACK] ❌ Error sirviendo archivo: {e}")
                    raise Http404(f"Archivo no encontrado: {path}")
            else:
                if is_critical:
                    print(f"[URLS-FALLBACK] ⚠️ Archivo no encontrado: {full_path}")
                raise Http404(f"Archivo no encontrado: {path}")
        
        # Agregar la ruta de fallback ANTES de las otras rutas
        # IMPORTANTE: Las URLs se procesan en orden, así que esto se ejecutará ANTES de WhiteNoise
        urlpatterns.insert(0, re_path(
            r'^{}(?P<path>.*)$'.format(static_url),
            serve_static_fallback,
            name='static_fallback'
        ))
        print(f"[URLS] ✅ Vista de fallback de archivos estáticos configurada desde: {static_root}")
    else:
        print(f"[URLS] [WARNING] STATIC_ROOT no existe: {static_root}")