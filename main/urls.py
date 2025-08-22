from django.urls import path
from django.contrib.auth import views as django_auth_views
from . import views
from .views import auth_views, task_views, calendar_views, event_views
app_name = "main"

urlpatterns = [
    path("", auth_views.home, name="home"),
    path("signup/", auth_views.signup, name="signup"),
    path("login/", django_auth_views.LoginView.as_view(template_name='main/login.html'), name="login"),
    path('logout/', django_auth_views.LogoutView.as_view(next_page='main:login'), name='logout'),
    path("tasks/",task_views.tasks_view, name="tasks"),
    path("tasks/create/", task_views.create_task, name="create_task"),
    path("tasks/complete/", task_views.complete_task, name="complete_task"),
    path("tasks/<int:pk>/edit/", task_views.edit_task, name="edit_task"),
    path("tasks/<int:pk>/delete/", task_views.delete_task, name="delete_task"),
    path('tasks/<int:task_id>/toggle_anchor/', task_views.toggle_anchor, name='toggle_anchor'),
    path("calendar/", calendar_views.calendar_view, name="calendar"),
    path("api/calendar/", calendar_views.calendar_events, name="calendar_events"),
    # Day panel
    path("api/tasks/day/", calendar_views.tasks_of_day, name="tasks_of_day"),
    path("api/daily-completions/", calendar_views.toggle_daily_completion, name="toggle_daily_completion"),
    path("api/tasks/<int:task_id>/complete/", calendar_views.toggle_long_term_completion, name="toggle_long_term_completion"),
    #path("events/new/", event_views.event_create, name="new"),
    #path("events/<int:pk>/edit/", event_views.event_edit, name="edit"),
    #path("events/<int:pk>/delete/", event_views.event_delete, name="delete"),
    path("api/calendar/", calendar_views.calendar_feed, name="calendar_feed"),
    path("api/events/", event_views.api_event_create, name="api_event_create"),
    path("api/events/<int:pk>/", event_views.api_event_detail, name="api_event_detail"),
]
