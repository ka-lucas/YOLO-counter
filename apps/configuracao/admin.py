from django.contrib import admin
from django.utils.html import format_html
from .models import ModelConfiguration
import os


@admin.register(ModelConfiguration)
class ModelConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'status_display', 'is_active', 'visibility_display', 'confidence_threshold', 'file_info', 'uploaded_at', 'uploaded_by')
    list_filter = ('is_active', 'is_public', 'uploaded_at', 'confidence_threshold')
    search_fields = ('name',)
    readonly_fields = ('uploaded_at', 'updated_at', 'file_size', 'uploaded_by', 'file_status')
    actions = ['delete_missing_files', 'make_public', 'make_private']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'model_file', 'is_active', 'file_status')
        }),
        ('Permissões', {
            'fields': ('is_public',),
            'description': 'Marque para disponibilizar este modelo para todos os usuários'
        }),
        ('Configurações', {
            'fields': ('confidence_threshold',)
        }),
        ('Metadados', {
            'fields': ('file_size', 'uploaded_by', 'uploaded_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Mostra se o arquivo existe ou está faltando"""
        try:
            if obj.model_file and os.path.isfile(obj.model_file.path):
                return format_html('<span style="color: green;">✓ Existe</span>')
            else:
                return format_html('<span style="color: red;">✗ Faltando</span>')
        except (ValueError, AttributeError):
            return format_html('<span style="color: red;">✗ Erro</span>')
    status_display.short_description = 'Status do Arquivo'
    
    def visibility_display(self, obj):
        """Mostra se é público ou privado"""
        if obj.is_public:
            return format_html('<span style="color: green; font-weight: bold;">🌐 Público</span>')
        else:
            return format_html('<span style="color: orange;">🔒 Privado</span>')
    visibility_display.short_description = 'Visibilidade'
    
    def file_info(self, obj):
        """Mostra informações do arquivo"""
        try:
            if obj.model_file:
                if os.path.isfile(obj.model_file.path):
                    size_mb = round(obj.model_file.size / (1024 * 1024), 2)
                    return f"{size_mb} MB"
                else:
                    return format_html('<span style="color: red;">Arquivo não encontrado</span>')
            return "—"
        except (ValueError, AttributeError):
            return "—"
    file_info.short_description = 'Tamanho'
    
    def file_status(self, obj):
        """Campo readonly que mostra o status completo do arquivo"""
        try:
            if not obj.model_file:
                return "Nenhum arquivo associado"
            
            file_path = obj.model_file.path
            if os.path.isfile(file_path):
                size_mb = round(obj.model_file.size / (1024 * 1024), 2)
                return format_html(
                    '<div style="color: green;"><strong>✓ Arquivo encontrado</strong><br/>'
                    f'Caminho: {file_path}<br/>'
                    f'Tamanho: {size_mb} MB</div>'
                )
            else:
                return format_html(
                    '<div style="color: red;"><strong>✗ Arquivo não encontrado!</strong><br/>'
                    f'Caminho esperado: {file_path}</div>'
                )
        except (ValueError, AttributeError) as e:
            return format_html(f'<div style="color: red;"><strong>✗ Erro ao verificar:</strong><br/>{str(e)}</div>')
    file_status.short_description = 'Status do Arquivo'
    
    def delete_missing_files(self, request, queryset):
        """Action para deletar registros com arquivos faltando"""
        deleted_count = 0
        for obj in queryset:
            try:
                if obj.model_file and not os.path.isfile(obj.model_file.path):
                    obj.delete()
                    deleted_count += 1
            except (ValueError, AttributeError):
                obj.delete()
                deleted_count += 1
        
        self.message_user(request, f'{deleted_count} modelo(s) com arquivo faltando foi/foram deletado(s).')
    delete_missing_files.short_description = 'Deletar modelos com arquivos faltando'
    
    def make_public(self, request, queryset):
        """Action para tornar modelos públicos"""
        updated = queryset.update(is_public=True)
        self.message_user(request, f'{updated} modelo(s) foi/foram marcado(s) como público(s).')
    make_public.short_description = 'Tornar público'
    
    def make_private(self, request, queryset):
        """Action para tornar modelos privados"""
        updated = queryset.update(is_public=False)
        self.message_user(request, f'{updated} modelo(s) foi/foram marcado(s) como privado(s).')
    make_private.short_description = 'Tornar privado'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo objeto
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
