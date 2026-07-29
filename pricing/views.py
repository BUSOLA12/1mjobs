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

from .subscription_engine import get_active_subscription, get_remaining_for_feature
from payments.services.africanmoney_service import AfricanMoneyService, AfricanMoneyError


# -------------------------
# PLAN LIST/FETCH
# -------------------------
class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer

    def get_queryset(self):
        qs = Plan.objects.filter(is_active=True)
        user_type = self.request.query_params.get("user_type")
        if user_type:
            qs = qs.filter(user_type=user_type)
        return qs


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
# CHECKOUT: Create African Money Transaction
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

        existing_tx = Transaction.objects.filter(
            order=order, reference__startswith="AFM_"
        ).first()
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

        return self.checkout_with_africanmoney(request, order, amount)

    def checkout_with_africanmoney(self, request, order, amount):
        reference = f"AFM_{order.id}_{timezone.now().strftime('%Y%m%d%H%M%S')}"

        plan_name = order.plan_name_snapshot or (order.plan.name if order.plan else "Subscription")

        # The order-confirmation page JS reads ?reference=... and POSTs it to
        # /api/pricing/payment/confirmation/ for server-side verification.
        success_url = f"{settings.FRONTEND_URL}order-confirmation/?reference={reference}"
        failed_url = f"{settings.FRONTEND_URL}checkout/{order.id}/"

        try:
            result = AfricanMoneyService.create_collection(
                item_name=f"{plan_name} ({order.billing_cycle})",
                amount=amount,
                email=request.user.email,
                phone="",
                client_name=request.user.get_full_name,
                success_url=success_url,
                failed_url=failed_url,
            )
        except AfricanMoneyError as e:
            raise APIException(f"African Money initialization failed: {e}")

        payment_url = result["payment_url"]

        tx = Transaction.objects.create(
            order=order,
            reference=reference,
            authorization_url=payment_url,
            amount=order.amount,
            status="pending",
        )

        return Response({
            "order_id": order.id,
            "payment_url": tx.authorization_url,
            "reference": tx.reference,
        })


# -------------------------
# Payment Confirmation (Manual)
# -------------------------
class PaymentConfirmationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"error": "Reference required"}, status=400)

        tx = get_object_or_404(Transaction, reference=reference)

        if tx.order.user != request.user:
            return Response({"error": "Not your transaction"}, status=403)

        if not reference.startswith("AFM_"):
            return Response({"error": "Unknown payment reference"}, status=400)

        # Verify server-side with African Money before crediting. The
        # collection id is the last path segment of the payment URL.
        collection_id = tx.authorization_url.rstrip("/").split("/")[-1]
        try:
            data = AfricanMoneyService.verify_collection(collection_id)
        except AfricanMoneyError as e:
            return Response({"error": f"Verification failed: {e}"}, status=400)

        if data.get("status") != "completed":
            return Response(
                {"error": "Payment not completed", "status": data.get("status")},
                status=400,
            )

        # Guard against tampering: the paid amount/currency must match the
        # VAT-inclusive charge we created the collection with.
        expected = tx.order.amount
        if getattr(settings, "VAT_ENABLED", False):
            expected += (expected * settings.VAT_RATE) / 100
        if int(data.get("amount") or 0) != int(expected):
            return Response(
                {"error": "Amount mismatch", "paid": data.get("amount"),
                 "expected": int(expected)},
                status=400,
            )
        if (data.get("currency") or "NGN") != "NGN":
            return Response({"error": "Currency mismatch"}, status=400)

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
