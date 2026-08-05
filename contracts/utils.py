"""Notifications for the hiring flow (offers).

Emails reuse the same EmailMultiAlternatives + render_to_string pattern as
ManageJobsTasks.utils, and in-app alerts go through notifications.create_notification.
All email sends are best-effort: a mail outage must never break the offer flow.
"""

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from notifications.utils import create_notification


def _abs_url(request, path):
    if request is not None:
        return request.build_absolute_uri(path)
    return settings.FRONTEND_URL.rstrip("/") + path


def _offer_links(offer):
    """(subject_title, freelancer_review_path, employer_review_path) for a Job or
    Task offer. Task offers point the freelancer at My Active Bids and the
    employer at Manage Bidders; job offers at My Applications / Manage Candidates."""
    if getattr(offer, "task_id", None):
        return (
            offer.task.project_name,
            reverse("dashboard_my_active_bids"),
            reverse("dashboard_manage_bidders", args=[offer.task_id]),
        )
    return (
        offer.job.title,
        reverse("dashboard_my_applications"),
        reverse("dashboard_manage_candidates", args=[offer.job_id]),
    )


def notify_freelancer_of_offer(offer, request=None):
    """Email + in-app notify the freelancer that they received an offer."""
    freelancer = offer.freelancer
    employer_name = offer.employer.get_full_name or "The employer"
    subject_title, fr_path, _emp_path = _offer_links(offer)

    link = _abs_url(request, fr_path)
    site_url = _abs_url(request, "/")

    # In-app notification (safe, no email exposed).
    create_notification(
        title="You received an offer",
        message=f"{employer_name} sent you an offer for \"{subject_title}\": NGN {offer.amount}, {offer.delivery_days} day(s).",
        recipient=freelancer,
        related_object=offer,
    )

    to_email = getattr(freelancer, "email", None)
    if not to_email:
        return

    subject = f"You received an offer for: {subject_title}"
    context = {
        "freelancer_name": freelancer.get_full_name or freelancer.email,
        "employer_name": employer_name,
        "job_title": subject_title,
        "amount": offer.amount,
        "delivery_days": offer.delivery_days,
        "note": offer.note,
        "link": link,
        "site_url": site_url,
    }
    text_body = (
        f"{employer_name} sent you an offer for \"{subject_title}\".\n\n"
        f"Amount: NGN {offer.amount}\n"
        f"Delivery time: {offer.delivery_days} day(s)\n"
        f"{('Note: ' + offer.note + chr(10)) if offer.note else ''}\n"
        f"Review and respond here: {link}\n\n"
        f"Opportunity Hub"
    )
    try:
        html_body = render_to_string("emails/job_offer_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject, body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        print(f"Failed to send offer email to freelancer: {e}")


def notify_employer_of_offer_response(offer, request=None):
    """Email + in-app notify the employer that the freelancer accepted/rejected."""
    employer = offer.employer
    freelancer_name = offer.freelancer.get_full_name or "The freelancer"
    accepted = offer.status == "accepted"
    outcome = "accepted" if accepted else "declined"
    subject_title, _fr_path, emp_path = _offer_links(offer)

    link = _abs_url(request, emp_path)
    site_url = _abs_url(request, "/")

    create_notification(
        title=f"Offer {outcome}",
        message=f"{freelancer_name} {outcome} your offer for \"{subject_title}\".",
        recipient=employer,
        related_object=offer,
    )

    to_email = getattr(employer, "email", None)
    if not to_email:
        return

    subject = f"Your offer was {outcome}: {subject_title}"
    context = {
        "employer_name": employer.get_full_name or employer.email,
        "freelancer_name": freelancer_name,
        "job_title": subject_title,
        "outcome": outcome,
        "accepted": accepted,
        "amount": offer.amount,
        "delivery_days": offer.delivery_days,
        "link": link,
        "site_url": site_url,
    }
    text_body = (
        f"{freelancer_name} has {outcome} your offer for \"{subject_title}\".\n\n"
        f"Amount: NGN {offer.amount}\n"
        f"Delivery time: {offer.delivery_days} day(s)\n\n"
        f"View here: {link}\n\n"
        f"Opportunity Hub"
    )
    try:
        html_body = render_to_string("emails/job_offer_response_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject, body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        print(f"Failed to send offer-response email to employer: {e}")


def notify_freelancer_escrow_funded(contract, request=None):
    """Email + in-app notify the freelancer that escrow is funded and they can start."""
    freelancer = contract.freelancer
    subject_title = contract.subject_title

    link = _abs_url(request, reverse("dashboard_contract_detail", args=[contract.id]))
    site_url = _abs_url(request, "/")

    create_notification(
        title="Escrow funded, you can start",
        message=f"The employer funded escrow (NGN {contract.amount}) for \"{subject_title}\". You can begin the work.",
        recipient=freelancer,
        related_object=contract,
    )

    to_email = getattr(freelancer, "email", None)
    if not to_email:
        return

    subject = f"Escrow funded: {subject_title}"
    context = {
        "freelancer_name": freelancer.get_full_name or freelancer.email,
        "job_title": subject_title,
        "amount": contract.amount,
        "delivery_days": contract.delivery_days,
        "link": link,
        "site_url": site_url,
    }
    text_body = (
        f"Good news: escrow has been funded for \"{subject_title}\".\n\n"
        f"Amount held: NGN {contract.amount}\n"
        f"Delivery time: {contract.delivery_days} day(s)\n\n"
        f"Open your contract to download any documents and start working: {link}\n\n"
        f"Opportunity Hub"
    )
    try:
        html_body = render_to_string("emails/contract_funded_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject, body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        print(f"Failed to send escrow-funded email to freelancer: {e}")


def _notify_contract_event(recipient, contract, title, subject, lines, request=None):
    """Generic contract-event notifier: writes an in-app notification and sends
    an email built from a shared template. Best-effort on the email side."""
    link = _abs_url(request, reverse("dashboard_contract_detail", args=[contract.id]))
    site_url = _abs_url(request, "/")

    create_notification(title=title, message=" ".join(lines), recipient=recipient, related_object=contract)

    to_email = getattr(recipient, "email", None)
    if not to_email:
        return
    context = {"title": title, "lines": lines, "link": link, "site_url": site_url}
    text_body = f"{title}\n\n" + "\n".join(lines) + f"\n\nView the contract: {link}\n\nOpportunity Hub"
    try:
        html_body = render_to_string("emails/contract_event_notification.html", context)
        email = EmailMultiAlternatives(
            subject=subject, body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL, to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send(fail_silently=True)
    except Exception as e:
        print(f"Failed to send contract-event email: {e}")


def notify_employer_of_submission(contract, submission, request=None):
    _notify_contract_event(
        contract.employer, contract,
        title="Work submitted for review",
        subject=f"Work submitted: {contract.subject_title}",
        lines=[
            f"The freelancer submitted their work (v{submission.version}) for \"{contract.subject_title}\".",
            "Review it and accept, request a change, or reject.",
        ],
        request=request,
    )


def notify_freelancer_work_accepted(contract, net_amount, request=None):
    _notify_contract_event(
        contract.freelancer, contract,
        title="Work accepted, payment released",
        subject=f"Payment released: {contract.subject_title}",
        lines=[
            f"The client accepted your work on \"{contract.subject_title}\".",
            f"NGN {net_amount} has been released to your wallet (after the platform fee and VAT).",
        ],
        request=request,
    )


def notify_freelancer_revision_requested(contract, note, request=None):
    lines = [f"The client requested a change on \"{contract.subject_title}\"."]
    if note:
        lines.append(f"Note: {note}")
    lines.append("Update your work and submit again.")
    _notify_contract_event(
        contract.freelancer, contract,
        title="Revision requested",
        subject=f"Revision requested: {contract.subject_title}",
        lines=lines, request=request,
    )


def notify_dispute_opened(dispute, request=None):
    """Notify the other party (the one who did not raise the dispute)."""
    contract = dispute.contract
    other = contract.freelancer if dispute.raised_by_id == contract.employer_id else contract.employer
    _notify_contract_event(
        other, contract,
        title="A dispute was opened",
        subject=f"Dispute opened: {contract.subject_title}",
        lines=[
            f"A dispute was opened on \"{contract.subject_title}\".",
            f"Reason: {dispute.reason}",
            "Our team will review it. The escrowed funds stay held until it is resolved.",
        ],
        request=request,
    )


# --- Recurring (Job) billing-period notifications ---

def notify_period_funded(period, request=None):
    contract = period.contract
    _notify_contract_event(
        contract.freelancer, contract,
        title="Escrow funded for this period",
        subject=f"Escrow funded: {contract.subject_title}",
        lines=[
            f"The client funded escrow (NGN {period.amount}) for period {period.period_number} of \"{contract.subject_title}\".",
            "Keep working; payment releases to your wallet after the review window at period end.",
        ],
        request=request,
    )


def notify_funding_reminder(period, request=None):
    contract = period.contract
    due = period.funding_due_date.strftime("%d %b %Y")
    _notify_contract_event(
        contract.employer, contract,
        title="Fund the next period's escrow",
        subject=f"Reminder: fund escrow for {contract.subject_title}",
        lines=[
            f"Escrow for period {period.period_number} of \"{contract.subject_title}\" (NGN {period.amount}) is due by {due}.",
            "Fund it before the period begins so work can continue without interruption.",
        ],
        request=request,
    )


def notify_period_released(period, net_amount, request=None):
    contract = period.contract
    _notify_contract_event(
        contract.freelancer, contract,
        title="Payment released",
        subject=f"Payment released: {contract.subject_title}",
        lines=[
            f"Period {period.period_number} of \"{contract.subject_title}\" passed its review window and was released.",
            f"NGN {net_amount} has been added to your wallet (after the platform fee and VAT).",
        ],
        request=request,
    )


def notify_missed_funding(period, request=None):
    """Notify both parties that a period's funding due date passed unfunded."""
    contract = period.contract
    _notify_contract_event(
        contract.employer, contract,
        title="Funding overdue",
        subject=f"Funding overdue: {contract.subject_title}",
        lines=[
            f"Period {period.period_number} of \"{contract.subject_title}\" was not funded by its due date.",
            "Fund escrow now to keep the engagement active and avoid termination.",
        ],
        request=request,
    )
    _notify_contract_event(
        contract.freelancer, contract,
        title="Client payment overdue",
        subject=f"Payment overdue on {contract.subject_title}",
        lines=[
            f"The client has not funded period {period.period_number} of \"{contract.subject_title}\".",
            "Please pause new work until it is funded. If it stays unpaid you will be able to request termination.",
        ],
        request=request,
    )


# --- Assignment notifications ---

def notify_freelancer_of_assignment(assignment, request=None):
    contract = assignment.contract
    _notify_contract_event(
        contract.freelancer, contract,
        title="New assignment",
        subject=f"New assignment: {contract.subject_title}",
        lines=[
            f"The client added an assignment on \"{contract.subject_title}\": {assignment.title}.",
            "Open the contract to view the details and submit your work.",
        ],
        request=request,
    )


def notify_employer_of_assignment_submission(assignment, request=None):
    contract = assignment.contract
    _notify_contract_event(
        contract.employer, contract,
        title="Assignment submitted",
        subject=f"Assignment submitted: {contract.subject_title}",
        lines=[
            f"The freelancer submitted work for the assignment \"{assignment.title}\".",
            "Review it and accept or request changes.",
        ],
        request=request,
    )


def notify_freelancer_of_assignment_review(assignment, action, request=None):
    contract = assignment.contract
    if action == "accept":
        title = "Assignment accepted"
        lines = [f"The client accepted your work on the assignment \"{assignment.title}\"."]
    else:
        title = "Changes requested on assignment"
        lines = [f"The client requested changes on \"{assignment.title}\"."]
        if assignment.review_note:
            lines.append(f"Note: {assignment.review_note}")
        lines.append("Update your work and submit again.")
    _notify_contract_event(
        contract.freelancer, contract,
        title=title,
        subject=f"{title}: {contract.subject_title}",
        lines=lines,
        request=request,
    )


# --- Termination notifications ---

def notify_termination_offered(contract, request=None):
    """Grace elapsed with no funding: invite the freelancer to request termination."""
    _notify_contract_event(
        contract.freelancer, contract,
        title="Payment overdue - you may request termination",
        subject=f"Payment overdue: {contract.subject_title}",
        lines=[
            f"The client has not funded the next period of \"{contract.subject_title}\" within the grace period.",
            "You are not expected to work unpaid. You can request to terminate the contract from its page; our team reviews and finalises it.",
        ],
        request=request,
    )


def notify_termination_requested(termination, request=None):
    """Notify the other party that a termination request was raised."""
    contract = termination.contract
    other = contract.freelancer if termination.requested_by_id == contract.employer_id else contract.employer
    _notify_contract_event(
        other, contract,
        title="Termination requested",
        subject=f"Termination requested: {contract.subject_title}",
        lines=[
            f"A request to terminate \"{contract.subject_title}\" was submitted.",
            f"Reason: {termination.reason}",
            "Our team will review and finalise it.",
        ],
        request=request,
    )


def notify_termination_result(termination, request=None):
    """Notify both parties of the admin's decision."""
    contract = termination.contract
    if termination.status == "approved":
        title = "Contract terminated"
        lines = [
            f"\"{contract.subject_title}\" has been terminated by our team.",
            "Any funded work has been settled to the freelancer's wallet.",
        ]
    else:
        title = "Termination request denied"
        lines = [f"The request to terminate \"{contract.subject_title}\" was denied; the contract continues."]
        if termination.admin_note:
            lines.append(f"Note: {termination.admin_note}")
    for user in {contract.employer, contract.freelancer}:
        _notify_contract_event(
            user, contract, title=title,
            subject=f"{title}: {contract.subject_title}", lines=lines, request=request,
        )
