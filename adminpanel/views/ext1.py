from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from ManageJobsTasks.models import Job, JobCategory
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
            log_admin_action(request.user, job, "Approved Job")
            messages.success(request, "Job approved successfully.")

        elif action == "reject":
            job.status = "rejected"
            job.approved = False
            job.is_active = False
            job.save()
            log_admin_action(request.user, job, "Rejected Job")
            messages.warning(request, "Job rejected.")

        elif action == "deactivate":
            job.is_active = False
            job.save()
            log_admin_action(request.user, job, "Deactivated Job")
            messages.info(request, "Job deactivated.")

        elif action == "extend":
            job.expiration_date += timedelta(days=30)
            job.is_active = True
            job.save()
            log_admin_action(request.user, job, "Extended Job Expiration by 30 days")
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
            log_admin_action(request.user, application, f"Updated Job Application Status to {new_status}")

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

    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)

    featured = request.GET.get('featured')
    if featured in ['true', 'false']:
        tasks = tasks.filter(is_featured=(featured == 'true'))

    q = request.GET.get('q')
    if q:
        tasks = tasks.filter(
            Q(project_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(category__icontains=q)
        )

    page_obj = Paginator(tasks, 15).get_page(request.GET.get('page'))

    return render(request, 'adminpanel/tasks/list.html', {
        'tasks': page_obj,
        'now': timezone.now(),
        'status': status or '',
        'featured': featured or '',
        'q': q or '',
        'status_choices': Task._meta.get_field('status').choices,
    })

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_POST

@staff_member_required
def admin_task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            task.approved = True
            task.status = "active"
            task.save(update_fields=["approved", "status"])
            log_admin_action(request.user, task, "Approved Task")
            messages.success(request, "Task approved and is now live.")

        elif action == "reject":
            task.approved = False
            task.status = "cancelled"
            task.save(update_fields=["approved", "status"])
            log_admin_action(request.user, task, "Rejected Task")
            messages.warning(request, "Task rejected. It stays hidden from the public list.")

        return redirect("admin_task_detail", task_id=task.id)

    return render(request, 'adminpanel/tasks/detail.html', {
        'task': task,
        'status_choices': Task._meta.get_field('status').choices,
        # Real bid count (the Task.applications_count/views_count fields are never
        # populated in app code, so show the actual TaskBidding total instead).
        'bids_count': TaskBidding.objects.filter(task=task).count(),
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


# ---------------------------------------------------------------------------
# Job categories (admin-managed; feeds the job-post form dropdown)
# ---------------------------------------------------------------------------

def _unique_category_slug(name):
    # Match the existing convention (e.g. "accounting_and_finance"): slugify
    # gives hyphens, so swap them for underscores.
    base = slugify(name).replace("-", "_") or "category"
    slug = base
    i = 2
    while JobCategory.objects.filter(slug=slug).exists():
        slug = f"{base}_{i}"
        i += 1
    return slug


@staff_member_required
def admin_job_category_list(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            messages.error(request, "Category name is required.")
        elif JobCategory.objects.filter(name__iexact=name).exists():
            messages.error(request, f'A category named "{name}" already exists.')
        else:
            category = JobCategory.objects.create(name=name, slug=_unique_category_slug(name))
            log_admin_action(request.user, category, "job_category_create", f'Created job category "{name}".')
            messages.success(request, f'Category "{name}" created.')
        return redirect("admin_job_category_list")

    categories = JobCategory.objects.order_by("name")

    search = (request.GET.get("q") or "").strip()
    if search:
        categories = categories.filter(name__icontains=search)

    page_obj = Paginator(categories, 15).get_page(request.GET.get("page"))

    # Job.category stores the slug (no FK), so count jobs per slug in one query
    # and attach it to each category on the current page.
    slug_counts = dict(
        Job.objects.values_list("category").annotate(n=Count("id")).values_list("category", "n")
    )
    for cat in page_obj:
        cat.job_count = slug_counts.get(cat.slug, 0)

    return render(request, "adminpanel/job_categories/list.html", {
        "page_obj": page_obj,
        "q": search,
        "total": JobCategory.objects.count(),
    })


@staff_member_required
@require_POST
def admin_job_category_toggle(request, pk):
    category = get_object_or_404(JobCategory, pk=pk)
    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])
    state = "activated" if category.is_active else "deactivated"
    log_admin_action(request.user, category, "job_category_toggle", f'{state.capitalize()} job category "{category.name}".')
    messages.success(request, f'Category "{category.name}" {state}.')
    return redirect("admin_job_category_list")


@staff_member_required
@require_POST
def admin_job_category_delete(request, pk):
    category = get_object_or_404(JobCategory, pk=pk)
    name = category.name
    used = Job.objects.filter(category=category.slug).count()
    if used:
        messages.error(
            request,
            f'Cannot delete "{name}" - it is used by {used} job(s). Deactivate it instead to hide it from the job form.',
        )
        return redirect("admin_job_category_list")
    log_admin_action(request.user, None, "job_category_delete", f'Deleted job category "{name}".')
    category.delete()
    messages.success(request, f'Category "{name}" deleted.')
    return redirect("admin_job_category_list")
