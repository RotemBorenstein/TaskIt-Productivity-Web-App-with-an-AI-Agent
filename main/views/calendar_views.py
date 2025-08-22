from django.shortcuts import render
from ..models import Task, DailyTaskCompletion, Event
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import models
from datetime import date as _date
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime, time

@login_required
def calendar_view(request):
    return render(request, "main/calendar.html")


def _parse_iso_to_aware(s: str):
    """
    FullCalendar sends 'start'/'end' as ISO (date or datetime).
    Convert to timezone-aware datetimes in the current TZ.
    """
    tz = timezone.get_current_timezone()
    try:
        # If it includes 'T', it's a datetime
        if "T" in s:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = timezone.make_aware(dt, tz)
            else:
                dt = dt.astimezone(tz)
        else:
            # Date-only -> make it midnight local
            d = datetime.fromisoformat(s).date()
            dt = timezone.make_aware(datetime.combine(d, time.min), tz)
        return dt
    except Exception:
        return None

@login_required
def calendar_events(request):
    # FullCalendar supplies ?start=...&end=... (end is exclusive)
    start_str = request.GET.get("start")
    end_str = request.GET.get("end")
    start_dt = _parse_iso_to_aware(start_str) if start_str else None
    end_dt = _parse_iso_to_aware(end_str) if end_str else None

    qs = Event.objects.filter(user=request.user)
    if start_dt and end_dt:
        # Events overlapping the [start,end) window
        qs = qs.filter(start_datetime__lt=end_dt, end_datetime__gt=start_dt)

    data = []
    for ev in qs:
        start_local = timezone.localtime(ev.start_datetime)
        end_local = timezone.localtime(ev.end_datetime)
        data.append({
            "id": ev.id,
            "title": ev.title,
            "start": start_local.isoformat(),  # e.g., 2025-08-10T14:00:00+03:00
            "end": end_local.isoformat(),
            "allDay": bool(ev.all_day),
        })
    return JsonResponse(data, safe=False)




def _parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str).date()
    except Exception:
        return None




@login_required
def tasks_of_day(request):
    date_str = request.GET.get("date")
    d = _parse_date(date_str)
    if not d:
        return HttpResponseBadRequest("Invalid or missing date")

    # hide all tasks for future dates
    if d > _date.today():
        return JsonResponse({"date": d.isoformat(), "daily": [], "long_term": []})

    # ---------- DAILY ----------
    # Base: user's daily tasks created on/before d and active
    daily_base = Task.objects.filter(
        user=request.user,
        task_type="daily",
        is_active=True,
        created_at__date__lte=d,
    )

    # Include if anchored OR (not completed yet by d)
    daily_qs = daily_base.filter(
        models.Q(is_anchored=True) |
        models.Q(completed_at__isnull=True) |
        models.Q(completed_at__date__gte=d)
    )

    # Which of those were completed ON d?
    completed_daily_ids = set(
        DailyTaskCompletion.objects
        .filter(task__in=daily_qs, date=d).values_list("task_id", flat=True)
    )

    daily = [
        {"id": t.id, "title": t.title, "completed": (t.id in completed_daily_ids)}
        for t in daily_qs
    ]

    # ---------- LONG-TERM (unchanged from your latest rule) ----------
    lt_qs = Task.objects.filter(
        user=request.user, task_type="long_term", created_at__date__lte=d
    ).filter(models.Q(completed_at__isnull=True) | models.Q(completed_at__date__gte=d))

    long_term = []
    for t in lt_qs:
        completed_at = getattr(t, "completed_at", None)
        long_term.append({
            "id": t.id,
            "title": t.title,
            "completed_on_that_day": bool(completed_at and completed_at.date() == d),
            "completed_on_or_before_selected_day": bool(completed_at and completed_at.date() <= d),
            "completed_at": completed_at.isoformat() if completed_at else None,
        })

    return JsonResponse({"date": d.isoformat(), "daily": daily, "long_term": long_term})



@require_http_methods(["POST", "DELETE"])
@login_required
def toggle_daily_completion(request):
    """
    POST -> mark completed for that date
    DELETE -> unmark completion for that date
    Body (JSON or form): task_id, date=YYYY-MM-DD
    """
    task_id = request.POST.get("task_id") or request.GET.get("task_id")
    date_str = request.POST.get("date") or request.GET.get("date")
    d = _parse_date(date_str)
    if not task_id or not d:
        return HttpResponseBadRequest("task_id and date are required")

    try:
        task = Task.objects.get(id=task_id, user=request.user, task_type="daily")
    except Task.DoesNotExist:
        return HttpResponseBadRequest("Task not found or not daily")

    if request.method == "POST":
        DailyTaskCompletion.objects.get_or_create(task=task, date=d)
        return JsonResponse({"ok": True, "completed": True})
    else:  # DELETE
        DailyTaskCompletion.objects.filter(task=task, date=d).delete()
        return JsonResponse({"ok": True, "completed": False})

@require_http_methods(["PATCH", "DELETE"])
@login_required
def toggle_long_term_completion(request, task_id: int):
    """
    PATCH -> set completed_at to the provided date (or now if missing)
    DELETE -> clear completed_at
    Query or body: date=YYYY-MM-DD (optional for PATCH)
    """
    try:
        task = Task.objects.get(id=task_id, user=request.user, task_type="long_term")
    except Task.DoesNotExist:
        return HttpResponseBadRequest("Task not found or not long_term")

    if request.method == "PATCH":
        date_str = request.POST.get("date") or request.GET.get("date")
        if date_str:
            d = _parse_date(date_str)
            if not d:
                return HttpResponseBadRequest("Invalid date")
            dt = timezone.make_aware(datetime(d.year, d.month, d.day))
        else:
            dt = timezone.now()
        # If your model lacks completed_at, add it; otherwise this line will error.
        task.completed_at = dt
        task.save(update_fields=["completed_at"])
        return JsonResponse({"ok": True, "completed_at": task.completed_at.isoformat()})
    else:  # DELETE
        if hasattr(task, "completed_at"):
            task.completed_at = None
            task.save(update_fields=["completed_at"])
        return JsonResponse({"ok": True, "completed_at": None})



@login_required
def calendar_feed(request):
    start = parse_datetime(request.GET.get("start", ""))
    end = parse_datetime(request.GET.get("end", ""))
    if start and timezone.is_naive(start): start = timezone.make_aware(start)
    if end and timezone.is_naive(end): end = timezone.make_aware(end)

    qs = Event.objects.filter(user=request.user)
    if start and end:
        qs = qs.filter(end_datetime__gte=start, start_datetime__lte=end)

    events = [{
        "id": ev.id,
        "title": ev.title,
        "start": ev.start_datetime.isoformat(),
        "end": ev.end_datetime.isoformat(),
        "allDay": ev.all_day,
    } for ev in qs]

    return JsonResponse(events, safe=False)
