from rest_framework import serializers
from .models import Job, Task, JobApplication, TaskBidding
from django.utils import timezone
from datetime import timedelta
from company.models import Company
from company.serializers import CreateCompanySerializer
from users.models import UserProfile
from users.serializers import ProfileDetailSerializer


# A user counts as online if the messaging socket marked them online, their
# last_seen is recent (guards ungraceful disconnects / idle sockets), and they
# have not made themselves invisible (users.UserProfile.status == 'inactive').
ONLINE_STALE_AFTER = timedelta(minutes=5)


def get_online_user_ids(user_ids):
    """Return the subset of user_ids that are currently online (one bulk query
    per table instead of two queries per row)."""
    user_ids = [uid for uid in user_ids if uid is not None]
    if not user_ids:
        return set()

    from Messaging.models import UserProfile as MessagingProfile

    invisible_ids = set(
        UserProfile.objects.filter(user_id__in=user_ids, status='inactive')
        .values_list('user_id', flat=True)
    )

    fresh_cutoff = timezone.now() - ONLINE_STALE_AFTER
    online_ids = set(
        MessagingProfile.objects.filter(
            user_id__in=user_ids, is_online=True, last_seen__gte=fresh_cutoff
        ).values_list('user_id', flat=True)
    )

    return online_ids - invisible_ids


class JobSerializer(serializers.ModelSerializer):
    files = serializers.FileField(required=False, allow_null=True, read_only=True)

    files_url = serializers.SerializerMethodField(read_only=True)

    uploaded_files = serializers.SerializerMethodField(read_only=True)

    company_info = serializers.SerializerMethodField(read_only=True)

    employer_rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Job
        fields = '__all__'
        # is_featured is set server-side (Employer Pro quota) and approved by
        # staff; neither may be mass-assigned by the client.
        read_only_fields = ('created_at', 'updated_at', 'user', 'is_featured', 'approved')

    def get_employer_rating(self, obj):
        """Aggregate rating of the job owner (from reviews), or count 0 when none."""
        profile = UserProfile.objects.filter(user=obj.user).first()
        if profile and getattr(profile, 'rating_count', 0):
            return {"avg": round(float(profile.avg_rating or 0), 1), "count": profile.rating_count}
        return {"avg": None, "count": 0}

    def get_uploaded_files(self, obj):
        request = self.context.get('request')
        files = []
        for job_file in obj.job_files.all():
            url = job_file.file.url
            if request:
                url = request.build_absolute_uri(url)
            files.append({"id": job_file.id, "url": url})
        return files

    def validate_expiration_date(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future.")
        return value

    def validate_salary_min(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Minimum salary cannot be negative.")
        return value

    def validate_salary_max(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Maximum salary cannot be negative.")
        return value

    def validate(self, data):
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError(
                {"salary_min": "Minimum salary cannot be greater than maximum salary."}
            )
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Report expiry live, as a real boolean, without writing to the DB on a
        # read. The persisted flag is reconciled by the expire_jobs_tasks command.
        if instance.expiration_date and timezone.now() > instance.expiration_date:
            data['is_expired'] = True
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

    employer_rating = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        # user is the poster (set in the view); approved is a staff gate;
        # is_featured is a paid perk. None may be mass-assigned by the client.
        read_only_fields = ('created_at', 'updated_at', 'user', 'is_featured', 'approved')

    def get_files_url(self, obj):
        request = self.context.get('request')
        if obj.files and request:
            return request.build_absolute_uri(obj.files.url)
        return None

    def get_employer_rating(self, obj):
        """Aggregate rating of the task owner (from reviews), or count 0 when none."""
        profile = UserProfile.objects.filter(user=obj.user).first()
        if profile and getattr(profile, 'rating_count', 0):
            return {"avg": round(float(profile.avg_rating or 0), 1), "count": profile.rating_count}
        return {"avg": None, "count": 0}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Report expiry live, without writing to the DB on a read. The persisted
        # status/flag is reconciled by the expire_jobs_tasks command.
        if instance.expiration_date and timezone.now() > instance.expiration_date:
            data['status'] = 'expired'
            data['is_expired'] = True
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
    files_url = serializers.SerializerMethodField(read_only=True)
    applicant_info = serializers.SerializerMethodField(read_only=True)
    job_info = serializers.SerializerMethodField(read_only=True)
    is_online = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = JobApplication
        # `email` is intentionally excluded: it is platform-internal and must
        # never be exposed to (or set by) the employer. `user` is exposed (the
        # applicant's account id, needed to start a chat) but read-only so the
        # client cannot apply on someone else's behalf; it is bound server-side.
        fields = (
            'id', 'job', 'user', 'name', 'proposal', 'bid_amount', 'files',
            'files_url', 'status', 'created_at', 'applicant_info', 'job_info',
            'is_online',
        )
        read_only_fields = ('created_at', 'user')
        extra_kwargs = {
            'status': {'required': False},
            'proposal': {'required': True, 'allow_blank': False},
            'bid_amount': {'required': True},
        }

    def get_is_online(self, obj):
        # Prefer a bulk-computed set passed by the view (avoids N+1); fall back
        # to a per-object lookup for single-instance serialization.
        online_ids = self.context.get('online_user_ids')
        if online_ids is not None:
            return obj.user_id in online_ids
        return obj.user_id in get_online_user_ids([obj.user_id])

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
                data = ProfileDetailSerializer(applicant, context={'request': request}).data
                # The applicant's email is platform-internal and must never reach
                # the employer, so strip it from the embedded profile too.
                data.pop('email', None)
                return data
            return None
        except UserProfile.DoesNotExist:
            return None

    def get_job_info(self, obj):
        try:
            job = obj.job
            if job:
                request = self.context.get('request')  # ✅ Make sure request is passed
                return JobSerializer(job, context={'request': request}).data
            return None
        except Job.DoesNotExist:
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