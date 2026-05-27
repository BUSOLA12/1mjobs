"""
ASGI config for jobwebsite project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobwebsite.settings')

# This sets up Django and loads settings
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import Messaging.routing  # Import AFTER Django is set up

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(
        Messaging.routing.websocket_urlpatterns
    ),
})
