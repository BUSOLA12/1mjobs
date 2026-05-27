from django.urls import path
from .views import (
    CreateReviewView, UpdateReviewView, ReviewsReceivedView,
    ReviewsByObjectView, PendingReviewsView, MyReviewsView
)

urlpatterns = [
    path('create/', CreateReviewView.as_view(), name='reviews-create'),
    path('<int:pk>/update/', UpdateReviewView.as_view(), name='reviews-update'),
    path('user/<int:user_id>/', ReviewsReceivedView.as_view(), name='reviews-received'),
    path('object/<str:model_type>/<int:object_id>/', ReviewsByObjectView.as_view(), name='reviews-by-object'),
    path('pending/', PendingReviewsView.as_view(), name='reviews-pending'),
    path('mine/', MyReviewsView.as_view(), name='reviews-mine'),
]
