from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

from users.utils import log_user_action
from .models import Review
from .utils import has_collaborated_on_object, update_user_aggregate_rating, get_pending_reviews_for_user
from django.core.exceptions import ValidationError
from django.utils import timezone

class ReviewCreateSerializer(serializers.ModelSerializer):
    model_type = serializers.ChoiceField(choices=['job', 'task'], write_only=True)
    object_id = serializers.IntegerField(write_only=True)
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5, allow_null=True)
    review_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    on_budget = serializers.BooleanField(required=False)
    on_time = serializers.BooleanField(required=False)

    class Meta:
        model = Review
        fields = ['id', 'model_type', 'object_id', 'rating', 'review_text', 'on_budget', 'on_time', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'model_type': {'write_only': True},
            'object_id': {'write_only': True},
        }

    def validate(self, attrs):
        user = self.context['request'].user
        model_type = attrs.get('model_type')
        object_id = attrs.get('object_id')

        model_map = {
            'job': ('ManageJobsTasks', 'Job'),
            'task': ('ManageJobsTasks', 'Task'),
        }
        app_label, model_name = model_map[model_type]
        try:
            ModelClass = apps.get_model(app_label, model_name)
        except LookupError:
            raise serializers.ValidationError(f"{model_name} model not found in {app_label} app.")

        obj = ModelClass.objects.filter(pk=object_id).first()
        if not obj:
            raise serializers.ValidationError(f"{model_name} with id {object_id} does not exist.")

        # Determine relationship: owner <-> accepted applicant
        owner = obj.user

        # Determine applicant for different models: Task and Job
        valid_status = ['accepted', 'completed']
        if model_name == 'Task':
            TaskBidding = apps.get_model('ManageJobsTasks', 'TaskBidding')
            applicant = TaskBidding.objects.filter(task=obj, status__in=valid_status).first().freelancer
        elif model_name == 'Job':
            JobApplication = apps.get_model('ManageJobsTasks', 'JobApplication')
            applicant = JobApplication.objects.filter(job=obj, status__in=valid_status).first().user

        if not applicant:
            raise serializers.ValidationError("This job/task has no accepted applicant yet.")

        # Decide who is reviewing whom
        if user == owner:
            reviewee = applicant
        elif user == applicant:
            reviewee = owner
        else:
            raise serializers.ValidationError("You are not part of this interaction.")

        if reviewee == user:
            raise serializers.ValidationError("You cannot review yourself for this interaction.")

        # Ensure collaboration validation (custom logic)
        try:
            collaborated = has_collaborated_on_object(user, reviewee, obj)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))

        if not collaborated:
            raise serializers.ValidationError("You cannot leave a review unless the interaction was accepted/completed.")

        # Prevent duplicate review
        ct = ContentType.objects.get_for_model(ModelClass)
        exists = Review.objects.filter(reviewer=user, content_type=ct, object_id=object_id).exists()
        if exists:
            raise serializers.ValidationError("You have already submitted a review for this interaction.")

        attrs['content_object'] = obj
        attrs['reviewee'] = reviewee
        return attrs


    def create(self, validated_data):
        user = self.context['request'].user
        obj = validated_data.pop('content_object')
        reviewee = validated_data.pop('reviewee')
        rating = validated_data.get('rating', None)
        review_text = validated_data.get('review_text', None)
        on_budget = validated_data.get('on_budget', None)
        on_time = validated_data.get('on_time', None)
        ct = ContentType.objects.get_for_model(obj.__class__)

        review = Review.objects.create(
            reviewer=user,
            reviewee=reviewee,
            content_type=ct,
            object_id=obj.pk,
            rating=rating,
            review_text=review_text
        )

        if on_budget is not None:
            review.on_budget = on_budget

        if on_time is not None:
            review.on_time = on_time

        review.save()

        log_user_action(user, "leave_review", metadata={"review_id": review.id, "reviewee": reviewee.email})

        # Update aggregate rating (non-blocking)
        try:
            update_user_aggregate_rating(reviewee)
        except Exception:
            pass

        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """
    Allows editing rating/review_text within 7 days of creation only.
    """
    rating = serializers.IntegerField(required=False, min_value=1, max_value=5, allow_null=True)
    review_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Review
        fields = ['rating', 'review_text', 'on_time', 'on_budget']

    def validate(self, attrs):
        review = self.instance
        if not review:
            raise serializers.ValidationError("Review instance required for update.")
        if not review.is_editable():
            raise serializers.ValidationError("This review can no longer be edited (editing window expired).")
        return attrs

    def update(self, instance, validated_data):
        instance.rating = validated_data.get('rating', instance.rating)
        instance.on_budget = validated_data.get('on_budget', instance.review_text)
        instance.on_time = validated_data.get('on_time', instance.review_text)
        instance.review_text = validated_data.get('review_text', instance.review_text)
        instance.save(update_fields=['rating', 'review_text', 'updated_at', 'on_time', 'on_budget'])
        # update aggregate rating
        try:
            update_user_aggregate_rating(instance.reviewee)
        except Exception:
            pass

        log_user_action(self.context['request'].user, "update_review", metadata={"review_id": instance.id})
        return instance


class ReviewListSerializer(serializers.ModelSerializer):
    reviewee = serializers.SerializerMethodField()
    object_type = serializers.SerializerMethodField()
    object_title = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'reviewee', 'object_type', 'object_id', 'object_title', 'rating', 'review_text', 'on_time', 'on_budget', 'created_at']

    def get_reviewee(self, obj):
        u = obj.reviewee
        return {'id': u.id,'name': f'{u.first_name} {u.last_name}', 'email': getattr(u, 'email', str(u))}

    def get_object_type(self, obj):
        return obj.content_type.model  # 'job' or 'task'

    def get_object_title(self, obj):
        # show job.title or task.project_name
        try:
            content = obj.content_object
            if hasattr(content, 'title'):
                return getattr(content, 'title')
            if hasattr(content, 'project_name'):
                return getattr(content, 'project_name')
            return str(content)
        except Exception:
            return ''
