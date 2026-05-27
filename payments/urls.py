from django.urls import path
from . import views


urlpatterns = [
    # path("wallet/", views.WalletView.as_view()),
    # path("transactions/", views.TransactionListView.as_view()),
    # path("escrow/<int:escrow_id>/release/", views.ReleaseEscrowView.as_view()),
    # path("withdraw/", views.WithdrawView.as_view()),
    # path("webhook/", views.PaymentWebhookView.as_view()),

    path("employer/", views.EmployerPaymentListAPIView.as_view()),
    path("employer/<int:pk>/", views.EmployerPaymentDetailAPIView.as_view()),
    path("employer/<int:pk>/initiate/", views.InitiatePaymentAPIView.as_view()),
]