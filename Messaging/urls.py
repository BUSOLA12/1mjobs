from django.urls import path
from . import views


urlpatterns = [
    # Conversation endpoints
    path('jobconversationcreate/', views.JobConversationView.as_view(), name='create-conversation'),
    path('conversationget/', views.GetConversationView.as_view(), name='get-conversation'),
    path('taskconversationcreate/', views.TaskConversationView.as_view(), name='create-task-conversation'),
    path('deleteconversation/<int:pk>/', views.GetConversationView.as_view(), name='delete-conversation'),
    path('searchconversation/', views.GetConversationView.as_view(), name='search-conversation'),


    
    #Message endpoints
    path('messageget/<int:conversation_id>/', views.MessageView.as_view(), name='get-message'),
    path('messagecreate/', views.MessageView.as_view(), name='create-message'),
    
    # Notification endpoints
    path('unread-notifications/', views.UnreadNotificationView.as_view(), name='unread-notifications'),
    path('mark-one-read/<int:pk>/', views.MarkOneReadView.as_view(), name='mark-one-read'),
    path('mark-all-read/', views.MarkAllReadView.as_view(), name='mark-all-read'),
    
]