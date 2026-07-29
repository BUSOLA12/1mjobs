"""Billing-period helpers for recurring (Job) contracts.

Periods are monthly. The employer pre-funds each period's escrow before it
begins; `process_billing_cycles` (management command) drives reminders,
end-of-period review windows, auto-release, and missed-funding grace.
"""

import calendar
from datetime import timedelta

from django.utils import timezone

from .models import BillingPeriod


# The first period gives the employer a short lead to fund and start; later
# periods are pre-created when the prior one funds, so they get the full
# reminder lead before their due date.
FIRST_PERIOD_FUNDING_LEAD_DAYS = 3
FUNDING_REMINDER_LEAD_DAYS = 5


def add_one_month(dt):
    """Add one calendar month, clamping the day to the target month's length."""
    month = dt.month + 1
    year = dt.year + (month - 1) // 12
    month = (month - 1) % 12 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def create_first_period(contract):
    """Create period 1 for a freshly activated recurring contract (idempotent)."""
    existing = contract.periods.order_by("period_number").first()
    if existing:
        return existing
    now = timezone.now()
    return BillingPeriod.objects.create(
        contract=contract,
        period_number=1,
        start_date=now,
        end_date=add_one_month(now),
        amount=contract.monthly_rate or contract.amount,
        funding_due_date=now + timedelta(days=FIRST_PERIOD_FUNDING_LEAD_DAYS),
        status="awaiting_funding",
    )


def settle_funded_periods(contract):
    """Release any funded / in-review period escrow to the freelancer. Used when
    a contract is terminated so already-funded work is paid out. Returns the
    number of periods released."""
    from payments.services.payment_service import PaymentService

    released = 0
    for period in contract.periods.filter(status__in=["funded", "in_review"]):
        payment = period.payments.filter(status="ESCROWED").order_by("-created_at").first()
        if payment:
            PaymentService.release_payment(payment)
        BillingPeriod.objects.filter(pk=period.pk).update(status="released")
        released += 1
    return released


def recompute_active_status(contract):
    """After a termination is denied, return the contract to 'active', or 'grace'
    if a period is still overdue and unfunded."""
    overdue = contract.periods.filter(
        status="awaiting_funding", funding_due_date__lt=timezone.now()
    ).exists()
    return "grace" if overdue else "active"


def create_next_period(contract):
    """Create the next upcoming period after the latest one (idempotent-ish:
    callers guard on existence)."""
    last = contract.periods.order_by("-period_number").first()
    if last is None:
        return create_first_period(contract)
    start = last.end_date
    return BillingPeriod.objects.create(
        contract=contract,
        period_number=last.period_number + 1,
        start_date=start,
        end_date=add_one_month(start),
        amount=contract.monthly_rate or contract.amount,
        funding_due_date=start,  # fund before the next period begins
        status="awaiting_funding",
    )
