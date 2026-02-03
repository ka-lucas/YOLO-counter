from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import home, EmailLoginView

urlpatterns = [
    path("", home, name="home"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
]
