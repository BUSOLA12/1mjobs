import requests
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, APIException

from users.utils import log_user_action

from .models import Plan, Order, Subscription, Transaction
from .serializers import PlanSerializer, OrderSerializer, SubscriptionSerializer
from .helper import create_subscription_from_order
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .subscription_engine import get_active_subscription, get_remaining_for_feature
from payments.services.payment_service import PaymentService


# -------------------------
# PLAN LIST/FETCH
# -------------------------
class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer

    def get_queryset(self):
        user_type = self.request.query_params.get("user_type")
        if user_type:
            return Plan.objects.filter(user_type=user_type)
        return Plan.objects.all()


class PlanPriceView(APIView):
    def get(self, request):
        plan_id = request.query_params.get("plan_id")
        plan = get_object_or_404(Plan, id=plan_id)

        return Response({
            "plan": plan.name,
            "monthly": float(plan.monthly_price),
            "yearly": float(plan.yearly_price or 0),
        })


# -------------------------
# SUBSCRIPTION
# -------------------------
class SubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return get_active_subscription(self.request.user)


# -------------------------
# ORDER
# -------------------------
class OrderCreateView(generics.CreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)
        log_user_action(self.request.user, "create_order", metadata={"order_id": order.id,
                                                                    "plan": order.plan_id})


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        order = get_object_or_404(Order, pk=self.kwargs["pk"])
        if order.user != self.request.user:
            raise PermissionDenied("Not your order.")
        return order


# -------------------------
# CHECKOUT: Create Paystack Transaction
# -------------------------
class CheckoutOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        order = get_object_or_404(Order, pk=self.kwargs["pk"])
        if order.user != self.request.user:
            raise PermissionDenied("You cannot access this order.")
        return order

    def get(self, request, *args, **kwargs):
        order = self.get_object()

        existing_tx = Transaction.objects.filter(order=order).first()
        if existing_tx:
            return Response({
                "order_id": order.id,
                "payment_url": existing_tx.authorization_url,
                "reference": existing_tx.reference,
            })

        # calculate real charge (VAT included)
        amount = order.amount
        if getattr(settings, "VAT_ENABLED", False):
            amount += (amount * settings.VAT_RATE) / 100

        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        reference = f"ORD_{order.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

        payload = {
            "email": request.user.email,
            "amount": int(amount * 100),
            "reference": reference,
            "callback_url": f"{settings.FRONTEND_URL}/order-confirmation/",
        }

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            raise APIException("Paystack initialization failed.")

        data = response.json()["data"]

        # Create Transaction instance
        tx = Transaction.objects.create(
            order=order,
            reference=reference,
            authorization_url=data["authorization_url"],
            amount=order.amount,
            status="pending",
        )

        return Response({
            "order_id": order.id,
            "payment_url": tx.authorization_url,
            "reference": tx.reference,
        })


# -------------------------
# PAYSTACK WEBHOOK
# -------------------------
@csrf_exempt
def paystack_webhook(request):
    import json

    try:
        payload = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid payload"}, status=400)

    event = payload.get("event")

    if event == "charge.success":
        data = payload.get("data", {})
        reference = data.get("reference")

        # check if reference start with PAY
        if reference.startswith(PaymentService.prefix):
            PaymentService.handle_successful_payment(reference)
            return Response({"status": "success"})

        try:
            with db_transaction.atomic():
                tx = Transaction.objects.select_related("order").get(reference=reference)

                if tx.status != "success":
                    tx.status = "success"
                    tx.save()

                    order = tx.order
                    order.status = "paid"
                    order.payment_reference = reference
                    order.save()

                    create_subscription_from_order(order.id)
        except Transaction.DoesNotExist:
            return JsonResponse({"error": "Transaction not found"}, status=404)

    return JsonResponse({"status": "ok"}, status=200)


# -------------------------
# Payment Confirmation (Manual)
# -------------------------
class PaymentConfirmationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"error": "Reference required"}, status=400)

        # Verify with Paystack
        verify_url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

        resp = requests.get(verify_url, headers=headers).json()
        if resp.get("data", {}).get("status") != "success":
            return Response({"error": "Verification failed"}, status=400)

        # Update database
        tx = get_object_or_404(Transaction, reference=reference)

        if tx.order.user != request.user:
            return Response({"error": "Not your transaction"}, status=403)

        with db_transaction.atomic():
            tx.status = "success"
            tx.save()

            order = tx.order
            order.status = "paid"
            order.payment_reference = reference
            order.save()

            create_subscription_from_order(order.id)

        return Response({"message": "Payment confirmed", "order_id": order.id})

# print a user with a subscription where the feature 'job_listings' is allowed and has remaining quota
def debug_print_subscriptions():
    sub = Subscription.objects.filter(
        is_active=True,
        end_date__gte=timezone.now(),
        remaining_features__has_key='offers'
    ).first()

    if sub:
        print(sub.user.email)

# debug_print_subscriptions()
# -------------------------

class SubscriptionCheckView(APIView):
    """
    GET /api/subscription/check/?feature=job_posts
    Returns whether the authenticated user is allowed to perform the action and the remaining balance (if any).
    This view is read-only and does NOT consume quota.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        feature = request.query_params.get("feature")
        if not feature:
            return Response({"detail": "feature query param is required"}, status=status.HTTP_400_BAD_REQUEST)

        sub = get_active_subscription(request.user)
        if not sub:
            return Response({"allowed": False, "message": "No active subscription."}, status=status.HTTP_200_OK)

        allowed, remaining = get_remaining_for_feature(request.user, feature)
        # Format friendly remaining
        if allowed:
            if remaining is None:
                rem = "unlimited"
            elif isinstance(remaining, bool):
                rem = "available"
            else:
                rem = remaining
            return Response({"allowed": True, "remaining": rem}, status=status.HTTP_200_OK)

        return Response({"allowed": False, "remaining": 0}, status=status.HTTP_200_OK)
