# payments/services/payment_service.py

import uuid
from django.db import transaction as db_transaction
from django.conf import settings

from payments.models import Payment, Transaction, Wallet
from payments.services.gateway_service import PaymentGatewayService


class PaymentService:

    prefix = "PAY"

    @staticmethod
    def generate_reference(self):
        return f"{self.prefix}-{uuid.uuid4().hex[:12].upper()}"


    @staticmethod
    @db_transaction.atomic
    def initiate_payment(payment: Payment):
        """
        Handles:
        - status validation
        - reference generation
        - gateway initialization
        """

        if payment.status not in ["NOT_INITIATED", "FAILED"]:
            raise ValueError("Payment already initiated or in progress")

        reference = PaymentService.generate_reference()

        # Call gateway
        gateway = PaymentGatewayService()
        payment_link = gateway.initialize_payment(
            amount=payment.amount,
            email=payment.employer.email,
            reference=reference
        )

        # Update payment
        payment.status = "INITIATED"
        payment.payment_reference = reference
        payment.payment_url = payment_link
        payment.save()

        return payment
    
    @staticmethod
    @db_transaction.atomic
    def handle_successful_payment(reference: str):
        """
        Called from webhook
        """

        payment = Payment.objects.select_for_update().get(
            payment_reference=reference
        )

        # Idempotency check
        if payment.status == "ESCROWED":
            return payment

        payment.status = "ESCROWED"
        payment.save()

        # Update freelancer wallet (pending)
        wallet = payment.freelancer.wallet

        wallet.pending_balance += payment.amount
        wallet.save()

        # Create transaction record
        Transaction.objects.create(
            wallet=wallet,
            payment=payment,
            amount=payment.amount,
            transaction_type="CREDIT",
            status="completed",
            reference=reference,
        )

        return payment
    
    @staticmethod
    @db_transaction.atomic
    def release_payment(payment: Payment):
        """
        Move money from pending → available
        """

        if payment.status != "ESCROWED":
            raise ValueError("Payment not in escrow")

        wallet = payment.freelancer.wallet

        wallet.pending_balance -= payment.amount
        wallet.available_balance += payment.amount
        wallet.save()

        payment.status = "RELEASED"
        payment.save()

        Transaction.objects.create(
            wallet=wallet,
            payment=payment,
            amount=payment.amount,
            transaction_type="CREDIT",
            status="completed",
            reference=f"REL-{payment.payment_reference}",
        )

        return payment