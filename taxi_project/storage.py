"""
Storage personalizado para WhiteNoise que maneja archivos faltantes durante collectstatic
"""
from whitenoise.storage import CompressedStaticFilesStorage
import os
import logging

logger = logging.getLogger(__name__)


class SafeCompressedStaticFilesStorage(CompressedStaticFilesStorage):
    """
    Storage que extiende CompressedStaticFilesStorage pero maneja archivos faltantes
    de forma segura durante collectstatic
    """
    
    def _compress_path(self, path):
        """
        Sobrescribe _compress_path para manejar archivos que pueden no existir
        """
        full_path = os.path.join(self.location, path)
        if not os.path.exists(full_path):
            logger.warning(f"Archivo no encontrado durante compresion: {full_path}")
            return []  # Retornar lista vacía si el archivo no existe
        
        try:
            # Llamar al método del padre solo si el archivo existe
            return super()._compress_path(path)
        except FileNotFoundError:
            logger.warning(f"Archivo eliminado durante compresion: {full_path}")
            return []  # Retornar lista vacía si el archivo fue eliminado
        except Exception as e:
            logger.warning(f"Error durante compresion de {path}: {e}")
            return []  # Retornar lista vacía en caso de error

