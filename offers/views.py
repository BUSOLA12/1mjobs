# Example: authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .models import Offer, OfferFile
from django.contrib.auth import get_user_model
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from datetime import timedelta
from pricing.subscription_engine import check_and_consume_feature, get_active_subscription
from users.utils import log_user_action

User = get_user_model()

from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import OfferCreateSerializer, OfferSerializer, OfferFileSerializer

class CreateOfferView(generics.CreateAPIView):
    serializer_class = OfferCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    FEATURE_KEY = "offers"

    def perform_create(self, serializer):
        user = self.request.user
        receiver = serializer.validated_data["receiver"]

        # Subscription check & consume
        check_and_consume_feature(user, self.FEATURE_KEY)

        # If allowed, create offer
        offer = serializer.save(sender=user)

        log_user_action(user, "create_offer", metadata={"offer_id": offer.id,
                                                        "receiver": receiver.email})


class OfferReceivedListView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        user = request.user
        forty_days_ago = timezone.now() - timedelta(days=40)

        has_subscription = get_active_subscription(user) is not None

        if has_subscription:
            queryset = Offer.objects.filter(receiver=user).order_by("-created_at")
            serializer = self.get_serializer(queryset, many=True)
            return Response({"offers": serializer.data, "unlisted": None})

        # ---- User has no active subscription ----
        all_offers = Offer.objects.filter(receiver=user)

        # Offers older than 40 days → shown
        visible_offers = all_offers.filter(created_at__lte=forty_days_ago).order_by("-created_at")

        # Offers newer than 40 days → hidden count
        hidden_count = all_offers.filter(created_at__gt=forty_days_ago).count()

        serializer = self.get_serializer(visible_offers, many=True)

        return Response({
            "offers": serializer.data,
            "unlisted": hidden_count
        })


class OfferSentListView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Offer.objects.filter(sender=self.request.user).order_by("-created_at")


class OfferDetailView(generics.RetrieveAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Offer.objects.all()

    def retrieve(self, request, *args, **kwargs):
        offer = self.get_object()
        if request.user != offer.sender and request.user != offer.receiver:
            raise PermissionDenied("You are not allowed to view this offer.")
        return super().retrieve(request, *args, **kwargs)



class OfferDeleteView(generics.DestroyAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Offer.objects.all()

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
            raise PermissionDenied("You can only delete offers you created.")
        log_user_action(self.request.user, "delete_offer", metadata={"offer_id": instance.id,
                                                                    "receiver": instance.receiver.email})
        instance.delete()
