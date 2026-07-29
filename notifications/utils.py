from .models import Notification
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


User = get_user_model()

def create_notification(title, message, recipient=None, related_object=None):
    if recipient is None:
        users = User.objects.all()
        for user in users:
            Notification.objects.create(
                title=title,
                message=message,
                recipient=user,
                related_object=related_object
            )

    elif isinstance(recipient, list):
        for user in recipient:
            Notification.objects.create(
                title=title,
                message=message,
                recipient=user,
                related_object=related_object
            )

    else:
        Notification.objects.create(
                title=title,
                message=message,
                recipient=recipient,
                related_object=related_object
            )


def send_email(name, subject, body, to, their_email, from_email=None, link=None):
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    context = {
        "name": name,
        "email": their_email,
        "subject": subject,
        "body": body,
        "link": link,
    }
    html_content = render_to_string("emails/contact_mails.html", context)
    email = EmailMultiAlternatives(subject=subject, body=body, from_email=from_email, to=[to])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)