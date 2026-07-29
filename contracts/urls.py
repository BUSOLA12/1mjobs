from django.urls import path

from .views import (
    SendJobOfferAPIView,
    RespondJobOfferAPIView,
    OffersReceivedListAPIView,
    OffersSentListAPIView,
    SendTaskOfferAPIView,
    RespondTaskOfferAPIView,
    TaskOffersReceivedListAPIView,
    TaskOffersSentListAPIView,
    ContractListAPIView,
    ContractDetailAPIView,
    FundContractAPIView,
    FundPeriodAPIView,
    ContractDocumentUploadAPIView,
    SubmitProjectAPIView,
    ReviewSubmissionAPIView,
    RaiseDisputeAPIView,
    CreateAssignmentAPIView,
    SubmitAssignmentAPIView,
    ReviewAssignmentAPIView,
    RequestTerminationAPIView,
)

urlpatterns = [
    path("offers/send/", SendJobOfferAPIView.as_view(), name="job-offer-send"),
    path("offers/<int:pk>/respond/", RespondJobOfferAPIView.as_view(), name="job-offer-respond"),
    path("offers/received/", OffersReceivedListAPIView.as_view(), name="job-offers-received"),
    path("offers/sent/", OffersSentListAPIView.as_view(), name="job-offers-sent"),

    path("task-offers/send/", SendTaskOfferAPIView.as_view(), name="task-offer-send"),
    path("task-offers/<int:pk>/respond/", RespondTaskOfferAPIView.as_view(), name="task-offer-respond"),
    path("task-offers/received/", TaskOffersReceivedListAPIView.as_view(), name="task-offers-received"),
    path("task-offers/sent/", TaskOffersSentListAPIView.as_view(), name="task-offers-sent"),

    path("list/", ContractListAPIView.as_view(), name="contract-list"),
    path("<int:pk>/", ContractDetailAPIView.as_view(), name="contract-detail"),
    path("<int:pk>/fund/", FundContractAPIView.as_view(), name="contract-fund"),
    path("periods/<int:pk>/fund/", FundPeriodAPIView.as_view(), name="period-fund"),
    path("<int:pk>/documents/", ContractDocumentUploadAPIView.as_view(), name="contract-document-upload"),
    path("<int:pk>/submit/", SubmitProjectAPIView.as_view(), name="contract-submit"),
    path("<int:pk>/review/", ReviewSubmissionAPIView.as_view(), name="contract-review"),
    path("<int:pk>/dispute/", RaiseDisputeAPIView.as_view(), name="contract-dispute"),
    path("<int:pk>/assignments/", CreateAssignmentAPIView.as_view(), name="assignment-create"),
    path("assignments/<int:pk>/submit/", SubmitAssignmentAPIView.as_view(), name="assignment-submit"),
    path("assignments/<int:pk>/review/", ReviewAssignmentAPIView.as_view(), name="assignment-review"),
    path("<int:pk>/terminate/", RequestTerminationAPIView.as_view(), name="contract-terminate"),
]
