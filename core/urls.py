from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.home.urls")),
    path("video-ao-vivo/", include("apps.video_ao_vivo.urls")),
    path("configuracoes/", include("apps.configuracao.urls")),
    path("oauth/", include("social_django.urls", namespace="social")),
    path("historico/", include("apps.historico.urls", namespace="historico")),
    path("cameras/", include("apps.cameras.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
