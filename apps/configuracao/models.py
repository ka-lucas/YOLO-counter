from django.db import models
from django.core.validators import FileExtensionValidator
from django.conf import settings
import os


def model_upload_path(instance, filename):
    """Define o caminho de upload: media/models/nome_do_arquivo.pt"""
    return f'models/{filename}'


class ModelConfigurationManager(models.Manager):
    """Manager customizado para ModelConfiguration"""
    
    def public(self):
        """Retorna apenas modelos públicos"""
        return self.filter(is_public=True)
    
    def get_available_for_user(self, user=None):
        """Retorna modelos disponíveis para um usuário
        - Se for superuser: todos os modelos
        - Se for usuário comum: modelos públicos + seus próprios modelos
        """
        if user and user.is_superuser:
            return self.all()
        elif user:
            return self.filter(models.Q(is_public=True) | models.Q(uploaded_by=user))
        else:
            return self.filter(is_public=True)


class ModelConfiguration(models.Model):
    """Configuração do modelo de IA"""
    
    # Manager customizado
    objects = ModelConfigurationManager()
    
    # Arquivo do modelo
    model_file = models.FileField(
        upload_to=model_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pt'])],
        help_text="Arquivo do modelo TensorRT (.pt)"
    )
    
    # Metadados
    name = models.CharField(
        max_length=255,
        help_text="Nome do modelo (ex: yolov8n_pig_v2)"
    )
    
    is_active = models.BooleanField(
        default=False,
        help_text="Modelo ativo no sistema"
    )
    
    is_public = models.BooleanField(
        default=False,
        help_text="Disponível para todos os usuários (se False, apenas o proprietário pode usar)"
    )
    
    confidence_threshold = models.FloatField(
        default=0.85,
        help_text="Confiança mínima para detecção (0.0 a 1.0)"
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_models'
    )
    
    class Meta:
        verbose_name = "Configuração de Modelo"
        verbose_name_plural = "Configurações de Modelos"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        visibility = "Público" if self.is_public else "Privado"
        return f"{self.name} - {'Ativo' if self.is_active else 'Inativo'} ({visibility})"
    
    def save(self, *args, **kwargs):
        # Se este modelo está sendo ativado, desativa todos os outros
        if self.is_active:
            ModelConfiguration.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Deleta o arquivo físico quando o registro for deletado
        if self.model_file:
            if os.path.isfile(self.model_file.path):
                os.remove(self.model_file.path)
        super().delete(*args, **kwargs)
    
    @property
    def file_size(self):
        """Retorna o tamanho do arquivo em MB"""
        if self.model_file:
            try:
                if os.path.isfile(self.model_file.path):
                    size_bytes = self.model_file.size
                    return round(size_bytes / (1024 * 1024), 2)
            except (ValueError, AttributeError):
                pass
        return 0
    
    @property
    def file_exists(self):
        """Verifica se o arquivo físico existe"""
        if self.model_file:
            try:
                return os.path.isfile(self.model_file.path)
            except (ValueError, AttributeError):
                return False
        return False