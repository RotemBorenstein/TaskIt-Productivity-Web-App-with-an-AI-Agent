# main/forms.py

from django import forms
from .models import Task
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Event

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





class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "start_datetime", "end_datetime", "all_day", "task"]
        widgets = {
            "start_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_datetime": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_datetime")
        end = cleaned.get("end_datetime")
        all_day = cleaned.get("all_day")

        if start and timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
            cleaned["start_datetime"] = start
        if end and timezone.is_naive(end):
            end = timezone.make_aware(end, timezone.get_current_timezone())
            cleaned["end_datetime"] = end

        if start and end and end <= start:
            raise ValidationError("End must be after start.")

        # FullCalendar end is exclusive for all-day. If all_day and same-day,
        # bump end to next midnight to follow that convention.
        if all_day and start and end and start.date() == end.date():
            cleaned["end_datetime"] = timezone.make_aware(
                timezone.datetime.combine(end.date(), timezone.datetime.min.time())
            ) + timezone.timedelta(days=1)

        return cleaned
