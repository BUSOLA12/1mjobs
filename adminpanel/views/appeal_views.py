from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from users.models import Appeal
from adminpanel.utils.base_utils import log_admin_action


@staff_member_required
def admin_appeal_list(request):
    appeals = Appeal.objects.select_related("user").order_by("-created_at")

    status = request.GET.get("status")
    if status:
        appeals = appeals.filter(status=status)

    q = request.GET.get("q")
    if q:
        appeals = appeals.filter(
            Q(user__email__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )

    page_obj = Paginator(appeals, 15).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/appeal_management/list.html",
        {"page_obj": page_obj, "status": status or "", "q": q or ""},
    )


@staff_member_required
def admin_appeal_detail(request, pk):
    appeal = get_object_or_404(Appeal.objects.select_related("user", "reviewed_by"), pk=pk)
    return render(request, "adminpanel/appeal_management/detail.html", {"appeal": appeal})


@staff_member_required
@require_POST
def admin_appeal_approve(request, pk):
    appeal = get_object_or_404(Appeal.objects.select_related("user"), pk=pk)
    user = appeal.user

    # Restore the account. Unban takes priority since a banned user may also
    # carry a stale suspended flag.
    if user.is_banned or user.account_status == "banned":
        user.unban()
        action = "appeal_approve_unban"
    else:
        user.unsuspend()
        action = "appeal_approve_unsuspend"

    appeal.status = "approved"
    appeal.reviewed_by = request.user
    appeal.reviewed_at = timezone.now()
    appeal.admin_response = (request.POST.get("response") or "").strip()
    appeal.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_response"])

    log_admin_action(request.user, user, action, f"Approved appeal #{appeal.id} and restored {user.email}.")

    if user.email:
        note = f"\n\nNote from our team: {appeal.admin_response}" if appeal.admin_response else ""
        send_mail(
            "Your appeal has been approved",
            f"Hello,\n\nGood news: your appeal has been approved and your account has "
            f"been reinstated. You can now log in as usual.{note}\n\n"
            f"Thank you,\nOne Million Jobs",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
    messages.success(request, f"Appeal approved; {user.email} reinstated and notified.")
    return redirect("admin_appeal_list")


@staff_member_required
@require_POST
def admin_appeal_reject(request, pk):
    appeal = get_object_or_404(Appeal.objects.select_related("user"), pk=pk)
    response = (request.POST.get("response") or "").strip()
    if not response:
        messages.error(request, "Please provide a reason so the user understands the decision.")
        return redirect("admin_appeal_detail", pk=pk)

    appeal.status = "rejected"
    appeal.reviewed_by = request.user
    appeal.reviewed_at = timezone.now()
    appeal.admin_response = response
    appeal.save(update_fields=["status", "reviewed_by", "reviewed_at", "admin_response"])

    log_admin_action(request.user, appeal.user, "appeal_reject", f"Rejected appeal #{appeal.id}: {response}")

    if appeal.user.email:
        send_mail(
            "Update on your appeal",
            f"Hello,\n\nWe have reviewed your appeal and it was not approved at this time.\n\n"
            f"Reason: {response}\n\nThank you,\nOne Million Jobs",
            settings.DEFAULT_FROM_EMAIL,
            [appeal.user.email],
            fail_silently=True,
        )
    messages.success(request, f"Appeal rejected; {appeal.user.email} notified.")
    return redirect("admin_appeal_list")
