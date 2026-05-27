from django.db import transaction
from payments.models import Escrow
from services.wallet_service import WalletService


class EscrowService:

    @staticmethod
    @transaction.atomic
    def fund_escrow(escrow: Escrow, payment_reference: str):
        """
        Called AFTER webhook confirms payment
        """

        if escrow.is_funded:
            return escrow  # idempotent

        escrow.is_funded = True
        escrow.save()

        freelancer_wallet = escrow.freelancer.wallet

        WalletService.credit_pending(
            wallet=freelancer_wallet,
            amount=escrow.amount,
            metadata={
                "escrow_id": escrow.id,
                "payment_reference": payment_reference
            }
        )

        return escrow

    @staticmethod
    @transaction.atomic
    def release_escrow(escrow: Escrow):
        """
        Employer confirms job completion
        """

        if not escrow.is_funded:
            raise ValueError("Escrow not funded")

        if escrow.is_released:
            return escrow  # idempotent

        wallet = escrow.freelancer.wallet

        WalletService.release_funds(
            wallet=wallet,
            amount=escrow.amount,
            metadata={"escrow_id": escrow.id}
        )

        escrow.is_released = True
        escrow.save()

        return escrow