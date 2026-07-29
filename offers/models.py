from django.db import models
from django.conf import settings

class Offer(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers_sent'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='offers_received'
    )

    sender_full_name = models.CharField(max_length=255)
    sender_email = models.EmailField()

    # An offer may be tied to one of the sender's jobs or tasks (optional).
    job = models.ForeignKey(
        'ManageJobsTasks.Job', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='offers'
    )
    task = models.ForeignKey(
        'ManageJobsTasks.Task', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='offers'
    )

    message = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Offer from {self.sender_email} to {self.receiver.email}"


class OfferFile(models.Model):
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name="files"
    )
    file = models.FileField(upload_to="offers/files/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for Offer ID {self.offer_id}"
