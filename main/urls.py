from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.home, name="signup"),
    path("login/", views.home, name="login"),
]
