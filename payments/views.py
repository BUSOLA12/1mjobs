from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import PaymentListSerializer, PaymentDetailSerializer, WalletSerializer
from .models import Payment, Wallet

class EmployerPaymentListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(
            employer=request.user
        ).select_related("task", "freelancer", "contract__job").order_by("-created_at")

        serializer = PaymentListSerializer(payments, many=True)
        return Response(serializer.data)


from django.shortcuts import get_object_or_404

class EmployerPaymentDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        payment = get_object_or_404(
            Payment.objects.select_related("task", "freelancer", "contract__job"),
            id=pk,
            employer=request.user
        )

        serializer = PaymentDetailSerializer(payment)
        return Response(serializer.data)


from rest_framework import status
from payments.services.payment_service import PaymentService

class InitiatePaymentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payment = get_object_or_404(
            Payment,
            id=pk,
            employer=request.user
        )

        try:
            payment = PaymentService.initiate_payment(payment)

            return Response({
                "payment_url": payment.payment_url,
                "status": payment.status
            })

        except ValueError as e:
            return Response({"error": str(e)}, status=400)

from payments.services.africanmoney_service import AfricanMoneyService, AfricanMoneyError


class PaymentConfirmationAPIView(APIView):
    """
    Employer returns from the African Money page with ?reference=PAY-...;
    verify server-side with African Money before marking the payment escrowed.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"error": "Reference required"}, status=400)

        payment = get_object_or_404(
            Payment,
            payment_reference=reference,
            employer=request.user
        )

        # Idempotency: already escrowed (or beyond) means nothing to do
        if payment.status in ("ESCROWED", "RELEASED"):
            return Response({"status": payment.status})

        collection_id = payment.collection_id or \
            (payment.payment_url or "").rstrip("/").split("/")[-1]

        try:
            data = AfricanMoneyService.verify_collection(collection_id)
        except AfricanMoneyError as e:
            return Response({"error": f"Verification failed: {e}"}, status=400)

        if data.get("status") != "completed":
            return Response(
                {"error": "Payment not completed", "status": data.get("status")},
                status=400,
            )

        # Guard against tampering: paid amount/currency must match the charge
        if int(data.get("amount") or 0) != int(payment.amount):
            return Response(
                {"error": "Amount mismatch", "paid": data.get("amount"),
                 "expected": int(payment.amount)},
                status=400,
            )
        if (data.get("currency") or "NGN") != "NGN":
            return Response({"error": "Currency mismatch"}, status=400)

        payment = PaymentService.handle_successful_payment(reference)
        return Response({"status": payment.status})


class ReleasePaymentAPIView(APIView):
    """
    Employer confirms the work is done: move escrowed funds to the freelancer,
    deducting the platform commission.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        payment = get_object_or_404(Payment, id=pk, employer=request.user)

        try:
            payment = PaymentService.release_payment(payment)

            return Response({
                "status": payment.status,
                "gross": payment.amount,
                "commission": payment.commission_amount,
                "net": payment.net_amount,
            })

        except ValueError as e:
            return Response({"error": str(e)}, status=400)


from ManageJobsTasks.models import TaskBidding
from payments.services.africanmoney_service import AfricanMoneyError
from .models import Transaction


class CreateJobPaymentAPIView(APIView):
    """
    Employer pays the freelancer for a Task they hired (accepted bid).
    Creates the Payment from the accepted bid (amount taken from the bid, not
    the client) and initiates it with African Money, returning the payment URL.
    Idempotent: reuses an existing, not-yet-released payment for the same
    task + freelancer instead of creating duplicates.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        bid = get_object_or_404(
            TaskBidding.objects.select_related("task", "freelancer"),
            id=request.data.get("bid_id"),
        )

        if bid.task.user != request.user:
            return Response({"error": "Not your task."}, status=403)
        if bid.status != "accepted":
            return Response({"error": "Accept the bid before paying."}, status=400)

        payment = Payment.objects.filter(
            task=bid.task, freelancer=bid.freelancer, employer=request.user,
        ).exclude(status="RELEASED").first()

        if not payment:
            payment = Payment.objects.create(
                employer=request.user,
                freelancer=bid.freelancer,
                task=bid.task,
                amount=bid.bid_amount,
                status="NOT_INITIATED",
            )

        if payment.status == "NOT_INITIATED":
            try:
                payment = PaymentService.initiate_payment(payment)
            except (AfricanMoneyError, ValueError) as e:
                return Response({"error": f"Could not start payment: {e}"}, status=400)

        return Response({
            "payment_id": payment.id,
            "payment_url": payment.payment_url,
            "status": payment.status,
        })


class WalletAPIView(APIView):
    """The logged-in user's wallet balances (freelancer earnings view)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response(WalletSerializer(wallet).data)


class TransactionListAPIView(APIView):
    """The logged-in user's recent wallet transactions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        txns = wallet.transactions.select_related("payment").order_by("-created_at")[:50]
        return Response([
            {
                "type": t.transaction_type,
                "amount": t.amount,
                "status": t.status,
                "reference": t.reference,
                "created_at": t.created_at,
            }
            for t in txns
        ])


from .models import Withdrawal, BankAccount
from .serializers import WithdrawalSerializer
from .services.withdrawal_service import WithdrawalService, WithdrawalError


class WithdrawalListCreateAPIView(APIView):
    """Freelancer: list their withdrawals (GET) or request a new one (POST)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        withdrawals = Withdrawal.objects.filter(user=request.user)
        return Response(WithdrawalSerializer(withdrawals, many=True).data)

    def post(self, request):
        amount = request.data.get("amount")
        account_name = (request.data.get("account_name") or "").strip()
        account_number = (request.data.get("account_number") or "").strip()
        bank_name = (request.data.get("bank_name") or "").strip()
        bank_code = (request.data.get("bank_code") or "").strip()

        if not amount or not account_name or not account_number or not bank_name:
            return Response(
                {"error": "amount, account_name, account_number and bank_name are required."},
                status=400,
            )

        # Remember the account for next time (matched by number), and link it.
        bank_account, _ = BankAccount.objects.get_or_create(
            user=request.user, account_number=account_number,
            defaults={"account_name": account_name, "bank_name": bank_name, "bank_code": bank_code},
        )

        try:
            withdrawal = WithdrawalService.request(
                user=request.user, amount=amount, account_name=account_name,
                account_number=account_number, bank_name=bank_name, bank_code=bank_code,
                bank_account=bank_account,
            )
        except WithdrawalError as e:
            return Response({"error": str(e)}, status=400)
        except Exception as e:
            return Response({"error": f"Could not request withdrawal: {e}"}, status=400)

        return Response(
            {"message": "Withdrawal requested", "withdrawal": WithdrawalSerializer(withdrawal).data},
            status=201,
        )












# from django.shortcuts import render

# # Create your views here.

# from rest_framework.views import APIView
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response

# from .serializers import WalletSerializer, TransactionSerializer, EscrowSerializer, WithdrawalSerializer
# from payments.models import Wallet, Transaction, Escrow
# from payments.services.escrow_service import EscrowService

# import json
# from django.views.decorators.csrf import csrf_exempt
# from django.utils.decorators import method_decorator

# from payments.services.payment_service import PaymentService
    
# from rest_framework.generics import ListAPIView
# from rest_framework import status
# from payments.services.withdrawal_service import WithdrawalService


# class WalletView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         wallet = request.user.wallet
#         serializer = WalletSerializer(wallet)
#         return Response(serializer.data)


# class TransactionListView(ListAPIView):
#     serializer_class = TransactionSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Transaction.objects.filter(
#             wallet=self.request.user.wallet
#         ).order_by('-created_at')


# class ReleaseEscrowView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, escrow_id):
#         escrow = Escrow.objects.get(id=escrow_id, employer=request.user)

#         # security check
#         if escrow.employer != request.user:
#             return Response({"error": "Unauthorized"}, status=403)

#         EscrowService.release_escrow(escrow)

#         return Response({"message": "Funds released successfully"})


# class WithdrawView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         serializer = WithdrawalSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)

#         amount = serializer.validated_data["amount"]

#         try:
#             result = WithdrawalService.request_withdrawal(
#                 user=request.user,
#                 amount=amount
#             )

#             return Response({
#                 "message": "Withdrawal initiated",
#                 "transaction_id": result["transaction"].id
#             })

#         except Exception as e:
#             return Response(
#                 {"error": str(e)},
#                 status=status.HTTP_400_BAD_REQUEST
#             )


# @method_decorator(csrf_exempt, name='dispatch')
# class PaymentWebhookView(APIView):

#     authentication_classes = []
#     permission_classes = []

#     def post(self, request):
#         payload = request.body
#         data = json.loads(payload)

#         # Example for Paystack
#         event = data.get("event")

#         if event == "charge.success":
#             payment_data = data["data"]

#             reference = payment_data["reference"]
#             amount = payment_data["amount"] / 100  # convert kobo → naira
#             metadata = payment_data.get("metadata", {})

#             PaymentService.handle_successful_payment(
#                 reference=reference,
#                 amount=amount,
#                 metadata=metadata
#             )

#         return Response({"status": "ok"})