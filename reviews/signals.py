from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Review
from .utils import update_user_aggregate_rating

@receiver(post_save, sender=Review)
def review_post_save(sender, instance, created, **kwargs):
    if created:
        # update aggregate rating for the reviewee (will raise if profile fields missing)
        try:
            update_user_aggregate_rating(instance.reviewee)
        except Exception:
            # in production log the exception; don't raise to avoid blocking
            pass
