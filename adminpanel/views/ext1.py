from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render

from ManageJobsTasks.models import Job
from adminpanel.utils.base_utils import log_admin_action


@staff_member_required
def admin_job_list(request):
    jobs = Job.objects.select_related("user").annotate(
        applications_count=Count("application")
    ).order_by("-created_at")

    # Filters
    status = request.GET.get("status")
    approved = request.GET.get("approved")
    job_type = request.GET.get("job_type")
    category = request.GET.get("category")
    q = request.GET.get("q")

    if status:
        jobs = jobs.filter(status=status)

    if approved in ["true", "false"]:
        jobs = jobs.filter(approved=(approved == "true"))

    if job_type:
        jobs = jobs.filter(job_type=job_type)

    if category:
        jobs = jobs.filter(category=category)

    if q:
        jobs = jobs.filter(
            Q(title__icontains=q) |
            Q(user__email__icontains=q) |
            Q(location__icontains=q)
        )

    paginator = Paginator(jobs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "adminpanel/jobs/list.html", {
        "jobs": page_obj,
        "status": status,
        "approved": approved,
        "job_type": job_type,
        "category": category,
        "q": q,
        "status_choices": Job._meta.get_field("status").choices,
        "job_types": Job._meta.get_field("job_type").choices,
        "categories": Job._meta.get_field("category").choices,
    })

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def admin_job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            job.approved = True
            job.status = "accepted"
            job.is_active = True
            job.save()
            messages.success(request, "Job approved successfully.")

        elif action == "reject":
            job.status = "rejected"
            job.approved = False
            job.is_active = False
            job.save()
            messages.warning(request, "Job rejected.")

        elif action == "deactivate":
            job.is_active = False
            job.save()
            messages.info(request, "Job deactivated.")

        elif action == "extend":
            job.expiration_date += timedelta(days=30)
            job.is_active = True
            job.save()
            messages.success(request, "Job expiration extended by 30 days.")

        return redirect("admin_job_detail", job_id=job.id)

    return render(request, "adminpanel/jobs/detail.html", {
        "job": job
    })


from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from ManageJobsTasks.models import JobApplication

@staff_member_required
def admin_job_applications_list(request, job_id):
    applications = JobApplication.objects.filter(job__id=job_id).select_related(
        'job', 'user'
    ).order_by('-created_at')

    return render(request, 'adminpanel/jobs/application_list.html', {
        'applications': applications
    })


@staff_member_required
def admin_job_application_detail(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status:
            application.status = new_status
            application.save()

    return render(request, 'adminpanel/jobs/application_detail.html', {
        'application': application,
        'status_choices': JobApplication._meta.get_field('status').choices
    })



from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from ManageJobsTasks.models import Task, TaskBidding

@staff_member_required
def admin_task_list(request):
    tasks = Task.objects.select_related('user').order_by('-created_at')

    return render(request, 'adminpanel/tasks/list.html', {
        'tasks': tasks,
        'now': timezone.now()
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST

@staff_member_required
def admin_task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    return render(request, 'adminpanel/tasks/detail.html', {
        'task': task,
        'status_choices': Task._meta.get_field('status').choices
    })


@staff_member_required
@require_POST
def admin_toggle_task_feature(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.is_featured = not task.is_featured
    task.save(update_fields=['is_featured'])

    log_admin_action(request.user, task, f"Toggle Task Feature to {task.is_featured}")

    messages.success(
        request,
        f"Task {'featured' if task.is_featured else 'unfeatured'} successfully."
    )
    return redirect('admin_task_detail', task_id=task.id)


@staff_member_required
@require_POST
def admin_update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    new_status = request.POST.get('status')

    allowed_statuses = dict(Task._meta.get_field('status').choices)
    if new_status not in allowed_statuses:
        messages.error(request, "Invalid status selected.")
        return redirect('admin_task_detail', task_id=task.id)

    task.status = new_status
    task.save(update_fields=['status'])

    log_admin_action(request.user, task, f"Updated Task Status to {new_status}")
    messages.success(request, "Task status updated successfully.")
    return redirect('admin_task_detail', task_id=task.id)


@staff_member_required
@require_POST
def admin_delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    task.delete()

    log_admin_action(request.user, task, "Deleted Task")
    messages.success(request, "Task deleted successfully.")
    return redirect('admin_task_list')

# tasks/admin_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST


@staff_member_required
def admin_task_bidding_list(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    bids = TaskBidding.objects.filter(task=task).select_related('freelancer')

    status = request.GET.get('status')
    if status:
        bids = bids.filter(status=status)

    return render(request, 'adminpanel/tasks/bidding_list.html', {
        'task': task,
        'bids': bids,
        'status_choices': TaskBidding._meta.get_field('status').choices
    })


@staff_member_required
@require_POST
def admin_update_task_bid_status(request, bid_id):
    bid = get_object_or_404(TaskBidding, id=bid_id)
    new_status = request.POST.get('status')

    allowed_statuses = dict(TaskBidding._meta.get_field('status').choices)
    if new_status not in allowed_statuses:
        messages.error(request, "Invalid status.")
        return redirect('admin_task_bidding_list', task_id=bid.task.id)

    bid.status = new_status
    bid.save(update_fields=['status'])

    log_admin_action(request.user, bid, f"Updated Bid Status to {new_status}")

    messages.success(request, "Bid status updated successfully.")
    return redirect('admin_task_bidding_list', task_id=bid.task.id)
