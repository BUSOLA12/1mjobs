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
from pricing.features import DIRECT_OFFERS
from users.utils import log_user_action

User = get_user_model()

from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from Messaging.models import Conversation
from .serializers import OfferCreateSerializer, OfferSerializer, OfferFileSerializer

class CreateOfferView(generics.CreateAPIView):
    serializer_class = OfferCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    FEATURE_KEY = DIRECT_OFFERS  # Employer Pro perk ("offers" feature key)

    def perform_create(self, serializer):
        user = self.request.user
        receiver = serializer.validated_data["receiver"]

        # Only employers send offers, and only to freelancers
        if user.role != "employer":
            raise PermissionDenied("Only employers can send offers.")
        if receiver.role != "freelancer":
            raise PermissionDenied("Offers can only be sent to freelancers.")

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


class OfferConversationView(APIView):
    """Create (or reuse) a direct conversation between the two people on an
    offer, so the offer's 'Send a Message' button opens a real chat.

    Scoped to offers: it only ever touches participants-only conversations
    (job and task are left null) and never affects job/task conversations.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        offer = get_object_or_404(Offer, pk=pk)

        # Only the two people on the offer may open its conversation.
        if request.user.id not in (offer.sender_id, offer.receiver_id):
            return Response({"error": "Not your offer."}, status=403)
        if offer.sender_id == offer.receiver_id:
            return Response({"error": "Cannot message yourself."}, status=400)

        # Reuse an existing conversation between exactly these two people,
        # scoped to the offer's job/task (or a job/task-less direct chat when the
        # offer isn't tied to either); otherwise create one. We check the exact
        # participant set in Python because chaining .filter(participants=...)
        # with a Count annotation does not reliably match a pair on a M2M join.
        target = {offer.sender_id, offer.receiver_id}
        candidates = Conversation.objects.filter(participants=offer.sender)
        if offer.job_id:
            candidates = candidates.filter(job_id=offer.job_id)
        elif offer.task_id:
            candidates = candidates.filter(task_id=offer.task_id)
        else:
            candidates = candidates.filter(job__isnull=True, task__isnull=True)

        conv = None
        for candidate in candidates.prefetch_related("participants"):
            if set(candidate.participants.values_list("id", flat=True)) == target:
                conv = candidate
                break

        if not conv:
            if offer.job_id:
                subject = offer.job.title
            elif offer.task_id:
                subject = offer.task.project_name
            else:
                subject = f"Offer from {offer.sender.get_full_name}"
            conv = Conversation.objects.create(
                subject=subject, job_id=offer.job_id, task_id=offer.task_id,
            )
            conv.participants.set([offer.sender, offer.receiver])

        return Response({"conversation_id": conv.id}, status=200)
