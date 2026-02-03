import logging
from django.utils import timezone

class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            from .models import LogEvent
            
            # Mapear níveis de log
            level_mapping = {
                'DEBUG': 'DEBUG',
                'INFO': 'INFO', 
                'WARNING': 'WARNING',
                'ERROR': 'ERROR',
                'CRITICAL': 'CRITICAL'
            }
            
            LogEvent.objects.create(
                level=level_mapping.get(record.levelname, 'INFO'),
                message=record.getMessage(),
                module=record.module,
                timestamp=timezone.now()
            )
        except Exception:
            # Evita loops infinitos se houver erro ao salvar log
            pass