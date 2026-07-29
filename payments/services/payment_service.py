# payments/services/payment_service.py

import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction as db_transaction
from django.conf import settings

from payments.models import Payment, Transaction, Wallet
from payments.services.africanmoney_service import AfricanMoneyService


class PaymentService:

    prefix = "PAY"

    @classmethod
    def generate_reference(cls):
        return f"{cls.prefix}-{uuid.uuid4().hex[:12].upper()}"


    @staticmethod
    @db_transaction.atomic
    def initiate_payment(payment: Payment):
        """
        Handles:
        - status validation
        - reference generation
        - African Money collection creation
        """

        if payment.status not in ["NOT_INITIATED", "FAILED"]:
            raise ValueError("Payment already initiated or in progress")

        reference = PaymentService.generate_reference()

        if payment.task_id:
            item_name = f"Task payment: {payment.task}"
        elif payment.contract_id:
            subject = payment.contract.subject_title
            if payment.period_id:
                item_name = f"Escrow: {subject} (period {payment.period.period_number})"
            else:
                item_name = f"Contract payment: {subject}"
        else:
            item_name = "Job payment"

        result = AfricanMoneyService.create_collection(
            item_name=item_name,
            amount=payment.amount,
            email=payment.employer.email,
            phone="",
            client_name=payment.employer.get_full_name,
            success_url=f"{settings.FRONTEND_URL}payment-confirmation/?reference={reference}",
            failed_url=f"{settings.FRONTEND_URL}dashboard/",
        )

        # Update payment
        payment.status = "INITIATED"
        payment.payment_reference = reference
        payment.payment_url = result["payment_url"]
        payment.collection_id = result["collection_id"]
        payment.save()

        return payment

    @staticmethod
    @db_transaction.atomic
    def handle_successful_payment(reference: str):
        """
        Called after the payment has been verified with African Money
        """

        payment = Payment.objects.select_for_update().get(
            payment_reference=reference
        )

        # Idempotency check
        if payment.status == "ESCROWED":
            return payment

        payment.status = "ESCROWED"
        payment.save()

        # Update freelancer wallet (pending). Ensure the wallet exists: a
        # freelancer hired via the contract flow may not have one yet.
        wallet, _ = Wallet.objects.get_or_create(user=payment.freelancer)

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
        Release escrowed funds to the freelancer.

        The escrowed ``amount`` splits three ways:
          - commission: the platform's service fee (PLATFORM_FEE_PERCENTAGE of amount)
          - vat: tax charged ON the commission (ESCROW_VAT_RATE), not on the
            freelancer's earnings or the escrow amount
          - net: what lands in the freelancer's available balance
            (amount - commission - vat)

        This mirrors how Upwork/Fiverr/Freelancer.com apply VAT to the service
        fee rather than the project amount. The employer funds the plain amount
        at escrow time; nothing is added on top there.
        """

        if payment.status != "ESCROWED":
            raise ValueError("Payment not in escrow")

        cents = Decimal("0.01")
        fee_rate = Decimal(str(settings.PLATFORM_FEE_PERCENTAGE))
        commission = (payment.amount * fee_rate / Decimal(100)).quantize(
            cents, rounding=ROUND_HALF_UP
        )

        vat_rate = Decimal(str(getattr(settings, "ESCROW_VAT_RATE", 0)))
        if getattr(settings, "ESCROW_VAT_ENABLED", False) and vat_rate > 0:
            vat = (commission * vat_rate / Decimal(100)).quantize(cents, rounding=ROUND_HALF_UP)
        else:
            vat = Decimal("0.00")

        net = payment.amount - commission - vat

        wallet = Wallet.objects.select_for_update().get(user=payment.freelancer)

        wallet.pending_balance -= payment.amount
        wallet.available_balance += net
        wallet.save()

        payment.status = "RELEASED"
        payment.commission_amount = commission
        payment.vat_amount = vat
        payment.net_amount = net
        payment.save()

        meta = {"gross": str(payment.amount), "fee_rate": str(fee_rate), "vat_rate": str(vat_rate)}

        # Net credit to the freelancer
        Transaction.objects.create(
            wallet=wallet,
            payment=payment,
            amount=net,
            transaction_type="CREDIT",
            status="completed",
            reference=f"REL-{payment.payment_reference}",
            metadata=meta,
        )

        # Platform commission record
        Transaction.objects.create(
            wallet=wallet,
            payment=payment,
            amount=commission,
            transaction_type="FEE",
            status="completed",
            reference=f"FEE-{payment.payment_reference}",
            metadata=meta,
        )

        # VAT charged on the commission (only when non-zero)
        if vat > 0:
            Transaction.objects.create(
                wallet=wallet,
                payment=payment,
                amount=vat,
                transaction_type="VAT",
                status="completed",
                reference=f"VAT-{payment.payment_reference}",
                metadata=meta,
            )

        return payment
