"""Drive the recurring (Job) billing cycle. Idempotent; run hourly from
entrypoint.sh (single machine, no Celery), like `expire_jobs_tasks`.

Each run:
  1. Funding reminders   - awaiting_funding periods due within the lead window.
  2. Missed funding      - awaiting_funding periods past their due date move the
                           contract to 'grace' (the period stays fundable).
  3. Open review windows - funded periods whose end has passed enter 'in_review'.
  4. Auto-release        - 'in_review' periods past their review window with no
                           open dispute release escrow to the freelancer.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.models import BillingPeriod, Contract, Dispute
from contracts.billing import FUNDING_REMINDER_LEAD_DAYS
from contracts import utils as cutils


class Command(BaseCommand):
    help = "Process recurring-contract billing periods (reminders, review windows, auto-release, grace)."

    def handle(self, *args, **options):
        now = timezone.now()
        reminders = self._send_reminders(now)
        graced = self._handle_missed(now)
        offered = self._offer_termination(now)
        opened = self._open_review_windows(now)
        released = self._auto_release(now)
        self.stdout.write(self.style.SUCCESS(
            f"billing: reminders={reminders} grace={graced} terminate_offered={offered} "
            f"review_opened={opened} released={released}"
        ))

    def _send_reminders(self, now):
        soon = now + timedelta(days=FUNDING_REMINDER_LEAD_DAYS)
        qs = BillingPeriod.objects.filter(
            status="awaiting_funding", reminder_sent=False,
            funding_due_date__gt=now, funding_due_date__lte=soon,
        ).select_related("contract")
        n = 0
        for p in qs:
            cutils.notify_funding_reminder(p)
            BillingPeriod.objects.filter(pk=p.pk).update(reminder_sent=True)
            n += 1
        return n

    def _handle_missed(self, now):
        # Past-due but still-unfunded periods: move an active contract into grace.
        # The period stays 'awaiting_funding' so the employer can still fund it
        # (funding during grace returns the contract to active via the signal).
        qs = BillingPeriod.objects.filter(
            status="awaiting_funding", funding_due_date__lt=now,
        ).select_related("contract")
        n = 0
        for p in qs:
            moved = Contract.objects.filter(pk=p.contract_id, status="active").update(status="grace")
            if moved:
                cutils.notify_missed_funding(p)
                n += 1
        return n

    def _offer_termination(self, now):
        # Contracts in grace whose grace window has fully elapsed: invite the
        # freelancer (once) to request termination for non-payment.
        n = 0
        graced = Contract.objects.filter(
            status="grace", termination_offered_at__isnull=True
        ).prefetch_related("periods")
        for c in graced:
            overdue = c.periods.filter(
                status="awaiting_funding", funding_due_date__lt=now
            ).order_by("funding_due_date").first()
            if not overdue:
                continue
            if now >= overdue.funding_due_date + timedelta(days=c.grace_period_days):
                Contract.objects.filter(pk=c.pk).update(termination_offered_at=now)
                cutils.notify_termination_offered(c)
                n += 1
        return n

    def _open_review_windows(self, now):
        qs = BillingPeriod.objects.filter(status="funded", end_date__lte=now).select_related("contract")
        n = 0
        for p in qs:
            rwe = p.end_date + timedelta(days=p.contract.review_window_days)
            BillingPeriod.objects.filter(pk=p.pk).update(status="in_review", review_window_end=rwe)
            n += 1
        return n

    def _auto_release(self, now):
        from payments.services.payment_service import PaymentService

        qs = BillingPeriod.objects.filter(
            status="in_review", review_window_end__lte=now,
        ).select_related("contract")
        n = 0
        for p in qs:
            # Hold the release if a dispute is open on this contract.
            if Dispute.objects.filter(
                contract_id=p.contract_id, status__in=["open", "under_review"]
            ).exists():
                continue
            payment = p.payments.filter(status="ESCROWED").order_by("-created_at").first()
            if payment:
                PaymentService.release_payment(payment)
                BillingPeriod.objects.filter(pk=p.pk).update(status="released")
                payment.refresh_from_db()
                cutils.notify_period_released(p, payment.net_amount)
            else:
                BillingPeriod.objects.filter(pk=p.pk).update(status="released")
            n += 1
        return n
