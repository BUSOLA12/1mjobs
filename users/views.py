# Example: authentication/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .models import UserProfile, UserFile, Category, WorkHistory,status_choices
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


class ProfileDetailView(generics.RetrieveAPIView):
    queryset = UserProfile.objects.select_related('user', 'category')
    serializer_class = ProfileDetailSerializer

class ProfileListView(generics.ListAPIView):
    queryset = UserProfile.objects.select_related('user', 'category').all()
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, MultiTermSearchFilter, OrderingFilter]
    filterset_class = UserProfileFilter
    pagination_class = DefaultPageNumberPagination
    search_fields = [
    'tagline', 'bio',
    'user__first_name', 'user__last_name', 'user__email'
    ]
    ordering_fields = ['hourly_rate', 'job_success', 'rating', 'created_at']
    ordering = ['-rating', 'created_at'] # default "Sort by: Relevance" analogue

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get('random') == 'true':
            qs = qs.order_by(Random())
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
