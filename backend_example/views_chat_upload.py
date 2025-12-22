"""Vista para subir archivos de chat a Cloudinary
Agregar esto a tu archivo views.py existente o crear un nuevo archivo"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import cloudinary
import cloudinary.uploader
from django.conf import settings
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_chat_media(request):
    """
    Endpoint para subir imágenes/videos a Cloudinary para el chat
    
    POST /api/chat/upload/
    Content-Type: multipart/form-data
    
    Campos:
    - file: Archivo (imagen o video)
    - message_type: 'image' o 'video' (opcional, se detecta automáticamente)
    
    Respuesta exitosa:
    {
        "success": true,
        "media_url": "https://res.cloudinary.com/...",
        "thumbnail_url": "https://res.cloudinary.com/...",  # Solo para videos
        "message_type": "image",
        "metadata": {
            "width": 1920,
            "height": 1080,
            "format": "jpg",
            "size": 123456
        }
    }
    
    Error:
    {
        "success": false,
        "error": "Mensaje de error"
    }
    """
    try:
        # Verificar que hay un archivo
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No se proporcionó ningún archivo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        file = request.FILES['file']
        
        # Validar tamaño (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return Response({
                'success': False,
                'error': f'El archivo es demasiado grande. Máximo: {max_size / (1024*1024):.1f}MB'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Detectar tipo de archivo
        file_type = request.POST.get('message_type', '').lower()
        if not file_type:
            # Detectar automáticamente por extensión
            file_name = file.name.lower()
            if any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                file_type = 'image'
            elif any(file_name.endswith(ext) for ext in ['.mp4', '.webm', '.mov', '.avi']):
                file_type = 'video'
            else:
                return Response({
                    'success': False,
                    'error': 'Tipo de archivo no soportado. Use imágenes (jpg, png, gif) o videos (mp4, webm)'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Configurar Cloudinary (si no está configurado, usar variables de entorno)
        # Asegúrate de tener estas variables en settings.py o en Railway:
        # CLOUDINARY_CLOUD_NAME
        # CLOUDINARY_API_KEY
        # CLOUDINARY_API_SECRET
        
        cloudinary.config(
            cloud_name=getattr(settings, 'CLOUDINARY_CLOUD_NAME', None),
            api_key=getattr(settings, 'CLOUDINARY_API_KEY', None),
            api_secret=getattr(settings, 'CLOUDINARY_API_SECRET', None)
        )
        
        # Subir a Cloudinary
        upload_options = {
            'folder': 'chat_media',  # Carpeta en Cloudinary
            'resource_type': 'auto',  # Detecta automáticamente imagen o video
        }
        
        # Para videos, generar thumbnail
        if file_type == 'video':
            upload_options['eager'] = [
                {'width': 300, 'height': 300, 'crop': 'fill', 'format': 'jpg'}
            ]
        
        result = cloudinary.uploader.upload(
            file,
            **upload_options
        )
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'media_url': result['secure_url'],
            'message_type': file_type,
            'metadata': {
                'width': result.get('width'),
                'height': result.get('height'),
                'format': result.get('format'),
                'size': result.get('bytes'),
                'duration': result.get('duration'),  # Solo para videos
            }
        }
        
        # Agregar thumbnail si es video
        if file_type == 'video' and 'eager' in result and len(result['eager']) > 0:
            response_data['thumbnail_url'] = result['eager'][0]['secure_url']
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except cloudinary.exceptions.Error as e:
        return Response({
            'success': False,
            'error': f'Error subiendo a Cloudinary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Versión alternativa sin DRF (si no usas DRF)
@csrf_exempt
def upload_chat_media_simple(request):
    """
    Versión simple sin DRF (usa Django puro)
    Agregar @login_required si lo necesitas
    """
    from django.http import JsonResponse
    from django.contrib.auth.decorators import login_required
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'No autenticado'}, status=401)
    
    # ... (mismo código de upload que arriba)
    # Usar JsonResponse en lugar de Response
    try:
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó ningún archivo'
            }, status=400)
        
        # ... resto del código igual ...
        # Al final:
        return JsonResponse(response_data, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

