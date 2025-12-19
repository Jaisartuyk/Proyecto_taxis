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
        # Log cada petición a archivos estáticos para debugging
        # Solo loggear archivos críticos para no saturar los logs
        if request.path.startswith(self.static_url) and any(
            x in request.path for x in ['floating-audio-button', 'audio-floating-button']
        ):
            print(f"[FALLBACK] Petición recibida: {request.path}")
            
            # Extraer la ruta del archivo
            file_path = request.path[len(self.static_url):].lstrip('/')
            full_path = os.path.join(self.static_root, file_path)
            
            print(f"[FALLBACK] Buscando archivo: {full_path}")
            print(f"[FALLBACK] Archivo existe: {os.path.exists(full_path)}")
            if os.path.exists(full_path):
                print(f"[FALLBACK] Es archivo: {os.path.isfile(full_path)}")
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                # Servir el archivo directamente sin pasar por WhiteNoise
                try:
                    print(f"[FALLBACK] ✅ Sirviendo archivo directamente: {file_path}")
                    file_handle = open(full_path, 'rb')
                    content_type = self._get_content_type(file_path)
                    print(f"[FALLBACK] Content-Type: {content_type}")
                    
                    response = FileResponse(
                        file_handle,
                        content_type=content_type
                    )
                    # Agregar headers apropiados
                    file_size = os.path.getsize(full_path)
                    response['Content-Length'] = file_size
                    print(f"[FALLBACK] Content-Length: {file_size}")
                    print(f"[FALLBACK] ✅ Respuesta creada, retornando archivo")
                    return response
                except Exception as e:
                    print(f"[FALLBACK] ❌ Error al servir archivo {file_path}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continuar con el procesamiento normal si hay un error
                    pass
            else:
                # Si el archivo no existe, log para debugging
                print(f"[FALLBACK] ⚠️ Archivo no encontrado: {full_path}")
                # Listar archivos en el directorio para debugging
                dir_path = os.path.dirname(full_path)
                if os.path.exists(dir_path):
                    print(f"[FALLBACK] Archivos en directorio {dir_path}:")
                    try:
                        for f in os.listdir(dir_path)[:10]:
                            print(f"  - {f}")
                    except:
                        pass
        
        # Procesar la petición normalmente (pasar a WhiteNoise u otros middlewares)
        # Solo loggear archivos críticos
        if request.path.startswith(self.static_url) and any(
            x in request.path for x in ['floating-audio-button', 'audio-floating-button']
        ):
            print(f"[FALLBACK] Pasando petición a siguiente middleware: {request.path}")
        response = self.get_response(request)
        if request.path.startswith(self.static_url) and any(
            x in request.path for x in ['floating-audio-button', 'audio-floating-button']
        ):
            print(f"[FALLBACK] Respuesta recibida del siguiente middleware: status={response.status_code}, path={request.path}")
        
        # Si WhiteNoise devolvió 404 para un archivo estático, intentar servirlo directamente
        if response.status_code == 404 and request.path.startswith(self.static_url):
            # Extraer la ruta del archivo
            file_path = request.path[len(self.static_url):].lstrip('/')
            full_path = os.path.join(self.static_root, file_path)
            
            print(f"[FALLBACK] WhiteNoise devolvió 404, intentando servir: {full_path}")
            
            # Verificar que el archivo existe
            if os.path.exists(full_path) and os.path.isfile(full_path):
                try:
                    print(f"[FALLBACK] ✅ WhiteNoise devolvió 404, sirviendo archivo directamente: {file_path}")
                    file_handle = open(full_path, 'rb')
                    response = FileResponse(
                        file_handle,
                        content_type=self._get_content_type(file_path)
                    )
                    # Agregar headers apropiados
                    response['Content-Length'] = os.path.getsize(full_path)
                    return response
                except Exception as e:
                    print(f"[FALLBACK] ❌ Error al servir archivo {file_path}: {e}")
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

