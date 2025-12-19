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
# En producción, WhiteNoise sirve los archivos estáticos automáticamente desde STATIC_ROOT
# No necesitamos agregar rutas estáticas aquí porque WhiteNoise middleware lo maneja