
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


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


    
]

if settings.DEBUG:

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

