"""
Management command para expirar negociaciones de precio después de 15 minutos.

Uso:
    python manage.py expire_negotiations

Para ejecutar automáticamente cada minuto, agregar a crontab:
    * * * * * cd /path/to/project && python manage.py expire_negotiations
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from taxis.models import PriceNegotiation


class Command(BaseCommand):
    help = 'Marca como expiradas las negociaciones pendientes después de 15 minutos'

    def handle(self, *args, **options):
        # Calcular tiempo de expiración (15 minutos atrás)
        expiration_time = timezone.now() - timedelta(minutes=15)
        
        # Buscar negociaciones pendientes o con contraoferta que ya expiraron
        expired_negotiations = PriceNegotiation.objects.filter(
            status__in=['pending', 'counter_offered'],
            created_at__lt=expiration_time
        )
        
        count = expired_negotiations.count()
        
        if count > 0:
            # Marcar como expiradas
            expired_negotiations.update(status='expired')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {count} negociación(es) marcada(s) como expirada(s)'
                )
            )
            
            # Log de cada negociación expirada
            for neg in expired_negotiations:
                self.stdout.write(
                    f'   - Negociación #{neg.id}: Cliente {neg.customer.get_full_name()}, '
                    f'Propuesta ${neg.proposed_price}, Creada hace {timezone.now() - neg.created_at}'
                )
        else:
            self.stdout.write(
                self.style.WARNING('⏰ No hay negociaciones para expirar')
            )
