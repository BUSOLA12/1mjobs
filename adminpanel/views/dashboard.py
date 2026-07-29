from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta

from users.models import CustomUser
from ManageJobsTasks.models import Job, JobApplication, Task, TaskBidding
from pricing.models import Order, Subscription, Transaction

from django.core.cache import cache
from ..utils.metrics import daily_count, daily_sum


def _continuous_series(rows, value_key, days=7):
    """Turn a sparse queryset of {day, value} rows into a dense, ordered
    (labels, data) pair covering the last `days` days, filling gaps with 0."""
    today = timezone.localtime(timezone.now()).date()
    start = today - timedelta(days=days - 1)
    bucket = {start + timedelta(days=i): 0 for i in range(days)}
    for row in rows:
        day = row.get("day")
        if day in bucket:
            bucket[day] = row.get(value_key) or 0
    ordered = sorted(bucket.items())
    labels = [day.strftime("%a %d") for day, _ in ordered]
    data = [value for _, value in ordered]
    return labels, data


def _trend(current, previous):
    """Period-over-period delta as a signed percentage, plus direction."""
    if previous:
        pct = round(((current - previous) / previous) * 100, 1)
    else:
        pct = 100.0 if current else 0.0
    return {"pct": abs(pct), "up": current >= previous}


def admin_dashboard(request):
    now = timezone.now()

    # ---- Time ranges ----
    last_24h = now - timedelta(hours=24)
    prev_24h = now - timedelta(hours=48)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # ---- Jobs ----
    jobs_24h = Job.objects.filter(created_at__gte=last_24h).count()
    jobs_7d = Job.objects.filter(created_at__gte=last_7d).count()
    jobs_30d = Job.objects.filter(created_at__gte=last_30d).count()
    jobs_prev_24h = Job.objects.filter(created_at__gte=prev_24h, created_at__lt=last_24h).count()

    pending_jobs = Job.objects.filter(status="pending").count()

    # ---- Tasks ----
    tasks_24h = Task.objects.filter(created_at__gte=last_24h).count()
    tasks_7d = Task.objects.filter(created_at__gte=last_7d).count()
    tasks_30d = Task.objects.filter(created_at__gte=last_30d).count()
    tasks_prev_24h = Task.objects.filter(created_at__gte=prev_24h, created_at__lt=last_24h).count()

    # ---- Users ----
    users_24h = CustomUser.objects.filter(date_joined__gte=last_24h).count()
    users_7d = CustomUser.objects.filter(date_joined__gte=last_7d).count()
    users_30d = CustomUser.objects.filter(date_joined__gte=last_30d).count()
    users_prev_24h = CustomUser.objects.filter(date_joined__gte=prev_24h, date_joined__lt=last_24h).count()

    suspended_users = CustomUser.objects.filter(account_status="suspended").count()

    # ---- Engagement ----
    avg_applications_per_job = (
        Job.objects.annotate(app_count=Count("application"))
        .aggregate(avg=Avg("app_count"))["avg"] or 0
    )

    avg_bids_per_task = (
        Task.objects.annotate(bid_count=Count("bidding"))
        .aggregate(avg=Avg("bid_count"))["avg"] or 0
    )

    pending_applications = JobApplication.objects.filter(status="pending").count()
    pending_bids = TaskBidding.objects.filter(status="pending").count()

    # ---- Revenue ----
    revenue_today = (
        Order.objects.filter(status="paid", created_at__date=now.date())
        .aggregate(total=Sum("amount"))["total"] or 0
    )
    revenue_yesterday = (
        Order.objects.filter(status="paid", created_at__date=(now - timedelta(days=1)).date())
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    revenue_30d = (
        Order.objects.filter(status="paid", created_at__gte=last_30d)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    # ---- Revenue by plan (last 30 days, paid) ----
    plan_rows = (
        Order.objects.filter(status="paid", created_at__gte=last_30d)
        .values("plan__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )
    revenue_by_plan_labels = []
    revenue_by_plan_data = []
    for row in plan_rows:
        revenue_by_plan_labels.append(row["plan__name"] or "Other")
        revenue_by_plan_data.append(float(row["total"] or 0))

    active_subscriptions = Subscription.objects.filter(is_active=True).count()

    total_transactions = Transaction.objects.count()
    successful_transactions = Transaction.objects.filter(status="success").count()

    payment_success_rate = (
        round((successful_transactions / total_transactions) * 100, 2)
        if total_transactions > 0 else 0
    )

    # ---- Chart series (last 7 days, gap-filled) ----
    cache_key = "admin_dashboard_charts_v2"
    charts = cache.get(cache_key)

    if not charts:
        labels, jobs_series = _continuous_series(
            daily_count(Job.objects.all(), days=7), "count"
        )
        _, tasks_series = _continuous_series(
            daily_count(Task.objects.all(), days=7), "count"
        )
        _, users_series = _continuous_series(
            daily_count(CustomUser.objects.all(), date_field="date_joined", days=7), "count"
        )
        _, revenue_series = _continuous_series(
            daily_sum(Order.objects.filter(status="paid"), field="amount", days=7), "total"
        )
        charts = {
            "labels": labels,
            "jobs": jobs_series,
            "tasks": tasks_series,
            "users": users_series,
            "revenue": [float(v) for v in revenue_series],
        }
        cache.set(cache_key, charts, timeout=60 * 10)

    context = {
        # Jobs
        "jobs_24h": jobs_24h,
        "jobs_7d": jobs_7d,
        "jobs_30d": jobs_30d,
        "jobs_trend": _trend(jobs_24h, jobs_prev_24h),
        "pending_jobs": pending_jobs,

        # Tasks
        "tasks_24h": tasks_24h,
        "tasks_7d": tasks_7d,
        "tasks_30d": tasks_30d,
        "tasks_trend": _trend(tasks_24h, tasks_prev_24h),

        # Users
        "users_24h": users_24h,
        "users_7d": users_7d,
        "users_30d": users_30d,
        "users_trend": _trend(users_24h, users_prev_24h),
        "suspended_users": suspended_users,

        # Engagement
        "avg_applications_per_job": round(avg_applications_per_job, 2),
        "avg_bids_per_task": round(avg_bids_per_task, 2),
        "pending_applications": pending_applications,
        "pending_bids": pending_bids,

        # Revenue
        "revenue_today": revenue_today,
        "revenue_30d": revenue_30d,
        "revenue_trend": _trend(float(revenue_today), float(revenue_yesterday)),
        "active_subscriptions": active_subscriptions,
        "payment_success_rate": payment_success_rate,
        "revenue_by_plan_labels": revenue_by_plan_labels,
        "revenue_by_plan_data": revenue_by_plan_data,

        # Chart series
        "chart_labels": charts["labels"],
        "jobs_series": charts["jobs"],
        "tasks_series": charts["tasks"],
        "users_series": charts["users"],
        "revenue_series": charts["revenue"],
    }

    return render(request, "adminpanel/dashboard/index.html", context)
