from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.CreateOfferView.as_view(), name="offer-create"),
    path("received/", views.OfferReceivedListView.as_view(), name="offers-received"),
    path("sent/", views.OfferSentListView.as_view(), name="offers-sent"),
    path("<int:pk>/", views.OfferDetailView.as_view(), name="offer-detail"),
    path("<int:pk>/conversation/", views.OfferConversationView.as_view(), name="offer-conversation"),
    path("<int:pk>/delete/", views.OfferDeleteView.as_view(), name="offer-delete"),
]
