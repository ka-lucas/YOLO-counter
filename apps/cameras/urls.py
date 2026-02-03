from django.urls import path
from . import views

app_name = "cameras"

urlpatterns = [
    path("", views.camera_list, name="list"),
    path("nova/", views.camera_create, name="create"),
    path("<int:pk>/editar/", views.camera_update, name="update"),
    path("<int:pk>/excluir/", views.camera_delete, name="delete"),
    path("<int:pk>/ao-vivo/", views.camera_live, name="live"),
]
