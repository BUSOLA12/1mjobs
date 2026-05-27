from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Review(models.Model):
    """
    Generic review linking a reviewer -> reviewee for a particular object (Job or Task).
    Once created, it can be edited within 7 days only (enforced at API layer).
    """
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews_given', on_delete=models.CASCADE)
    reviewee = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='reviews_received', on_delete=models.CASCADE)

    # Generic relation to Job or Task
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1..5, rating can be provided w/o review_text
    review_text = models.TextField(blank=True, null=True)
    on_budget = models.BooleanField(default=False)
    on_time = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # updated only if within one week

    class Meta:
        ordering = ['-created_at']
        unique_together = ('reviewer', 'content_type', 'object_id')  # one review per reviewer per object

    def __str__(self):
        return f"Review {self.id} by {self.reviewer_id} for {self.reviewee_id} on {self.content_type}#{self.object_id}"

    @property
    def editable_until(self):
        """
        Returns the datetime until which this review is editable (7 days after creation).
        """
        from django.utils import timezone
        return self.created_at + timezone.timedelta(days=7)

    def is_editable(self):
        from django.utils import timezone
        return timezone.now() <= self.editable_until
