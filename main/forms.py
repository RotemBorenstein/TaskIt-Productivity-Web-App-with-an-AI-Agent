# main/forms.py

from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    """
    A ModelForm for creating or editing a Task, exposing only:
      - title (text input)
      - description (textarea)
    """
    """task_type = forms.ChoiceField(
        choices=Task.TASK_TYPE_CHOICES,
        widget=forms.RadioSelect,
        label="Task Type"
    )"""

    class Meta:
        model = Task
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter task title",
                "required": True,
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional description",
            }),
        }
        labels = {
            "title": "Title",
            "description": "Description",
        }
