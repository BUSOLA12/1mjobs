from django.contrib import admin

# from .models import UserProfile, Conversation, Message, MessageNotification

# @admin.register(UserProfile)
# class UserProfileAdmin(admin.ModelAdmin):
#     list_display = ('user', 'user_type', 'is_online', 'last_seen')
#     list_filter = ('user_type', 'is_online')
#     search_fields = ('user__username', 'user__first_name', 'user__last_name')


# @admin.register(Conversation)
# class ConversationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'get_participants', 'created_at', 'updated_at', 'is_active')
#     list_filter = ('is_active', 'created_at')
#     filter_horizontal = ('participants',)

#     def get_participants(self, obj):
#         return ", ".join([user.username for user in obj.participants.all()])
#     get_participants.short_description = 'Participants'



# @admin.register(Message)
# class MessageAdmin(admin.ModelAdmin):
#     list_display = ('sender', 'recipient', 'content_preview', 'timestamp', 'is_read')
#     list_filter = ('is_read', 'message_type', 'timestamp')
#     search_fields = ('content', 'sender__username', 'recipient__username')
    
#     def content_preview(self, obj):
#         return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
#     content_preview.short_description = 'Content'


# @admin.register(MessageNotification)
# class MessageNotificationAdmin(admin.ModelAdmin):
#     list_display = ('user', 'conversation', 'unread_count', 'last_updated')
#     list_filter = ('last_updated',)
#     search_fields = ('user__username',)