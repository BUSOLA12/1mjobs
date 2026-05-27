from rest_framework import serializers
from .models import Job, Task, JobApplication, TaskBidding
from django.utils import timezone
from company.models import Company
from company.serializers import CreateCompanySerializer
from users.models import UserProfile
from users.serializers import ProfileDetailSerializer


class JobSerializer(serializers.ModelSerializer):
    files = serializers.FileField(required=False, allow_empty_file=True, allow_null=True)

    files_url = serializers.SerializerMethodField(read_only=True)

    company_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'user')


    def to_representation(self, instance):
        data = super().to_representation(instance)

        if timezone.now() > instance.expiration_date:
            instance.is_expired = 'True'
            instance.save()
            data['is_expired'] = 'expired'
        return data

    def get_files_url(self, obj):
        request = self.context.get('request')
        if obj.files and request:
            return request.build_absolute_uri(obj.files.url)
        return None

    def get_company_info(self, obj):
        try:
            company = Company.objects.filter(created_by=obj.user).first()
            if company:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return CreateCompanySerializer(company, context={'request': request}).data
            return None
        except Company.DoesNotExist:
            return None

class TaskSerializer(serializers.ModelSerializer):
    files = serializers.FileField(required=False, allow_empty_file=True, allow_null=True)
    files_url = serializers.SerializerMethodField(read_only=True)

    company_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_files_url(self, obj):
        request = self.context.get('request')
        if obj.files and request:
            return request.build_absolute_uri(obj.files.url)
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if timezone.now() > instance.expiration_date:
            instance.status = 'expired'
            instance.save()
            data['status'] = 'expired'
        return data

    def get_company_info(self, obj):
        try:
            company = Company.objects.filter(created_by=obj.user).first()
            if company:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return CreateCompanySerializer(company, context={'request': request}).data
            return None
        except Company.DoesNotExist:
            return None

class JobApplicationSerializer(serializers.ModelSerializer):
    files = serializers.FileField(required=False, allow_empty_file=True, allow_null=True)
    files_url = serializers.ModelSerializer(read_only=True)
    applicant_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobApplication
        fields = '__all__'
        read_only_fields = ('created_at',)
        extra_kwargs = {'status': {'required': False}}

    def get_files_url(self, obj):
        request = self.context.get('request')
        if obj.files and request:
            return request.build_absolute_uri(obj.files.url)
        return None

    def get_applicant_info(self, obj):
        try:
            applicant = UserProfile.objects.filter(user=obj.user).first()
            if applicant:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return ProfileDetailSerializer(applicant, context={'request': request}).data
            return None
        except UserProfile.DoesNotExist:
            return None

    

class TaskBidsSerializer(serializers.ModelSerializer):
    freelancer_info = serializers.SerializerMethodField(read_only=True)
    task_info = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = TaskBidding
        fields ='__all__'
        read_only_fields = ('created_at',)

    def get_freelancer_info(self, obj):
        try:
            freelancer = UserProfile.objects.filter(user=obj.freelancer).first()
            if freelancer:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return ProfileDetailSerializer(freelancer, context={'request': request}).data
            return None
        except UserProfile.DoesNotExist:
            return None

    def get_task_info(self, obj):
        try:
            task = obj.task
            if task:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return TaskSerializer(task, context={'request': request}).data
            return None
        except Task.DoesNotExist:
            return None