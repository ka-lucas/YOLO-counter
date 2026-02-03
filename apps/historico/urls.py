from django.urls import path
from . import views

app_name = 'historico'

urlpatterns = [
    path("", views.historico, name="historico"),
    path("session/<int:log_id>/", views.log_detail, name="log_detail"),
]
