import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Message

logger = logging.getLogger(__name__)


def _push(recipient_id, payload):
    """Best-effort realtime push to a user's channel group. The channel layer
    (Redis) may be unavailable (e.g. local dev without Redis); a push failure
    must never break saving the message, so we swallow and log."""
    try:
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return
        async_to_sync(channel_layer.group_send)(f"user_{recipient_id}", payload)
    except Exception as e:  # Redis down / channel layer error
        logger.warning("Realtime message push failed (non-fatal): %s", e)


@receiver(post_save, sender=Message)
def notify_unread_messages(sender, instance, created, **kwargs):
    if not created:
        return
    _push(instance.recipient_id, {
        "type": "send_notification",
        "data": {
            "type": "new_message",
            "conversation_id": instance.conversation_id,
            "message_id": instance.id,
            "sender": instance.sender.first_name,
            "sender_id": instance.sender_id,
            "content": instance.content,
            "timestamp": str(instance.created_at),
        },
    })


@receiver(post_save, sender=Message)
def refresh_conversation(sender, instance, created, **kwargs):
    if not created:
        return
    _push(instance.recipient_id, {
        "type": "refresh_conv",
        "timestamp": str(instance.created_at),
    })
