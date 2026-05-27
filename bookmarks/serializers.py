from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Bookmark
from ManageJobsTasks.models import Job, Task
from users.models import UserProfile

class BookmarkCreateSerializer(serializers.ModelSerializer):
    model_type = serializers.ChoiceField(choices=['job', 'task', 'userprofile'], write_only=True)
    object_id = serializers.IntegerField()

    class Meta:
        model = Bookmark
        fields = ['id', 'model_type', 'object_id']

    def validate(self, attrs):
        model_type = attrs.get('model_type')
        object_id = attrs.get('object_id')

        model_map = {
            'job': Job,
            'task': Task,
            'userprofile': UserProfile,
        }

        model_class = model_map.get(model_type)
        if not model_class:
            raise serializers.ValidationError("Invalid bookmark type.")

        if not model_class.objects.filter(id=object_id).exists():
            raise serializers.ValidationError(f"{model_type} with id {object_id} does not exist.")

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        model_type = validated_data['model_type']
        object_id = validated_data['object_id']

        model_map = {
            'job': Job,
            'task': Task,
            'userprofile': UserProfile,
        }

        model_class = model_map[model_type]
        content_type = ContentType.objects.get_for_model(model_class)

        bookmark, created = Bookmark.objects.get_or_create(
            user=user,
            content_type=content_type,
            object_id=object_id
        )
        return bookmark

class BookmarkListSerializer(serializers.Serializer):
    jobs = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    userprofiles = serializers.SerializerMethodField()

    def get_jobs(self, obj):
        jobs = Bookmark.objects.filter(user=obj, content_type=ContentType.objects.get_for_model(Job))
        return [{
            'id': b.id, 
            'job_id': b.object_id, 
            "job_type": b.content_object.job_type, 
            "location": b.content_object.location, 
            "created_at": b.content_object.created_at, 
            'title': b.content_object.title} for b in jobs]

    def get_tasks(self, obj):
        tasks = Bookmark.objects.filter(user=obj, content_type=ContentType.objects.get_for_model(Task))
        return [{'id': b.id, 'task_id': b.object_id, 
                 "created_at": b.content_object.created_at, 
                 "project_type": b.content_object.project_type,
                 "location": b.content_object.location,
                 'project_name': b.content_object.project_name} for b in tasks]

    def get_userprofiles(self, obj):
        profiles = Bookmark.objects.filter(user=obj, content_type=ContentType.objects.get_for_model(UserProfile))
        return [{
            'id': b.id, 
            'profile_id': b.object_id, 
            'tagline': b.content_object.tagline,
            'full_name': b.content_object.user.first_name + " " + b.content_object.user.last_name,
            'verified': b.content_object.verified,
            'rating': b.content_object.rating,
            'bio': b.content_object.bio} for b in profiles]
