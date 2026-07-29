# accounts/serializers.py

from rest_framework import serializers
from pathlib import Path
from django.contrib.auth import get_user_model
from .models import OfferFile, Offer

User = get_user_model()

class OfferFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OfferFile
        fields = ["id", "file", "uploaded_at"]

class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "email",
            "first_name",
            "last_name",
            "avatar",
            "rating",
            "verified",
        ]

    def get_avatar(self, obj):
        """Return full absolute URL for user avatar."""
        request = self.context.get("request")
        profile = getattr(obj, "user_profile", None)

        if profile and profile.avatar:
            return request.build_absolute_uri(profile.avatar.url)
        return None

    def get_rating(self, obj):
        profile = getattr(obj, "user_profile", None)
        return getattr(profile, "rating", 0.0)

    def get_verified(self, obj):
        profile = getattr(obj, "user_profile", None)
        return getattr(profile, "verified", False)


class OfferSerializer(serializers.ModelSerializer):
    files = OfferFileSerializer(many=True, read_only=True)
    sender = UserDetailSerializer(read_only=True)
    receiver = UserDetailSerializer(read_only=True)
    # What the offer is tied to (if anything): {type, id, title} or null.
    linked_to = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            "id",
            "sender",
            "receiver",
            "sender_full_name",
            "sender_email",
            "message",
            "files",
            "linked_to",
            "created_at",
            "is_read",
        ]

    def get_linked_to(self, obj):
        if obj.job_id:
            return {"type": "job", "id": obj.job_id, "title": obj.job.title}
        if obj.task_id:
            return {"type": "task", "id": obj.task_id, "title": obj.task.project_name}
        return None

class OfferCreateSerializer(serializers.ModelSerializer):
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )

    class Meta:
        model = Offer
        fields = ["receiver", "message", "job", "task", "uploaded_files"]
        extra_kwargs = {
            "job": {"required": False, "allow_null": True},
            "task": {"required": False, "allow_null": True},
        }

    def validate(self, data):
        # An offer can be tied to a job OR a task, not both.
        if data.get("job") and data.get("task"):
            raise serializers.ValidationError(
                "An offer can be linked to a job or a task, not both."
            )
        # The sender may only link their own job/task.
        user = self.context["request"].user
        job = data.get("job")
        task = data.get("task")
        if job and job.user_id != user.id:
            raise serializers.ValidationError({"job": "You can only link your own job."})
        if task and task.user_id != user.id:
            raise serializers.ValidationError({"task": "You can only link your own task."})
        return data

    def create(self, validated_data):
        user = self.context['request'].user
        sender_full_name = f"{user.first_name} {user.last_name}"
        sender_email = user.email
        files = validated_data.pop("uploaded_files", [])
        offer = Offer.objects.create(sender_email=sender_email, sender_full_name=sender_full_name, **validated_data)

        for file in files:
            OfferFile.objects.create(offer=offer, file=file)

        return offer

    
