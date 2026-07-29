# Example: authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
import calendar
from rest_framework import status, generics, permissions
from django.utils import timezone
from django.db import models
from .models import UserProfile, UserFile, Category, WorkHistory, status_choices, ProfileView
from ManageJobsTasks.models import JobApplication, TaskBidding
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import UserProfileEditSerializer, UserFileSerializer, AvatarUploadSerializer, UserProfileSerializer, UserFileCreateSerializer, UserSerializer, WorkHistorySerializer
from django.contrib.auth import get_user_model
from django.db.models.functions import Random

User = get_user_model()

from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ProfileSerializer, CategorySerializer, ProfileDetailSerializer
from .filters import UserProfileFilter, MultiTermSearchFilter
from .pagination import DefaultPageNumberPagination
from pricing.subscription_engine import check_feature_allowed
from pricing.features import (
    SEARCH_BOOST, PROFILE_VIEWERS, HIRING_ANALYTICS,
    feature_subscription_exists,
)


class ProfileDetailView(generics.RetrieveAPIView):
    queryset = UserProfile.objects.select_related('user', 'category')
    serializer_class = ProfileDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        self._record_view(request, instance)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def _record_view(self, request, profile):
        viewer = request.user if request.user.is_authenticated else None
        # Don't count the owner viewing their own profile.
        if viewer and viewer.pk == profile.user_id:
            return
        ip = (request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
              or request.META.get('REMOTE_ADDR'))
        # Dedupe: one view per viewer (or IP, if anonymous) per profile per day.
        today = timezone.now().date()
        dedupe = models.Q(viewer=viewer) if viewer else models.Q(ip_address=ip)
        already = ProfileView.objects.filter(
            profile=profile, created_at__date=today,
        ).filter(dedupe).exists()
        if not already:
            ProfileView.objects.create(profile=profile, viewer=viewer, ip_address=ip)

class ProfileListView(generics.ListAPIView):
    queryset = UserProfile.objects.select_related('user', 'category').filter(user__role='freelancer')
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, MultiTermSearchFilter, OrderingFilter]
    filterset_class = UserProfileFilter
    pagination_class = DefaultPageNumberPagination
    search_fields = [
    'tagline', 'bio',
    'user__first_name', 'user__last_name', 'user__email'
    ]
    ordering_fields = ['hourly_rate', 'job_success', 'rating', 'created_at']
    ordering = ['-is_pro', '-rating', 'created_at'] # default "Sort by: Relevance" analogue

    def get_queryset(self):
        # Pro subscribers (search_boost perk) get an is_pro flag used for both
        # the PRO badge in the payload and the ranking boost below.
        qs = super().get_queryset().annotate(
            is_pro=feature_subscription_exists(SEARCH_BOOST)
        )
        if self.request.query_params.get('random') == 'true':
            qs = qs.order_by(Random())
        return qs

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        # Pro freelancers rank first for every explicit sort except random.
        if self.request.query_params.get('random') != 'true':
            current = list(qs.query.order_by) or list(self.ordering)
            if '-is_pro' not in current:
                qs = qs.order_by('-is_pro', *current)
        return qs

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None # usually small list

class UploadAvatarView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AvatarUploadSerializer(data=request.data)
        if serializer.is_valid():
            userProfile = UserProfile.objects.get(user=request.user)

            # If there's an existing avatar, delete it via Django's storage system
            if userProfile.avatar:
                userProfile.avatar.delete(save=False)

            # Save the new avatar
            userProfile.avatar = serializer.validated_data['avatar']
            userProfile.save()
            userProfile.recompute_onboarding()

            # Return the absolute URL
            avatar_url = request.build_absolute_uri(userProfile.avatar.url) if userProfile.avatar else None
            return Response({'avatar_url': avatar_url}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return UserProfile.objects.get(user=self.request.user)

class EditUserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileEditSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Ensures the logged-in user can only edit their own profile
        return UserProfile.objects.get(user=self.request.user)

class UserFilesView(generics.ListAPIView):
    serializer_class = UserFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        userProfile = UserProfile.objects.get(user=self.request.user)
        return (userProfile.file.all().order_by('-uploaded_at'))

class UserFilesUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        files = request.FILES.getlist('files')
        if not files:
            return Response({'detail': 'No files provided.'}, status=status.HTTP_400_BAD_REQUEST)

        created_objs = []
        for f in files:
            # You can validate size/type here if you want
            userprofile = UserProfile.objects.get(user=request.user)  # Ensure the user has a profile
            obj = UserFile.objects.create(profile=userprofile, file=f)
            created_objs.append(obj)

        data = UserFileSerializer(created_objs, many=True).data
        return Response(data, status=status.HTTP_201_CREATED)

class UserFileDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserFileSerializer
    queryset = UserFile.objects.all()

    def get_queryset(self):
        userprofile = UserProfile.objects.get(user=self.request.user)
        return UserFile.objects.filter(profile=userprofile)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT)

class UserRoleUpdateView(APIView):
    """Switch the logged-in user's role between freelancer and employer.

    Used by the company-onboarding "back out" action so a user who changed
    their mind can revert to freelancer. Admins cannot change their role here,
    and this endpoint only touches `role` (no skills/profile side effects).
    """
    permission_classes = [permissions.IsAuthenticated]

    ALLOWED_ROLES = {"freelancer", "employer"}

    def patch(self, request):
        role = request.data.get("role")
        if role not in self.ALLOWED_ROLES:
            return Response({"error": "Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if user.role == "admin":
            return Response({"error": "Admins cannot change their role"}, status=status.HTTP_403_FORBIDDEN)

        user.role = role
        user.save(update_fields=["role"])
        return Response({"role": user.role})


class UserStatusToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        status_value = request.data.get("status")
        if status_value not in dict(status_choices).keys():
            return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        user_profile = user.user_profile
        user_profile.status = status_value
        user_profile.save()
        return Response({"message": "Status updated"})

class WorkHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = WorkHistorySerializer

    def get_permissions(self):
        # Anyone can VIEW work history
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        # Only logged-in users can create work history
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        # Get ?id= from URL
        user_id = self.request.query_params.get("id")

        # If user_id is provided → return that user's work history
        if user_id:
            return WorkHistory.objects.filter(user__id=user_id).order_by("-created_at")

        # If no ID → return current user's work history
        if self.request.user.is_authenticated:
            return WorkHistory.objects.filter(user=self.request.user).order_by("-created_at")

        # Non-authenticated and no ID provided → empty queryset
        return WorkHistory.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
class WorkHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WorkHistorySerializer

    def get_queryset(self):
        return WorkHistory.objects.filter(user=self.request.user)

class CurrentUserAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):

        if not request.user.is_authenticated:
            return Response(
                {"detail": "No user is logged in"},
                status=status.HTTP_200_OK
            )

        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProfileStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = UserProfile.objects.get(user=request.user)
        period = request.query_params.get("range", "6m")  # 6m | year | month
        series = profile.view_series(period)
        return Response({
            "month_views": profile.views_this_month(),  # tile, always current month
            "labels": series["labels"],
            "data": series["data"],
        })


class ProfileViewersView(APIView):
    """Pro perk: list the actual people who viewed your profile.

    Free users keep the aggregate counts from ProfileStatsView; the
    PermissionDenied raised for them becomes a 403 the frontend turns
    into an upgrade prompt.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        check_feature_allowed(request.user, PROFILE_VIEWERS)

        profile = UserProfile.objects.get(user=request.user)
        since = timezone.now() - timezone.timedelta(days=90)
        views = (profile.views.filter(created_at__gte=since)
                 .select_related('viewer')
                 .order_by('-created_at')[:100])

        results = []
        for v in views:
            if v.viewer:
                vp = getattr(v.viewer, 'user_profile', None)
                avatar = None
                if vp and getattr(vp, 'avatar', None):
                    avatar = request.build_absolute_uri(vp.avatar.url)
                results.append({
                    "viewer_id": v.viewer.id,
                    "name": f"{v.viewer.first_name} {v.viewer.last_name}".strip() or v.viewer.email,
                    "role": v.viewer.role,
                    "avatar": avatar,
                    "viewed_at": v.created_at,
                })
            else:
                results.append({
                    "viewer_id": None, "name": "Anonymous visitor",
                    "role": None, "avatar": None, "viewed_at": v.created_at,
                })
        return Response({"count": len(results), "viewers": results})


def _period_series(qs, period):
    """Bucket a queryset by created_at into labels/data for the given period.

    period: '6m' (last 6 months), 'year' (12 months), 'month' (daily, current month).
    """
    now = timezone.now()
    if period == "month":
        days = calendar.monthrange(now.year, now.month)[1]
        labels = [str(d) for d in range(1, days + 1)]
        data = [qs.filter(created_at__year=now.year, created_at__month=now.month,
                          created_at__day=d).count() for d in range(1, days + 1)]
        return labels, data
    months = 12 if period == "year" else 6
    labels, data = [], []
    for off in range(months - 1, -1, -1):
        m, y = now.month - off, now.year
        while m <= 0:
            m += 12
            y -= 1
        labels.append(timezone.datetime(y, m, 1).strftime("%b"))
        data.append(qs.filter(created_at__year=y, created_at__month=m).count())
    return labels, data


class EmployerStatsView(APIView):
    """Submissions received on the employer's own listings, per month.

    type=jobs  -> JobApplications on the employer's Jobs
    type=tasks -> TaskBiddings on the employer's Tasks
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        type_ = request.query_params.get("type", "jobs")   # jobs | tasks
        period = request.query_params.get("range", "6m")   # 6m | year | month
        now = timezone.now()
        if type_ == "tasks":
            qs = TaskBidding.objects.filter(task__user=request.user)
        else:
            qs = JobApplication.objects.filter(job__user=request.user)
        labels, data = _period_series(qs, period)
        month_count = qs.filter(created_at__year=now.year, created_at__month=now.month).count()
        return Response({
            "type": type_,
            "month_count": month_count,
            "labels": labels,
            "data": data,
        })


class EmployerHiringAnalyticsView(APIView):
    """Employer Pro perk: per-listing breakdown + hiring funnel, beyond the
    free EmployerStatsView monthly series."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        check_feature_allowed(request.user, HIRING_ANALYTICS)

        period = request.query_params.get("range", "6m")
        apps_qs = JobApplication.objects.filter(job__user=request.user)
        bids_qs = TaskBidding.objects.filter(task__user=request.user)

        labels, app_data = _period_series(apps_qs, period)
        _, bid_data = _period_series(bids_qs, period)

        per_job = (apps_qs.values("job__id", "job__title")
                   .annotate(total=models.Count("id"))
                   .order_by("-total")[:20])

        funnel = {
            "applications": apps_qs.count(),
            "accepted": apps_qs.filter(status__in=["accepted", "completed"]).count(),
            "bids": bids_qs.count(),
            "bids_accepted": bids_qs.filter(status="accepted").count(),
        }

        return Response({
            "labels": labels,
            "applications": app_data,
            "bids": bid_data,
            "top_jobs": list(per_job),
            "funnel": funnel,
        })
