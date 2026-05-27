from django.urls import path
from . import views

urlpatterns = [
    path('', views.BookmarkListView.as_view()),
    path('create/', views.BookmarkCreateView.as_view()),
    path('<int:id>/delete/', views.BookmarkDeleteView.as_view()),
]