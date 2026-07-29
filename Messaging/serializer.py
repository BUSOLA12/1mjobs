from rest_framework import serializers
from .models import Message, Conversation, UserProfile



class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['username', 'full_name', 'avatar_url', 'is_online', 'last_seen', 'user_type']

    def get_full_name(self, obj):
        return obj.user.get_full_name or obj.user.username

    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return '/static/images/user-avatar-placeholder.png'

class MessageSerializer(serializers.ModelSerializer):
    sender_profile = UserProfileSerializer(source='sender.userprofile', read_only=True)
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'content', 'timestamp', 'is_read', 'message_type', 'attachment', 'sender_profile', 'time_ago']
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)

class ConversationListSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_participant', 'last_message', 'unread_count', 'time_ago', 'updated_at']


    def get_other_participant(self, obj):
            user = self.context['request'].user
            other_user = obj.get_other_participant(user)
            if other_user:
                return UserProfileSerializer(other_user.userprofile).data
            return None

    def get_last_message(self, obj):
            last_message = obj.get_last_message()
            if last_message:
                return {
                    'content': last_message.content[:50] + '...' if len(last_message.content) > 50 else last_message.content,
                    'timestamp': last_message.timestamp,
                    'sender': last_message.sender.username
                }
            return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(recipient=user, is_read=False).count()

    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        last_message = obj.get_last_message()
        if last_message:
            return timesince(last_message.timestamp)
        return timesince(obj.updated_at)

class ConversationDetailSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'other_participant', 'messages', 'created_at', 'updated_at']

    def get_other_participant(self, obj):
        user = self.context['request'].user
        other_user = obj.get_other_participant(user)
        if other_user:
            return UserProfileSerializer(other_user.userprofile).data
        return None 
    
class JobConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'created_at', 'updated_at', 'participants', 'job']
        read_only_fields = ['created_at', 'updated_at', 'id']


class TaskConversationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ['id', 'created_at', 'updated_at', 'participants', 'task']
        read_only_fields = ['created_at', 'updated_at', 'id']


from users.models import UserProfile

class UserAvatarSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ["avatar_url"]

    def get_avatar_url(self, obj):
        """
        Returns the absolute avatar URL.
        Always returns a valid URL, even if no custom avatar is uploaded.
        """
        request = self.context.get("request")

        # Get avatar path (default included)
        avatar_path = obj.avatar.url if obj.avatar else "avatars/user-avatar-placeholder.png"

        # Return absolute URL if request is available
        if request:
            return request.build_absolute_uri(avatar_path)
        return avatar_path
