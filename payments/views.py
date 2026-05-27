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
        ).select_related("task", "freelancer").order_by("-created_at")

        serializer = PaymentListSerializer(payments, many=True)
        return Response(serializer.data)


from django.shortcuts import get_object_or_404

class EmployerPaymentDetailAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        payment = get_object_or_404(
            Payment.objects.select_related("task", "freelancer"),
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

class PaymentWebhookAPIView(APIView):

    authentication_classes = []  # Paystack won't send auth
    permission_classes = []

    def post(self, request):
        reference = request.data.get("reference")

        PaymentService.handle_successful_payment(reference)

        return Response({"status": "success"})












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