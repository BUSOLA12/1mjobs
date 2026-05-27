from notifications.utils import send_email
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MessageContact, AdminProfile
from django.conf import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',  # Log messages will be saved to 'app.log'
    filemode='a'  # Append to the log file instead of overwriting
)


logger = logging.getLogger(__name__)

@receiver(post_save, sender=MessageContact)
def send_contact_email_notification(sender, instance, created, **kwargs):
    logger.info("--- Signal Fired ---")

    if created:
        logger.info(f"--- New MessageContact created (ID: {instance.id}) ---")
        admin_profile = AdminProfile.objects.first()
        
        if admin_profile and admin_profile.gmail:
            logger.info(f"--- Admin found: {admin_profile.gmail}. Attempting to send email. ---")
            send_email(
                name=instance.name, 
                subject=instance.subject, 
                body=instance.message,
                their_email=instance.email,
                to=admin_profile.gmail
            )
            logger.info("--- send_email function was called. ---")
        else:
            logger.info("--- ERROR: No admin profile found or admin has no gmail address. ---")