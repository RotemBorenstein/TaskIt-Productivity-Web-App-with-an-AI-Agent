# main/admin.py
from django.contrib import admin
from django.utils import timezone
from datetime import datetime, time, timedelta
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_datetime", "end_datetime", "all_day")
    list_filter = ("all_day", "start_datetime")
    search_fields = ("title", "description")
    date_hierarchy = "start_datetime"
    ordering = ("-start_datetime",)
    exclude = ("user",)  # set automatically

    def save_model(self, request, obj, form, change):
        # Auto-assign creator if empty
        if not obj.user_id:
            obj.user = request.user

        # Normalize all-day events to midnight boundaries (end is exclusive)
        if obj.all_day:
            tz = timezone.get_current_timezone()

            # If start is missing (shouldn't be, but just in case), use today
            if obj.start_datetime:
                start_date = obj.start_datetime.astimezone(tz).date()
            else:
                start_date = timezone.localdate()

            # If end provided, use its date; otherwise default to same start day
            if obj.end_datetime:
                end_date = obj.end_datetime.astimezone(tz).date()
                # Guard: don’t allow end before start
                if end_date < start_date:
                    end_date = start_date
            else:
                end_date = start_date

            # Build aware datetimes at local midnight
            start_dt = timezone.make_aware(datetime.combine(start_date, time.min), tz)
            # FullCalendar expects end to be exclusive midnight *after* the last day
            end_dt = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min), tz)

            obj.start_datetime = start_dt
            obj.end_datetime = end_dt

        super().save_model(request, obj, form, change)
