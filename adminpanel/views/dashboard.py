from django.shortcuts import render
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta

from users.models import CustomUser
from ManageJobsTasks.models import Job, JobApplication, Task, TaskBidding
from pricing.models import Order, Subscription, Transaction

from django.core.cache import cache
from ..utils.metrics import daily_count, daily_sum


def admin_dashboard(request):
    now = timezone.now()

    # ---- Time ranges ----
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    last_30d = now - timedelta(days=30)

    # ---- Jobs ----
    jobs_24h = Job.objects.filter(created_at__gte=last_24h).count()
    jobs_7d = Job.objects.filter(created_at__gte=last_7d).count()
    jobs_30d = Job.objects.filter(created_at__gte=last_30d).count()

    pending_jobs = Job.objects.filter(status="pending").count()

    # ---- Tasks ----
    tasks_24h = Task.objects.filter(created_at__gte=last_24h).count()
    tasks_7d = Task.objects.filter(created_at__gte=last_7d).count()
    tasks_30d = Task.objects.filter(created_at__gte=last_30d).count()

    # ---- Users ----
    users_24h = CustomUser.objects.filter(date_joined__gte=last_24h).count()
    users_7d = CustomUser.objects.filter(date_joined__gte=last_7d).count()
    users_30d = CustomUser.objects.filter(date_joined__gte=last_30d).count()

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

    revenue_30d = (
        Order.objects.filter(status="paid", created_at__gte=last_30d)
        .aggregate(total=Sum("amount"))["total"] or 0
    )

    active_subscriptions = Subscription.objects.filter(is_active=True).count()

    total_transactions = Transaction.objects.count()
    successful_transactions = Transaction.objects.filter(status="success").count()

    payment_success_rate = (
        round((successful_transactions / total_transactions) * 100, 2)
        if total_transactions > 0 else 0
    )

    cache_key = "admin_dashboard_charts"
    charts = cache.get(cache_key)

    if not charts:
        charts = {
            "jobs": list(daily_count(Job.objects.all(), days=7)),
            "tasks": list(daily_count(Task.objects.all(), days=7)),
            "users": list(daily_count(CustomUser.objects.all(), date_field="date_joined", days=7)),
            "revenue": list(
                daily_sum(
                    Order.objects.filter(status="paid"),
                    field="amount",
                    days=7
                )
            ),
        }
        cache.set(cache_key, charts, timeout=60 * 30)

    context = {
        # Jobs
        "jobs_24h": jobs_24h,
        "jobs_7d": jobs_7d,
        "jobs_30d": jobs_30d,
        "pending_jobs": pending_jobs,

        # Tasks
        "tasks_24h": tasks_24h,
        "tasks_7d": tasks_7d,
        "tasks_30d": tasks_30d,

        # Users
        "users_24h": users_24h,
        "users_7d": users_7d,
        "users_30d": users_30d,
        "suspended_users": suspended_users,

        # Engagement
        "avg_applications_per_job": round(avg_applications_per_job, 2),
        "avg_bids_per_task": round(avg_bids_per_task, 2),
        "pending_applications": pending_applications,
        "pending_bids": pending_bids,

        # Revenue
        "revenue_today": revenue_today,
        "revenue_30d": revenue_30d,
        "active_subscriptions": active_subscriptions,
        "payment_success_rate": payment_success_rate,
    }

    return render(request, "adminpanel/dashboard/index.html", context)
