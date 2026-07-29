"""Site-admin (/site-admin/) management for freelancer withdrawals and contract
disputes. Mirrors the KYC/appeal management pattern: staff-only function views
with list/detail pages and POST actions, logging via log_admin_action."""

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from adminpanel.utils.base_utils import log_admin_action
from notifications.utils import create_notification
from payments.models import Withdrawal
from payments.services.withdrawal_service import WithdrawalService, WithdrawalError
from contracts.models import Dispute, TerminationRequest
from contracts import utils as contract_utils
from payments.services.payment_service import PaymentService


# ---------------------------------------------------------------------------
# Withdrawals
# ---------------------------------------------------------------------------

@staff_member_required
def admin_withdrawal_list(request):
    withdrawals = Withdrawal.objects.select_related("user").order_by("-created_at")

    status = request.GET.get("status")
    if status:
        withdrawals = withdrawals.filter(status=status)

    q = request.GET.get("q")
    if q:
        withdrawals = withdrawals.filter(
            Q(user__email__icontains=q)
            | Q(account_name__icontains=q)
            | Q(account_number__icontains=q)
            | Q(bank_name__icontains=q)
        )

    page_obj = Paginator(withdrawals, 15).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/withdrawals/list.html",
        {"page_obj": page_obj, "status": status or "", "q": q or ""},
    )


@staff_member_required
def admin_withdrawal_detail(request, pk):
    withdrawal = get_object_or_404(Withdrawal.objects.select_related("user"), pk=pk)
    wallet = getattr(withdrawal.user, "wallet", None)
    return render(
        request,
        "adminpanel/withdrawals/detail.html",
        {"w": withdrawal, "wallet": wallet},
    )


def _notify_withdrawal(user, title, message):
    create_notification(title=title, message=message, recipient=user)
    if user.email:
        send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


@staff_member_required
@require_POST
def admin_withdrawal_mark_paid(request, pk):
    withdrawal = get_object_or_404(Withdrawal, pk=pk)
    try:
        WithdrawalService.mark_paid(withdrawal)
    except WithdrawalError as e:
        messages.error(request, f"Could not mark paid: {e}")
        return redirect("admin_withdrawal_detail", pk=pk)

    log_admin_action(
        request.user, withdrawal.user, "withdrawal_paid",
        f"Paid withdrawal #{withdrawal.id} of NGN {withdrawal.amount} to {withdrawal.user.email}.",
    )
    _notify_withdrawal(
        withdrawal.user, "Your withdrawal has been paid",
        f"Your withdrawal of NGN {withdrawal.amount} has been processed to "
        f"{withdrawal.bank_name} ({withdrawal.account_number}).",
    )
    messages.success(request, f"Withdrawal #{withdrawal.id} marked paid and wallet debited.")
    return redirect("admin_withdrawal_list")


@staff_member_required
@require_POST
def admin_withdrawal_reject(request, pk):
    withdrawal = get_object_or_404(Withdrawal, pk=pk)
    reason = (request.POST.get("reason") or "").strip()
    if not reason:
        messages.error(request, "Please provide a rejection reason.")
        return redirect("admin_withdrawal_detail", pk=pk)
    try:
        WithdrawalService.reject(withdrawal, note=reason)
    except WithdrawalError as e:
        messages.error(request, f"Could not reject: {e}")
        return redirect("admin_withdrawal_detail", pk=pk)

    log_admin_action(
        request.user, withdrawal.user, "withdrawal_reject",
        f"Rejected withdrawal #{withdrawal.id}: {reason}",
    )
    _notify_withdrawal(
        withdrawal.user, "Your withdrawal request was declined",
        f"Your withdrawal of NGN {withdrawal.amount} could not be processed.\n\nReason: {reason}",
    )
    messages.success(request, f"Withdrawal #{withdrawal.id} rejected; {withdrawal.user.email} notified.")
    return redirect("admin_withdrawal_list")


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------

@staff_member_required
def admin_dispute_list(request):
    disputes = Dispute.objects.select_related("contract__job", "raised_by").order_by("-created_at")

    status = request.GET.get("status")
    if status:
        disputes = disputes.filter(status=status)

    q = request.GET.get("q")
    if q:
        disputes = disputes.filter(
            Q(contract__job__title__icontains=q)
            | Q(raised_by__email__icontains=q)
        )

    page_obj = Paginator(disputes, 15).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/disputes/list.html",
        {"page_obj": page_obj, "status": status or "", "q": q or ""},
    )


@staff_member_required
def admin_dispute_detail(request, pk):
    dispute = get_object_or_404(
        Dispute.objects.select_related("contract__job", "contract__employer", "contract__freelancer", "raised_by"),
        pk=pk,
    )
    contract = dispute.contract
    submissions = contract.submissions.prefetch_related("files").all()
    escrow_payment = contract.payments.filter(status="ESCROWED").order_by("-created_at").first()
    return render(
        request,
        "adminpanel/disputes/detail.html",
        {"d": dispute, "contract": contract, "submissions": submissions, "escrow_payment": escrow_payment},
    )


def _notify_both_parties(contract, title, message):
    for user in {contract.employer, contract.freelancer}:
        create_notification(title=title, message=message, recipient=user)
        if user.email:
            send_mail(title, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


@staff_member_required
@require_POST
def admin_dispute_under_review(request, pk):
    dispute = get_object_or_404(Dispute, pk=pk)
    if dispute.status == "open":
        dispute.status = "under_review"
        dispute.save(update_fields=["status"])
        log_admin_action(request.user, dispute.contract, "dispute_under_review", f"Dispute #{dispute.id} marked under review.")
        messages.success(request, "Dispute marked under review.")
    return redirect("admin_dispute_detail", pk=pk)


@staff_member_required
@require_POST
def admin_dispute_resolve_release(request, pk):
    from django.utils import timezone

    dispute = get_object_or_404(Dispute.objects.select_related("contract"), pk=pk)
    if dispute.status in ("resolved_released", "resolved_refunded"):
        messages.error(request, "This dispute is already resolved.")
        return redirect("admin_dispute_detail", pk=pk)

    contract = dispute.contract
    payment = contract.payments.filter(status="ESCROWED").order_by("-created_at").first()
    if not payment:
        messages.error(request, "No escrowed payment to release for this contract.")
        return redirect("admin_dispute_detail", pk=pk)

    PaymentService.release_payment(payment)
    contract.status = "completed"
    contract.save(update_fields=["status", "updated_at"])
    dispute.status = "resolved_released"
    dispute.admin_note = (request.POST.get("note") or "").strip()
    dispute.resolved_at = timezone.now()
    dispute.save(update_fields=["status", "admin_note", "resolved_at"])

    log_admin_action(request.user, contract, "dispute_resolve_release",
                     f"Dispute #{dispute.id}: released escrow to freelancer.")
    _notify_both_parties(
        contract, "Dispute resolved - funds released",
        f"The dispute on \"{contract.subject_title}\" was resolved. The escrowed funds were released to the freelancer.",
    )
    messages.success(request, "Dispute resolved: escrow released to the freelancer.")
    return redirect("admin_dispute_list")


@staff_member_required
@require_POST
def admin_dispute_resolve_refund(request, pk):
    from django.utils import timezone

    dispute = get_object_or_404(Dispute.objects.select_related("contract"), pk=pk)
    if dispute.status in ("resolved_released", "resolved_refunded"):
        messages.error(request, "This dispute is already resolved.")
        return redirect("admin_dispute_detail", pk=pk)

    contract = dispute.contract
    contract.status = "cancelled"
    contract.save(update_fields=["status", "updated_at"])
    dispute.status = "resolved_refunded"
    dispute.admin_note = (request.POST.get("note") or "").strip()
    dispute.resolved_at = timezone.now()
    dispute.save(update_fields=["status", "admin_note", "resolved_at"])

    log_admin_action(request.user, contract, "dispute_resolve_refund",
                     f"Dispute #{dispute.id}: refunded employer (handled off-platform), contract cancelled.")
    _notify_both_parties(
        contract, "Dispute resolved - refund to employer",
        f"The dispute on \"{contract.subject_title}\" was resolved in favour of the employer. "
        f"The contract was cancelled; any refund is handled by our team directly.",
    )
    messages.success(request, "Dispute resolved: contract cancelled (refund handled off-platform).")
    return redirect("admin_dispute_list")


# ---------------------------------------------------------------------------
# Termination requests
# ---------------------------------------------------------------------------

@staff_member_required
def admin_termination_list(request):
    reqs = TerminationRequest.objects.select_related(
        "contract__job", "contract__task", "requested_by"
    ).order_by("-created_at")

    status = request.GET.get("status")
    if status:
        reqs = reqs.filter(status=status)

    q = request.GET.get("q")
    if q:
        reqs = reqs.filter(
            Q(contract__job__title__icontains=q)
            | Q(contract__task__project_name__icontains=q)
            | Q(requested_by__email__icontains=q)
        )

    page_obj = Paginator(reqs, 15).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/terminations/list.html",
        {"page_obj": page_obj, "status": status or "", "q": q or ""},
    )


@staff_member_required
def admin_termination_detail(request, pk):
    tr = get_object_or_404(
        TerminationRequest.objects.select_related(
            "contract__job", "contract__task", "contract__employer", "contract__freelancer", "requested_by"
        ),
        pk=pk,
    )
    contract = tr.contract
    periods = contract.periods.all()
    return render(
        request,
        "adminpanel/terminations/detail.html",
        {"t": tr, "contract": contract, "periods": periods},
    )


@staff_member_required
@require_POST
def admin_termination_execute(request, pk):
    from django.utils import timezone
    from contracts.billing import settle_funded_periods

    tr = get_object_or_404(TerminationRequest.objects.select_related("contract"), pk=pk)
    if tr.status != "pending":
        messages.error(request, "This request is already resolved.")
        return redirect("admin_termination_detail", pk=pk)

    contract = tr.contract
    released = settle_funded_periods(contract)
    contract.status = "terminated"
    contract.save(update_fields=["status", "updated_at"])

    tr.status = "approved"
    tr.admin_note = (request.POST.get("note") or "").strip()
    tr.resolved_by = request.user
    tr.resolved_at = timezone.now()
    tr.save(update_fields=["status", "admin_note", "resolved_by", "resolved_at"])

    log_admin_action(request.user, contract, "terminate_contract",
                     f"Terminated contract {contract.id}; settled {released} funded period(s) to the freelancer.")
    contract_utils.notify_termination_result(tr)
    messages.success(request, f"Contract terminated; {released} funded period(s) released to the freelancer.")
    return redirect("admin_termination_list")


@staff_member_required
@require_POST
def admin_termination_deny(request, pk):
    from django.utils import timezone
    from contracts.billing import recompute_active_status

    tr = get_object_or_404(TerminationRequest.objects.select_related("contract"), pk=pk)
    if tr.status != "pending":
        messages.error(request, "This request is already resolved.")
        return redirect("admin_termination_detail", pk=pk)

    contract = tr.contract
    contract.status = recompute_active_status(contract)
    contract.save(update_fields=["status", "updated_at"])

    tr.status = "denied"
    tr.admin_note = (request.POST.get("note") or "").strip()
    tr.resolved_by = request.user
    tr.resolved_at = timezone.now()
    tr.save(update_fields=["status", "admin_note", "resolved_by", "resolved_at"])

    log_admin_action(request.user, contract, "deny_termination", f"Denied termination on contract {contract.id}.")
    contract_utils.notify_termination_result(tr)
    messages.success(request, "Termination denied; the contract continues.")
    return redirect("admin_termination_list")
