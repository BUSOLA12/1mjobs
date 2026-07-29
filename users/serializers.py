# accounts/serializers.py

from rest_framework import serializers
from pathlib import Path
from django.contrib.auth import get_user_model
from .models import UserProfile, UserFile, Category, Skill, WorkHistory

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    has_usable_password = serializers.SerializerMethodField()

    def get_has_usable_password(self, obj):
        return obj.has_usable_password()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'two_step_verification',
            'has_usable_password',
        ]
        read_only_fields = ['email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    skills = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'avatar', 'bio', 'skills', 'tagline', 'hourly_rate', 'nationality', 'address', 'portfolio_url', 'status']

    def get_skills(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())

class UserProfileEditSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'avatar',
            'bio',
            'skills',
            'tagline',
            'hourly_rate',
            'nationality',
            'address',
            'portfolio_url',
            'status',
            'user',
        ]

    def get_skills(self, obj):
        return [skill.name for skill in obj.skills.all()]

    def update(self, instance, validated_data):
        # Handle nested user update
        user_data = validated_data.pop('user', None)
        
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.user.save()

        # Handle skills update
        skills_list = self.initial_data.get('skills', None)
        if skills_list is not None:
            skill_objs = []
            for name in skills_list:
                skill_obj, _ = Skill.objects.get_or_create(
                    name__iexact=name,
                    defaults={'name': name}
                )
                skill_objs.append(skill_obj)
            instance.skills.set(skill_objs)
        else:
            instance.skills.clear()

        # Prevent ManyToMany direct assignment error
        validated_data.pop('skills', None)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        instance.recompute_onboarding()
        return instance

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    full_name = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    skills = serializers.SerializerMethodField(read_only=True)
    # Filled by the ProfileListView queryset annotation (search_boost perk).
    is_pro = serializers.BooleanField(read_only=True, default=False)


    class Meta:
        model = UserProfile
        fields = [
        "id", "user_id", "full_name", "tagline", "category", "nationality",
        "hourly_rate", "job_success", "rating", "verified", "bio", "avatar",
        "skills", "created_at", "is_pro",
        ]

        read_only_fields = [
            "id", "user_id", "full_name", "tagline", "category", "nationality",
            "hourly_rate", "job_success", "rating", "verified", "bio", "avatar",
            "skills", "created_at", "is_pro",
        ]


    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_skills(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())

class UserFileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    extension = serializers.SerializerMethodField()
    url = serializers.FileField(source='file', read_only=True)
    size = serializers.IntegerField(source='file.size', read_only=True)

    class Meta:
        model = UserFile
        fields = ('id', 'name', 'extension', 'url', 'size', 'uploaded_at')

    def get_name(self, obj):
        return Path(obj.file.name).name

    def get_extension(self, obj):
        return Path(obj.file.name).suffix.lstrip('.').lower()

class ProfileDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    files = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField(read_only=True)
    category = CategorySerializer(read_only=True)
    skills = serializers.SerializerMethodField(read_only=True)
    # Employer-facing activity metrics (shown in place of the freelancer-only
    # Hourly Rate / Job Success stats on the profile page).
    jobs_posted = serializers.SerializerMethodField(read_only=True)
    hires = serializers.SerializerMethodField(read_only=True)
    is_pro = serializers.SerializerMethodField(read_only=True)


    class Meta:
        model = UserProfile
        fields = [
        "id", "user_id", "full_name", "email", "tagline", "category", "nationality",
        "hourly_rate", "job_success", "rating", "verified", "bio", "avatar",
        "skills", "files", "portfolio_url", "created_at", "jobs_posted", "hires",
        "is_pro",
        ]

        read_only_fields = fields


    def get_email(self, obj):
        return obj.user.email
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_skills(self, obj):
        return ", ".join(skill.name for skill in obj.skills.all())
    
    def get_files(self, obj):
        request = self.context.get("request")
        return [
            request.build_absolute_uri(user_file.file.url)
            for user_file in obj.file.all()
        ]

    def get_jobs_posted(self, obj):
        # Total Jobs + Tasks this user has posted (relevant for employers).
        from django.apps import apps
        Job = apps.get_model('ManageJobsTasks', 'Job')
        Task = apps.get_model('ManageJobsTasks', 'Task')
        return (Job.objects.filter(user=obj.user).count()
                + Task.objects.filter(user=obj.user).count())

    def get_hires(self, obj):
        # Freelancers engaged on this user's postings: accepted/completed job
        # applications plus accepted task bids.
        from django.apps import apps
        JobApplication = apps.get_model('ManageJobsTasks', 'JobApplication')
        TaskBidding = apps.get_model('ManageJobsTasks', 'TaskBidding')
        return (JobApplication.objects.filter(
                    job__user=obj.user, status__in=['accepted', 'completed']
                ).count()
                + TaskBidding.objects.filter(
                    task__user=obj.user, status='accepted'
                ).count())

    def get_is_pro(self, obj):
        from pricing.features import FEATURED_PROFILE, has_feature
        return has_feature(obj.user, FEATURED_PROFILE)

# class UserFileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = UserFile
#         fields = ['file']



class UserFileCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ('id', 'file', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField()




class UserSerializer(serializers.ModelSerializer):
    is_pro = serializers.SerializerMethodField()
    priority_support = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_pro', 'priority_support']

    def get_is_pro(self, obj):
        from pricing.subscription_engine import get_active_subscription
        return get_active_subscription(obj) is not None

    def get_priority_support(self, obj):
        from pricing.features import PRIORITY_SUPPORT, has_feature
        return has_feature(obj, PRIORITY_SUPPORT)

class WorkHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkHistory
        fields = [
            "id",
            "company_name",
            "work_role",
            "start_month_year",
            "end_month_year",
            "responsibilities"
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        
        return WorkHistory.objects.create(**validated_data)
