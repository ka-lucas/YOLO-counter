from django import forms
from .models import ModelConfiguration


class ModelUploadForm(forms.ModelForm):
    """Form para upload de modelos TensorRT"""
    
    class Meta:
        model = ModelConfiguration
        fields = ['model_file', 'name', 'confidence_threshold', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do modelo (opcional)'
            }),
            'confidence_threshold': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '1',
                'step': '0.01',
                'value': '0.85'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def clean_model_file(self):
        file = self.cleaned_data.get('model_file')
        
        if file:
            # Verifica extensão
            if not file.name.endswith('.pt'):
                raise forms.ValidationError('Apenas arquivos .pt são permitidos')
            
            # Verifica tamanho (limite de 500MB)
            if file.size > 500 * 1024 * 1024:
                raise forms.ValidationError('Arquivo muito grande. Máximo: 500MB')
        
        return file