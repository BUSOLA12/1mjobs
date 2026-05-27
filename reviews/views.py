from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Review
from .serializers import (
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
    ReviewListSerializer
)
from .utils import get_pending_reviews_for_user
from django.contrib.contenttypes.models import ContentType
from django.apps import apps
from users.pagination import DefaultPageNumberPagination
from django.contrib.auth import get_user_model
User = get_user_model()

# get random a user email from the user model
# user = User.objects.filter(is_active=True).order_by('?').first()
# email = user.email if user else ''
# print(f"Random active user email: {email}")



class CreateReviewView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewCreateSerializer


class UpdateReviewView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewUpdateSerializer
    queryset = Review.objects.all()

    def get_object(self):
        obj = super().get_object()
        # Only reviewer can edit their review
        if obj.reviewer != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You may only edit your own reviews.")
        return obj


class ReviewsReceivedView(generics.ListAPIView):
    """
    List all reviews received by a user (for the profile page).
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ReviewListSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Review.objects.filter(reviewee__id=user_id).order_by('-created_at')


class ReviewsByObjectView(generics.ListAPIView):
    """
    List all reviews tied to a specific object (job/task)
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ReviewListSerializer

    def get_queryset(self):
        model_type = self.kwargs.get('model_type')  # 'job' or 'task'
        object_id = self.kwargs.get('object_id')
        model_map = {
            'job': ('jobs', 'Job'),
            'task': ('tasks', 'Task')
        }
        if model_type not in model_map:
            return Review.objects.none()
        app_label, model_name = model_map[model_type]
        try:
            ModelClass = apps.get_model(app_label, model_name)
        except LookupError:
            return Review.objects.none()

        ct = ContentType.objects.get_for_model(ModelClass)
        return Review.objects.filter(content_type=ct, object_id=object_id).order_by('-created_at')


class PendingReviewsView(generics.GenericAPIView):
    """
    Returns a paginated list of pending reviews for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPageNumberPagination

    def get(self, request):
        pending = get_pending_reviews_for_user(request.user)  # -> list of dicts

        # Use DRF pagination helpers (works with lists)
        page = self.paginate_queryset(pending)
        if page is not None:
            # page is a sliced list according to the paginator
            return self.get_paginated_response(page)

        # fallback (no pagination configured)
        return Response({'pending': pending}, status=status.HTTP_200_OK)


class MyReviewsView(generics.ListAPIView):
    """
    Returns paginated reviews the current user has submitted,
    with an 'editable' flag per review.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ReviewListSerializer
    pagination_class = DefaultPageNumberPagination

    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        # Get queryset
        queryset = self.get_queryset()

        # Apply pagination (built-in to GenericAPIView)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data

            # Add editable info for items in this page
            for idx, review in enumerate(page):
                data[idx]['is_editable'] = review.is_editable()
                data[idx]['editable_until'] = review.editable_until.isoformat()

            # Return paginated response
            return self.get_paginated_response(data)

        # Fallback (if pagination disabled)
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for idx, review in enumerate(queryset):
            data[idx]['is_editable'] = review.is_editable()
            data[idx]['editable_until'] = review.editable_until.isoformat()

        return Response({'my_reviews': data}, status=status.HTTP_200_OK)
