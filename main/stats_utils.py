# stats_utils.py
from collections import defaultdict, OrderedDict
from datetime import timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from .models import DailyTaskCompletion


def _sunday_of(d):
    """Helper: return the Sunday of the given date."""
    return d - timedelta(days=(d.weekday() + 1) % 7)


def detect_granularity(query: str) -> str:
    """
    Try to guess the right granularity (day/week/month) from a query.
    Defaults to 'week' if unsure.
    """
    if not query:
        return "week"
    q = query.lower()
    if "day" in q or "yesterday" in q or "today" in q:
        return "day"
    if "month" in q or "monthly" in q:
        return "month"
    if "week" in q or "weekly" in q or "last 7 days" in q:
        return "week"
    return "week"


def get_completion_rate(user, granularity="week"):
    """
    Return completion rates over the last 12 periods (day/week/month).
    Each row: {date, label, created, completed, completion_rate}
    """
    today = timezone.localdate()

    if granularity == "month":
        current_start = today.replace(day=1)
        starts = [current_start - relativedelta(months=i) for i in range(11, -1, -1)]
        ends = [s + relativedelta(months=1) for s in starts]
        label_fmt = "%Y-%m"
    elif granularity == "week":
        current_start = _sunday_of(today)
        starts = [current_start - timedelta(weeks=i) for i in range(11, -1, -1)]
        ends = [s + timedelta(days=7) for s in starts]
        label_fmt = None  # handled below
    else:  # daily
        starts = [today - timedelta(days=i) for i in range(11, -1, -1)]
        ends = [s + timedelta(days=1) for s in starts]
        label_fmt = "%a %Y-%m-%d"

    range_start, range_end = starts[0], ends[-1]

    rows = (
        DailyTaskCompletion.objects
        .filter(task__user=user, date__gte=range_start, date__lt=range_end)
        .values("date", "completed")
    )

    buckets = OrderedDict((s, {"created": 0, "completed": 0}) for s in starts)

    def bucket_key(d):
        if granularity == "month":
            return d.replace(day=1)
        elif granularity == "week":
            return _sunday_of(d)
        else:
            return d

    for r in rows:
        key = bucket_key(r["date"])
        if key in buckets:
            buckets[key]["created"] += 1
            if r["completed"]:
                buckets[key]["completed"] += 1

    data = []
    for s in starts:
        created = buckets[s]["created"]
        completed = buckets[s]["completed"]
        rate = (completed / created) * 100.0 if created else 0.0
        if granularity == "week":
            label = f"{s.strftime('%b %d')} – {(s + timedelta(days=6)).strftime('%b %d')}"
        else:
            label = s.strftime(label_fmt)
        data.append({
            "date": s.isoformat(),
            "label": label,
            "created": created,
            "completed": completed,
            "completion_rate": round(rate, 2),
        })
    return data


def get_completed_daily_tasks_count(user, limit=10):
    """
    Return top N most completed tasks for the user.
    Format: [(task_title, count), ...]
    """
    completed_tasks = DailyTaskCompletion.objects.filter(task__user=user, completed=True)
    cntr = defaultdict(int)
    for c_task in completed_tasks:
        cntr[c_task.task.title.lower()] += 1
    return sorted(cntr.items(), key=lambda item: item[1], reverse=True)[:limit]


def get_per_task_completion_rate(user, granularity="count"):
    """
    Return per-task completion rates.
    If granularity='percentage' -> list of {'task': title, 'rate': percent}
    If granularity='count' -> list of {'task': title, 'rate': missed_count}
    """
    dtc_records = DailyTaskCompletion.objects.filter(task__user=user)
    created, completed = defaultdict(int), defaultdict(int)

    for dtc in dtc_records:
        created[dtc.task.title.lower()] += 1
        if dtc.completed:
            completed[dtc.task.title.lower()] += 1

    if granularity == 'percentage':
        return sorted(
            [
                {'task': t, 'rate': round(completed[t] / created[t], 2) * 100}
                for t in created
            ],
            key=lambda x: x['rate']
        )
    else:
        return sorted(
            [
                {'task': t, 'rate': created[t] - completed[t]}
                for t in created
            ],
            key=lambda x: x['rate'],
            reverse=True
        )
