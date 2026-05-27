from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.UserProfileView.as_view()),
    path('avatar/', views.UploadAvatarView.as_view()),
    path('status/', views.UserStatusToggleView.as_view()),
    path('profiles/', views.ProfileListView.as_view(), name='profile-list'),
    path('profiles/<int:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('profile/edit/', views.EditUserProfileView.as_view(), name='edit-profile'),
    path('profile/files/', views.UserFilesView.as_view(), name='edit-profile-file'),
    path('profile/files/upload/', views.UserFilesUploadView.as_view(), name='my-files-upload'),
    path('profile/files/<int:pk>/', views.UserFileDetailView.as_view(), name='my-file-detail'),
    path("work-history/", views.WorkHistoryListCreateView.as_view(), name="work-history-list-create"),
    path("work-history/<int:pk>/", views.WorkHistoryDetailView.as_view(), name="work-history-detail"),
    path('currentuser/<int:pk>/', views.ProfileDetailView.as_view(), name='current-user'),
    path('currentuser/', views.CurrentUserAPIView.as_view(), name='current-user'),

]