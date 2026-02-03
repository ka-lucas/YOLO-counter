from django.urls import path
from . import views

app_name = "video_ao_vivo"

urlpatterns = [
    path("", views.live_page, name="index"),
    path("live/", views.live_page, name="live"),
    path("api/start/", views.api_start, name="start"),
    path("api/pause/", views.api_pause, name="pause"),
    path("api/resume/", views.api_resume, name="resume"),
    path("api/events/", views.api_events, name="events"),
    path("api/stop/", views.api_stop, name="stop"),
    path("api/status/", views.api_status, name="status"),
    path("stream/", views.stream_mjpeg, name="stream"),
    path("api/meta/", views.api_video_meta, name="meta"),
    path("api/line/", views.api_set_line, name="line"),
    path("api/snapshot/", views.api_snapshot, name="snapshot"),
    path("api/chart-data/", views.api_chart_data, name="chart_data"),
]
