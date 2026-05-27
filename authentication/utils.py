from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sessions.models import Session
from rest_framework.permissions import BasePermission
from .models import EmailVerificationCode
from django.conf import settings
from django.core.mail import send_mail
import random

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


def renew_session(request):
    request.session.set_expiry(60 * 60 * 24)  # 1 day again


def send_verification_email(user):
    # Generate OTP
    code = str(random.randint(100000, 999999))

    # Store OTP
    EmailVerificationCode.objects.create(user=user, code=code)

    send_mail(
        "Verify Your Email",
        f"Your verification code is: {code}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

