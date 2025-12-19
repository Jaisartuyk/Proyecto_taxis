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
        # Logs de inicialización - estos deberían aparecer al iniciar el servidor
        print(f"\n[FALLBACK] ========================================")
        print(f"[FALLBACK] StaticFilesFallbackMiddleware INICIALIZADO")
        print(f"[FALLBACK] STATIC_ROOT: {self.static_root}")
        print(f"[FALLBACK] STATIC_URL: {self.static_url}")
        # Verificar que STATIC_ROOT existe
        if os.path.exists(self.static_root):
            file_count = sum([len(files) for r, d, files in os.walk(self.static_root)])
            print(f"[FALLBACK] Archivos en STATIC_ROOT: {file_count}")
            # Verificar archivos críticos
            critical_files = ['css/floating-audio-button.css', 'js/audio-floating-button.js']
            for file_path in critical_files:
                full_path = os.path.join(self.static_root, file_path)
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"[FALLBACK] [OK] {file_path} - {size} bytes")
                else:
                    print(f"[FALLBACK] [ERROR] {file_path} NO existe")
        else:
            print(f"[FALLBACK] [ERROR] STATIC_ROOT no existe: {self.static_root}")
        print(f"[FALLBACK] ========================================\n")
        
    def __call__(self, request):
        # Interceptar ANTES de que WhiteNoise procese la petición
        # Si es una petición a un archivo estático, verificar si existe y servirlo directamente
        if request.path.startswith(self.static_url):
            # Extraer la ruta del archivo
            file_path = request.path[len(self.static_url):].lstrip('/')
            full_path = os.path.join(self.static_root, file_path)
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Servir el archivo directamente sin pasar por WhiteNoise
                try:
                    print(f"[FALLBACK] Sirviendo archivo directamente (antes de WhiteNoise): {file_path}")
                    file_handle = open(full_path, 'rb')
                    response = FileResponse(
                        file_handle,
                        content_type=self._get_content_type(file_path)
                    )
                    # Agregar headers apropiados
                    response['Content-Length'] = os.path.getsize(full_path)
                    return response
                except Exception as e:
                    print(f"[FALLBACK] Error al servir archivo {file_path}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continuar con el procesamiento normal si hay un error
                    pass
            else:
                # Si el archivo no existe, log para debugging
                print(f"[FALLBACK] Archivo no encontrado: {full_path}")
        
        # Procesar la petición normalmente (pasar a WhiteNoise u otros middlewares)
        response = self.get_response(request)
        
        # Si WhiteNoise devolvió 404 para un archivo estático, intentar servirlo directamente
        if response.status_code == 404 and request.path.startswith(self.static_url):
            # Extraer la ruta del archivo
            file_path = request.path[len(self.static_url):].lstrip('/')
            full_path = os.path.join(self.static_root, file_path)
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                try:
                    print(f"[FALLBACK] WhiteNoise devolvió 404, sirviendo archivo directamente: {file_path}")
                    file_handle = open(full_path, 'rb')
                    response = FileResponse(
                        file_handle,
                        content_type=self._get_content_type(file_path)
                    )
                    # Agregar headers apropiados
                    response['Content-Length'] = os.path.getsize(full_path)
                    return response
                except Exception as e:
                    print(f"[FALLBACK] Error al servir archivo {file_path}: {e}")
                    import traceback
                    traceback.print_exc()
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

