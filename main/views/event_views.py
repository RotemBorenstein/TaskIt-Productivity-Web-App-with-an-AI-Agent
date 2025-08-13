from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from ..models import Task, DailyTaskCompletion, Event
from ..forms import TaskForm, EventForm
from datetime import datetime, time, date, timedelta
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.dateparse import parse_datetime, parse_date


CALENDAR_URL = "/calendar/"  # <- change if your calendar page is at a different URL

def _aware(dt):
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

def _prefill_from_query(request):
    """
    Prefill initial form values from FullCalendar query params:
    - start, end: ISO strings (datetime or date)
    - all_day: 'true'/'false'
    """
    start_q = request.GET.get("start")
    end_q = request.GET.get("end")
    all_day_q = request.GET.get("all_day")

    initial = {}

    all_day = (all_day_q or "").lower() == "true"

    # Try datetime first, then date-only
    start_dt = parse_datetime(start_q) if start_q else None
    end_dt = parse_datetime(end_q) if end_q else None

    if not start_dt and start_q:
        d = parse_date(start_q)
        if d:
            start_dt = datetime.combine(d, time.min)
            if all_day:
                end_dt = datetime.combine(d + timedelta(days=1), time.min)
            else:
                end_dt = datetime.combine(d, time(hour=1))  # 1h default
    if not end_dt and end_q:
        d = parse_date(end_q)
        if d:
            end_dt = datetime.combine(d, time.min)

    start_dt = _aware(start_dt) if start_dt else None
    end_dt = _aware(end_dt) if end_dt else None

    if start_dt:
        initial["start_datetime"] = start_dt
    if end_dt:
        initial["end_datetime"] = end_dt
    initial["all_day"] = all_day

    return initial

"""@login_required
def event_create(request):
    initial = _prefill_from_query(request) if request.method == "GET" else {}
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.user = request.user
            ev.save()
            return redirect(CALENDAR_URL)
    else:
        form = EventForm(initial=initial)
    return render(request, "main/event_form.html", {"form": form, "mode": "create"})
"""
@login_required
def event_edit(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if ev.user_id != request.user.id:
        raise Http404()

    if request.method == "POST":
        form = EventForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            return redirect(CALENDAR_URL)
    else:
        form = EventForm(instance=ev)
    return render(request, "main/event_form.html", {"form": form, "mode": "edit", "event": ev})

@login_required
@require_http_methods(["POST"])
def event_delete(request, pk):
    ev = get_object_or_404(Event, pk=pk)
    if ev.user_id != request.user.id:
        raise Http404()
    ev.delete()
    return redirect(CALENDAR_URL)


# main/views_events.py
import json
from django.views.decorators.http import require_http_methods
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.http import JsonResponse, HttpResponseBadRequest
from ..models import Event

def _aware(dt):
    if dt and timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt

@login_required
@require_http_methods(["POST"])
def api_event_create(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    title = (payload.get("title") or "").strip()
    start = _aware(parse_datetime(payload.get("start")))
    end   = _aware(parse_datetime(payload.get("end")))
    all_day = bool(payload.get("allDay"))

    if not title or not start or not end:
        return HttpResponseBadRequest("title, start, end required")
    if end <= start:
        return HttpResponseBadRequest("end must be after start")

    # All-day end is exclusive (FullCalendar convention)
    # If same-day all-day, bump end to next midnight.
    if all_day and start.date() == end.date():
        end = timezone.make_aware(
            timezone.datetime.combine(end.date(), timezone.datetime.min.time())
        ) + timezone.timedelta(days=1)

    ev = Event.objects.create(
        user=request.user,
        title=title,
        start_datetime=start,
        end_datetime=end,
        all_day=all_day,
        description=payload.get("description", "").strip(),
    )

    return JsonResponse({
        "id": ev.id,
        "title": ev.title,
        "start": ev.start_datetime.isoformat(),
        "end": ev.end_datetime.isoformat(),
        "allDay": ev.all_day,
    }, status=201)
