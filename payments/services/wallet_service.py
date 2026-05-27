from decimal import Decimal
from django.conf import settings
from django.db import transaction
from payments.models import escrow
from payments.models import Wallet, Transaction
from payments.utils.generators import generate_reference


class WalletService:

    @staticmethod
    @transaction.atomic
    def credit_pending(wallet: Wallet, amount: Decimal, metadata=None):
        wallet.pending_balance += amount
        wallet.save()

        return Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='escrow_funding',
            status='completed',
            reference=generate_reference(),
            metadata=metadata or {}
        )

    @staticmethod
    @transaction.atomic
    def release_funds(wallet: Wallet, amount: Decimal, metadata=None):
        if wallet.pending_balance < amount:
            raise ValueError("Insufficient pending balance")

        wallet.pending_balance -= amount

        fee = amount * Decimal(settings.PLATFORM_FEE_PERCENTAGE) / Decimal(100)
        net_amount = amount - fee

        wallet.available_balance += net_amount
        wallet.save()

        return Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='release',
            status='completed',
            reference=generate_reference(),
            metadata=metadata or {}
        )

    @staticmethod
    @transaction.atomic
    def debit_available(wallet: Wallet, amount: Decimal, metadata=None):
        if wallet.available_balance < amount:
            raise ValueError("Insufficient balance")

        wallet.available_balance -= amount
        wallet.save()

        return Transaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type='withdrawal',
            status='pending',
            reference=generate_reference(),
            metadata=metadata or {}
        )