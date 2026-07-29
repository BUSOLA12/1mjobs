from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from users.models import UserKYC
from adminpanel.utils.base_utils import log_admin_action


@staff_member_required
def admin_kyc_list(request):
    kycs = UserKYC.objects.select_related("user").order_by("-created_at")

    status = request.GET.get("status")
    if status:
        kycs = kycs.filter(verification_status=status)

    q = request.GET.get("q")
    if q:
        kycs = kycs.filter(
            Q(user__email__icontains=q)
            | Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
        )

    page_obj = Paginator(kycs, 15).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/kyc_management/list.html",
        {"page_obj": page_obj, "status": status or "", "q": q or ""},
    )


@staff_member_required
def admin_kyc_detail(request, pk):
    kyc = get_object_or_404(UserKYC.objects.select_related("user"), pk=pk)
    return render(request, "adminpanel/kyc_management/detail.html", {"kyc": kyc})


@staff_member_required
@require_POST
def admin_kyc_approve(request, pk):
    kyc = get_object_or_404(UserKYC, pk=pk)
    if not kyc.user.verified_email:
        messages.error(
            request,
            f"Cannot approve: {kyc.user.email} has not verified their email yet.",
        )
        return redirect("admin_kyc_detail", pk=pk)
    kyc.mark_approved(request.user)
    log_admin_action(request.user, kyc.user, "kyc_approve", f"Approved KYC for {kyc.user.email}.")
    if kyc.user.email:
        send_mail(
            "Your identity is verified",
            "Hello,\n\nYour identity has been verified and the verified badge now appears "
            "on your profile.\n\nThank you,\nOne Million Jobs",
            settings.DEFAULT_FROM_EMAIL,
            [kyc.user.email],
            fail_silently=True,
        )
    messages.success(request, f"KYC approved for {kyc.user.email}.")
    return redirect("admin_kyc_list")


@staff_member_required
@require_POST
def admin_kyc_reject(request, pk):
    kyc = get_object_or_404(UserKYC, pk=pk)
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Please provide a rejection reason.")
        return redirect("admin_kyc_detail", pk=pk)

    kyc.mark_rejected(request.user, reason)
    log_admin_action(request.user, kyc.user, "kyc_reject", f"Rejected KYC for {kyc.user.email}: {reason}")
    if kyc.user.email:
        resubmit_url = request.build_absolute_uri(reverse("verify_identity"))
        send_mail(
            "Your identity verification needs attention",
            f"Hello,\n\nYour identity documents could not be approved.\n\n"
            f"Reason: {reason}\n\nPlease re-upload here:\n{resubmit_url}\n\n"
            f"Thank you,\nOne Million Jobs",
            settings.DEFAULT_FROM_EMAIL,
            [kyc.user.email],
            fail_silently=True,
        )
    messages.success(request, f"KYC rejected; {kyc.user.email} notified.")
    return redirect("admin_kyc_list")
