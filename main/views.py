from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from .forms import TaskForm
from .models import Task
def home(request):
    return render(request, "main/home.html", {})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after signup:
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'main/signup.html', {'form': form})

@login_required
def tasks(request):
    return render(request, "main/tasks.html", {})


# main/views.py


@login_required
def tasks_view(request):
    """
    Render the main Tasks page:
      - daily_tasks: all “daily” tasks for this user that are active and not completed
      - long_tasks: all “long_term” tasks for this user that are active and not completed
      - form: empty TaskForm to add a new task
    """
    daily_tasks = Task.objects.filter(
        user=request.user,
        task_type="daily",
        is_active=True,
        is_completed=False,
    ).order_by("created_at")

    long_tasks = Task.objects.filter(
        user=request.user,
        task_type="long_term",
        is_active=True,
        is_completed=False,
    ).order_by("created_at")

    daily_form_data = request.session.pop('daily_form_data', None)
    if daily_form_data:
        daily_form = TaskForm(daily_form_data, prefix='daily')
    else:
        daily_form = TaskForm(prefix='daily')

    long_form_data = request.session.pop('long_form_data', None)
    if long_form_data:
        long_form = TaskForm(long_form_data, prefix='long')
    else:
        long_form = TaskForm(prefix='long')

    return render(request, "main/tasks.html", {
        "daily_tasks": daily_tasks,
        "long_tasks": long_tasks,
        "daily_form": daily_form,
        "long_form": long_form,
    })


@login_required
def create_task(request):
    """
    Handle POST from the “Add New Task” form.
    If form is valid, attach user and save, then redirect to /tasks/.
    """
    if request.method != "POST":
        return redirect(reverse("main:tasks"))

    task_type = request.POST.get("task_type")
    if task_type not in ["daily", "long_term"]:
        messages.error(request, "Invalid task type")
        return redirect(reverse("main:tasks"))

    prefix = "daily" if task_type == "daily" else "long"
    form = TaskForm(request.POST, prefix=prefix)
    if form.is_valid():
        new_task = form.save(commit=False)
        new_task.user = request.user
        new_task.task_type = task_type
        new_task.save()
        messages.success(request, "Task added successfully")
    else:
        # Save only the POST data to the session, NOT the form itself!
        if task_type == "daily":
            request.session['daily_form_data'] = request.POST.dict()
        else:
            request.session['long_form_data'] = request.POST.dict()

    return redirect(reverse("main:tasks"))



@login_required
def complete_task(request):
    """
    AJAX endpoint to mark a Task as completed.
    Expects POST with 'task_id'. Returns JSON {"success": true} on success.
    """
    if request.method != "POST" or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"success": False, "error": "Invalid request."}, status=400)

    task_id = request.POST.get("task_id")
    if not task_id:
        return JsonResponse({"success": False, "error": "task_id missing."}, status=400)

    try:
        task = Task.objects.get(pk=task_id, user=request.user, is_active=True)
    except Task.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task not found."}, status=404)

    task.is_completed = True
    task.completed_at = timezone.now()
    task.save()
    return JsonResponse({"success": True})


@login_required
def edit_task(request, pk):
    """
    GET: Show a TaskForm pre-filled for task=pk.
    POST: Bind form to existing task, save if valid, then redirect to /tasks/.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user, is_active=True)

    if request.method == "POST":
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, "Task updated.")
            return redirect(reverse("main:tasks"))
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TaskForm(instance=task)

    return render(request, "main/edit_task.html", {
        "form": form,
        "task": task,
    })


@login_required
def delete_task(request, pk):
    """
    GET: Show a confirmation page for deleting task=pk.
    POST: Set is_active=False on the task, then redirect to /tasks/.
    """
    task = get_object_or_404(Task, pk=pk, user=request.user, is_active=True)

    if request.method == "POST":
        task.is_active = False
        task.save()
        messages.success(request, "Task deleted.")
        return redirect(reverse("main:tasks"))

    return render(request, "main/confirm_delete.html", {
        "task": task,
    })
