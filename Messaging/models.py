from django.db import models
from django.conf import settings
from django.utils import timezone


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messaging_profile')
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    user_type = models.CharField(max_length=20, choices=[
        ('freelancer', 'Freelancer'),
        ('employer', 'Employer')
    ], default='freelancer')

    def __str__(self):
        return f"{self.user.get_full_name or self.user.username} - {self.user_type}"


class Conversation(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    job = models.ForeignKey('ManageJobsTasks.Job', on_delete=models.CASCADE, related_name='conversations_job', null=True, blank=True)
    task = models.ForeignKey('ManageJobsTasks.Task', on_delete=models.CASCADE, related_name='conversations_task', null=True, blank=True)
    subject = models.CharField(max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


    class Meta:
        ordering = ['-updated_at']


    def __str__(self):
        users = list(self.participants.all())
        if len(users) >= 2:
            return f"Conversation between {users[0].first_name} and {users[1].first_name}"

        return f"Conversation {self.id}"

    def get_other_participant(self, user):
        return self.participants.exclude(id=user.id).first()

    def get_last_message(self):
        return self.messages.order_by('-timestamp').first()

    def mark_as_read(self, user):
        self.messages.filter(recipient=user, is_read=False).update(is_read=True)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now=True)
    message_type = models.CharField(max_length=10, choices=[
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File')
    ], default='text')
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Message from {self.sender.username} to {self.recipient.username} at {self.timestamp}"
 

class MessageNotification(models.Model):
    """Notification for unread messages"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    unread_count = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        
        ordering = ["-created_at"]


    def __str__(self):
        return f"{self.user.username} has {self.unread_count} unread messages"

