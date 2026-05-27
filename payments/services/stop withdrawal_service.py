from django.db import transaction
from payments.models import Wallet, BankAccount
from payments.services.wallet_service import WalletService


class WithdrawalService:

    @staticmethod
    @transaction.atomic
    def request_withdrawal(user, amount):
        wallet = user.wallet

        if amount <= 0:
            raise ValueError("Invalid amount")

        # debit wallet first
        txn = WalletService.debit_available(
            wallet=wallet,
            amount=amount,
            metadata={"user_id": user.id}
        )

        # get default bank
        bank = BankAccount.objects.filter(user=user, is_default=True).first()

        if not bank:
            raise ValueError("No default bank account")

        # TODO: integrate Paystack/Monnify transfer here

        return {
            "transaction": txn,
            "bank": bank
        }
