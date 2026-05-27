from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django.utils import timezone
from .models import UserProfile, UserActivityLog

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile_exists(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

@receiver(user_logged_in)
def log_user_login(sender, user, request, **kwargs):
    ip = request.META.get("REMOTE_ADDR")
    ua = request.META.get("HTTP_USER_AGENT", "")
    UserActivityLog.objects.create(user=user, action="login", ip_address=ip, user_agent=ua)

@receiver(user_logged_out)
def log_user_logout(sender, user, request, **kwargs):
    try:
        ip = request.META.get("REMOTE_ADDR")
    except Exception:
        ip = None
    ua = request.META.get("HTTP_USER_AGENT", "")
    UserActivityLog.objects.create(user=user, action="logout", ip_address=ip, user_agent=ua)

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    ip = request.META.get("REMOTE_ADDR") if request else None
    ua = request.META.get("HTTP_USER_AGENT", "") if request else None
    # user may be None at failed login, we leave user null
    UserActivityLog.objects.create(user=None, action="failed_login", metadata={"credentials": credentials, "ip": ip, "ua": ua})
