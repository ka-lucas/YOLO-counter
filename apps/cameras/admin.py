from django.contrib import admin
from .models import Camera

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'detection_class_name', 'primary_url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['name', 'primary_url', 'user__email']
    readonly_fields = ['created_at', 'detection_class_name']
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('name', 'user', 'location', 'is_active', 'created_at')
        }),
        ('URLs da Câmera', {
            'fields': ('stream_url', 'rtsp_url')
        }),
        ('Configuração de Detecção', {
            'fields': ('detection_class', 'detection_class_name', 'model_config')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)