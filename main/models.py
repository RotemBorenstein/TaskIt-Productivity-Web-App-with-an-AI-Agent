from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Task(models.Model):
    TASK_TYPE_CHOICES = [
        ("daily", "Daily"),
        ("long_term", "Long Term"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    task_type = models.CharField(
        max_length=10, choices=TASK_TYPE_CHOICES, default="long_term"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.title} ({self.task_type})"


class DailyTaskCompletion(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="completions"
    )
    date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['task', 'date'], name='unique_task_date')]

    def __str__(self):
        return f"{self.task.title} completed on {self.date}"
