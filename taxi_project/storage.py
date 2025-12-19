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
        durante la compresión paralela de WhiteNoise
        """
        full_path = os.path.join(self.location, path)
        
        # Verificar que el archivo existe antes de intentar comprimirlo
        if not os.path.exists(full_path):
            logger.warning(f"Archivo no encontrado durante compresion (ignorado): {full_path}")
            return []  # Retornar lista vacía si el archivo no existe
        
        try:
            # Llamar al método del padre solo si el archivo existe
            return super()._compress_path(path)
        except FileNotFoundError:
            # El archivo pudo haber sido eliminado durante la compresión
            logger.warning(f"Archivo eliminado durante compresion (ignorado): {full_path}")
            return []  # Retornar lista vacía si el archivo fue eliminado
        except Exception as e:
            # Cualquier otro error durante la compresión
            logger.warning(f"Error durante compresion de {path} (ignorado): {e}")
            return []  # Retornar lista vacía en caso de error
    
    def post_process(self, paths, dry_run=False, **options):
        """
        Sobrescribe post_process para manejar archivos que pueden no existir
        """
        # Filtrar solo archivos que realmente existen
        existing_paths = {}
        for path, storage in paths.items():
            full_path = os.path.join(self.location, path)
            if os.path.exists(full_path):
                existing_paths[path] = storage
            else:
                # Log pero no fallar si el archivo no existe
                logger.warning(f"Archivo no encontrado durante post_process: {full_path}")
                # Aún así retornar el path para que se copie sin comprimir
                yield path, storage, False
        
        # Llamar al post_process del padre solo con archivos existentes
        if existing_paths:
            try:
                yield from super().post_process(existing_paths, dry_run=dry_run, **options)
            except FileNotFoundError as e:
                # Si aún así hay un error, loguear pero continuar
                logger.warning(f"Error durante compresion (ignorado): {e}")
                # Retornar los paths sin comprimir
                for path, storage in existing_paths.items():
                    yield path, storage, False
            except Exception as e:
                logger.warning(f"Error durante post_process (ignorado): {e}")
                # Retornar los paths sin comprimir
                for path, storage in existing_paths.items():
                    yield path, storage, False

