
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('ManageJobsTasks.urls')),
    path('api/messaging/', include('Messaging.urls')), 
    path('api/notifications/', include('notifications.urls')),
    path('api/companies/', include('company.urls')),  
    path('api/admins/', include('admins.urls')),  

    # Include the frontend URLs
    path('', include('frontend.urls')),
    path('site-admin/', include('adminpanel.urls')),

    # Include the API URLs
    path('api/auth/', include('authentication.urls')),
    path('api/users/', include('users.urls')),
    path('api/pricing/', include('pricing.urls')),
    path('api/bookmarks/', include('bookmarks.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/offers/', include('offers.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/contracts/', include('contracts.urls')),


    
]

# Custom error handler for unmatched URLs (active when DEBUG=False)
handler404 = 'frontend.views.custom_404'

# User-uploaded media (avatars, CVs, etc.) lives on the persistent volume at
# MEDIA_ROOT. WhiteNoise only serves STATIC files, and the DEBUG-only static()
# helper below does not run in production, so without this route /media/ URLs
# 404 in prod and uploaded images never display. Daphne serves them directly
# here since this is a single machine with the media on a local volume.
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

