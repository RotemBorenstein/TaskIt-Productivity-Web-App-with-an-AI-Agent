from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "main"

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", auth_views.LoginView.as_view(template_name='main/login.html'), name="login"),
    path('logout/',auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path("tasks/",views.tasks_view, name="tasks"),
    path("tasks/create/", views.create_task, name="create_task"),
    path("tasks/complete/", views.complete_task, name="complete_task"),
    path("tasks/<int:pk>/edit/", views.edit_task, name="edit_task"),
    path("tasks/<int:pk>/delete/", views.delete_task, name="delete_task"),
]
