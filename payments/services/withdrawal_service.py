"""Manual, admin-processed withdrawals.

A freelancer requests a payout against their available wallet balance. The
request does NOT move money on its own; an admin verifies the bank details and
marks it paid, at which point the wallet is debited and a DEBIT transaction is
written. Rejecting leaves the balance untouched.
"""

from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from payments.models import Wallet, Withdrawal, Transaction


class WithdrawalError(Exception):
    pass


class WithdrawalService:

    @staticmethod
    @db_transaction.atomic
    def request(user, amount, account_name, account_number, bank_name, bank_code="", bank_account=None):
        amount = Decimal(str(amount))
        if amount <= 0:
            raise WithdrawalError("Amount must be greater than zero.")

        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)

        # Funds already tied up in not-yet-processed requests can't be requested again.
        outstanding = Withdrawal.objects.filter(
            user=user, status__in=["requested", "approved"]
        ).aggregate(s=Sum("amount"))["s"] or Decimal("0")

        available_for_request = wallet.available_balance - outstanding
        if amount > available_for_request:
            raise WithdrawalError(
                f"Amount exceeds your available balance (NGN {available_for_request} available to withdraw)."
            )

        return Withdrawal.objects.create(
            user=user, amount=amount, bank_account=bank_account,
            account_name=account_name, account_number=account_number,
            bank_name=bank_name, status="requested",
        )

    @staticmethod
    @db_transaction.atomic
    def mark_paid(withdrawal):
        """Admin action: debit the wallet and record the payout. Idempotent."""
        w = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
        if w.status == "paid":
            return w
        if w.status == "rejected":
            raise WithdrawalError("This withdrawal was rejected.")

        wallet = Wallet.objects.select_for_update().get(user=w.user)
        if wallet.available_balance < w.amount:
            raise WithdrawalError("Insufficient available balance to pay this withdrawal.")

        wallet.available_balance -= w.amount
        wallet.save()

        Transaction.objects.create(
            wallet=wallet,
            amount=w.amount,
            transaction_type="DEBIT",
            status="completed",
            reference=f"WD-{w.id}-{int(timezone.now().timestamp())}",
            metadata={"withdrawal_id": w.id, "bank": w.bank_name, "account": w.account_number},
        )

        w.status = "paid"
        w.processed_at = timezone.now()
        w.save(update_fields=["status", "processed_at"])
        return w

    @staticmethod
    @db_transaction.atomic
    def reject(withdrawal, note=""):
        w = Withdrawal.objects.select_for_update().get(pk=withdrawal.pk)
        if w.status == "paid":
            raise WithdrawalError("Already paid; cannot reject.")
        w.status = "rejected"
        w.admin_note = note or w.admin_note
        w.processed_at = timezone.now()
        w.save(update_fields=["status", "admin_note", "processed_at"])
        return w
