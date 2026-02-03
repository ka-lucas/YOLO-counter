from django.urls import path
from . import views

app_name = 'configuracao'

urlpatterns = [
    path("", views.index, name="index"),
    path("models/", views.models_list, name="models_list"),
    path("model/<int:pk>/edit/", views.model_edit, name="model_edit"),
    path("model/<int:pk>/delete/", views.model_delete, name="model_delete"),
    path("model/upload/", views.upload_model, name="upload_model"),
    path("model/<int:pk>/toggle/", views.toggle_model_active, name="toggle_model"),
    path("model/confidence/", views.update_model_confidence, name="update_confidence"),
]