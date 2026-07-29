from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from payments.models import Payment

from .models import Contract, BillingPeriod


@receiver(post_save, sender=Payment)
def on_payment_escrowed(sender, instance, **kwargs):
    """React to a payment reaching ESCROWED.

    - Recurring (Job): the payment funds a BillingPeriod -> mark the period
      funded, bring the contract back to 'active' if it was in grace, and make
      sure the next upcoming period exists so the employer can pre-fund it.
    - One-shot (Task): the payment funds the whole contract -> mark it funded
      and stamp the deadline (legacy behaviour).
    """
    if instance.status != "ESCROWED":
        return

    # --- Recurring period funding ---
    if instance.period_id:
        updated = BillingPeriod.objects.filter(
            pk=instance.period_id, status="awaiting_funding"
        ).update(status="funded")
        if not updated:
            return
        period = BillingPeriod.objects.select_related("contract").get(pk=instance.period_id)
        contract = period.contract
        # Funding while in grace resolves the missed payment.
        if contract.status == "grace":
            Contract.objects.filter(pk=contract.id).update(status="active")
        # Ensure the next period exists so the employer can pre-fund ahead.
        if not contract.periods.filter(period_number=period.period_number + 1).exists():
            from .billing import create_next_period
            create_next_period(contract)
        from .utils import notify_period_funded
        notify_period_funded(period)
        return

    # --- One-shot (Task) contract funding (legacy) ---
    if instance.contract_id:
        updated = Contract.objects.filter(
            pk=instance.contract_id, status="awaiting_funding"
        ).update(
            status="funded",
            deadline=timezone.now() + timedelta(days=_delivery_days(instance.contract_id)),
        )
        if updated:
            from .utils import notify_freelancer_escrow_funded
            notify_freelancer_escrow_funded(Contract.objects.get(pk=instance.contract_id))


def _delivery_days(contract_id):
    return Contract.objects.filter(pk=contract_id).values_list("delivery_days", flat=True).first() or 0
