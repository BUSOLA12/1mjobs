from django.urls import path
from .views import CreateCompanyAPIView, CompanyExistsAPIView


urlpatterns = [
    path('create/', CreateCompanyAPIView.as_view(), name='company-create'),
    path('get/<int:pk>/', CreateCompanyAPIView.as_view(), name='company-get'),
    path('exists/<int:pk>/', CompanyExistsAPIView.as_view(), name='company-exists'),

]
