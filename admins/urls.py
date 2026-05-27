from django.urls import path
from .views import SocialsAPIView, ContactAPIView, message_contact_view

urlpatterns = [
    path('socials/', SocialsAPIView.as_view(), name='social-view'),
    path('contact/', ContactAPIView.as_view(), name='contact-view'),
    path('message-contact/', message_contact_view, name='message-contact-view'),
]