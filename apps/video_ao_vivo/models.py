from django.db import models
from django.conf import settings
from apps.cameras.models import Camera


class CountingSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Contadores finais
    total_in = models.IntegerField(default=0)
    total_out = models.IntegerField(default=0)
    balance = models.IntegerField(default=0)
    
    # Path do log para auditoria
    log_file_path = models.CharField(max_length=500, blank=True, null=True)
    
    # Configurações usadas
    line_y_norm = models.FloatField(default=0.5)
    model_used = models.CharField(max_length=200, blank=True, null=True)
    
    # Informações adicionais da contagem
    animal_type = models.CharField(max_length=100, blank=True, null=True, help_text="Tipo de animal detectado")
    batch_number = models.CharField(max_length=100, blank=True, null=True, help_text="Número do lote")
    recipient = models.CharField(max_length=200, blank=True, null=True, help_text="Destinatário/Empresa")
    additional_notes = models.TextField(blank=True, null=True, help_text="Informações adicionais")
    
    class Meta:
        db_table = "counting_sessions"
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Sessão {self.id} - {self.camera.name} ({self.started_at})"