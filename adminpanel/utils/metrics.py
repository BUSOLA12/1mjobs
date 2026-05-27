# admin_panel/utils/metrics.py
from django.db.models.functions import TruncDate
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

def daily_count(queryset, date_field="created_at", days=7):
    start_date = timezone.now() - timedelta(days=days)

    qs = (
        queryset.filter(**{f"{date_field}__gte": start_date})
        .annotate(day=TruncDate(date_field))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    return qs


def daily_sum(queryset, field, days=7):
    start_date = timezone.now() - timedelta(days=days)

    qs = (
        queryset.filter(created_at__gte=start_date)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum(field))
        .order_by("day")
    )

    return qs
