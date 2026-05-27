from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message

@receiver(post_save, sender=Message)
def notify_unread_messages(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        recipient_id = instance.recipient.id

        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}",
            {
                "type": "send_notification",
                "data": {
                    "type": "new_message",
                    "conversation_id": instance.conversation.id,
                    "message_id": instance.id,
                    "sender": instance.sender.first_name,
                    "sender_id": instance.sender.id,
                    "content": instance.content,
                    "timestamp": str(instance.created_at),
                },

            },
            )
            
@receiver(post_save, sender=Message)
def refresh_conversation(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        recipient_id = instance.recipient.id

        async_to_sync(channel_layer.group_send)(
            f"user_{recipient_id}",
            {
                "type": "refresh_conv",
                "timestamp": str(instance.created_at),
            },
        )
        

        
        