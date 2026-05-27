from django.urls import path
from .views import NotificationListView, MarkOneNotificationReadView, MarkAllNotificationReadView


urlpatterns = [
    path('notification-list/', NotificationListView.as_view(), name='notification-list'),
    path('mark-one-notification/<int:pk>/', MarkOneNotificationReadView.as_view(), name='mark-one-notification'),
    path('mark-all-notification/', MarkAllNotificationReadView.as_view(), name='mark-all-notification'),

]

