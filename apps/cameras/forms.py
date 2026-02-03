# forms.py
from django import forms
from .models import Camera
from apps.configuracao.models import ModelConfiguration


class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = ["name", "rtsp_url", "stream_url", "location", "model_config", "detection_class", "is_active"]
        labels = {
            "name": "Nome da Câmera",
            "rtsp_url": "URL RTSP",
            "stream_url": "URL HTTP/MJPEG",
            "location": "Localização",
            "model_config": "Modelo .pt",
            "detection_class": "Classe para Detectar",
            "is_active": "Ativa",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "rtsp_url": forms.TextInput(attrs={"class": "form-control", "placeholder": "rtsp://ip:porta/caminho"}),
            "stream_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "http://ip:porta/mjpg/video.mjpg"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "model_config": forms.Select(attrs={"class": "form-control"}),
            "detection_class": forms.Select(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extrai o user dos kwargs ANTES de chamar super()
        self.user = kwargs.pop('user', None)
        
        # Chama o super
        super().__init__(*args, **kwargs)
        
        # Configura o queryset do model_config
        if self.user:
            # Filtrar modelos apenas do usuário logado + modelo ativo global
            user_models = ModelConfiguration.objects.filter(uploaded_by=self.user)
            active_global = ModelConfiguration.objects.filter(is_active=True)
            available_models = (user_models | active_global).distinct()
            self.fields['model_config'].queryset = available_models
        else:
            # Se não houver user, mostra todos
            self.fields['model_config'].queryset = ModelConfiguration.objects.all()
        
        # Configura o empty_label
        self.fields['model_config'].empty_label = "-- Selecione um modelo --"
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Atribui o usuário logado
        instance.user = self.user
        # Garante que o nome da classe seja salvo
        if instance.detection_class is not None:
            class_dict = dict(Camera.YOLO_CLASSES)
            instance.detection_class_name = class_dict.get(instance.detection_class, '')
        if commit:
            instance.save()
        return instance