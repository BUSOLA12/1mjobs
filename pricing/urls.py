from django.urls import path
from . import views

urlpatterns = [
    path('plans/', views.PlanListView.as_view(), name='plan-list'),
    path('plan/price/', views.PlanPriceView.as_view(), name='plan-price'),
    path('orders/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/me/', views.OrderListView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderRetrieveUpdateView.as_view(), name='order-detail'),
    path('subscription/active/', views.SubscriptionDetailView.as_view(), name='subscription-active'),
    path('checkout/<int:pk>/', views.CheckoutOrderDetailView.as_view(), name='checkout-order-detail'),
    
    path('subscription/check/', views.SubscriptionCheckView.as_view(), name='subscription-check'),


    path('payment/confirmation/', views.PaymentConfirmationView.as_view(), name='payment_confirmation'),
]
