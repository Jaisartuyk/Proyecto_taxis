"""
Middleware personalizado para servir archivos estáticos si WhiteNoise no los encuentra
"""
import os
from django.http import FileResponse, Http404
from django.conf import settings


class StaticFilesFallbackMiddleware:
    """
    Middleware que sirve archivos estáticos desde STATIC_ROOT
    si WhiteNoise no los encuentra (devuelve 404).
    Este middleware debe estar DESPUÉS de WhiteNoiseMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.static_root = settings.STATIC_ROOT
        self.static_url = settings.STATIC_URL.rstrip('/')
        
    def __call__(self, request):
        response = self.get_response(request)
        
        # Si WhiteNoise devolvió 404 para un archivo estático, intentar servirlo directamente
        if response.status_code == 404 and request.path.startswith(self.static_url):
            # Extraer la ruta del archivo
            file_path = request.path[len(self.static_url):].lstrip('/')
            full_path = os.path.join(self.static_root, file_path)
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                try:
                    # Servir el archivo directamente
                    return FileResponse(
                        open(full_path, 'rb'),
                        content_type=self._get_content_type(file_path)
                    )
                except Exception as e:
                    # Si hay un error al servir el archivo, devolver 404
                    pass
        
        return response
    
    def _get_content_type(self, file_path):
        """Determinar el tipo de contenido basado en la extensión del archivo"""
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.json': 'application/json',
            '.woff': 'font/woff',
            '.woff2': 'font/woff2',
            '.ttf': 'font/ttf',
            '.eot': 'application/vnd.ms-fontobject',
        }
        return content_types.get(ext, 'application/octet-stream')

