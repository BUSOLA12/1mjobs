from django.urls import path
from .views import (
    JobCreateAPIView, 
    JobDetailAPIView, TaskCreateAPIView, 
    TaskManageAPIView, TaskDetailAPIView, 
    JobSimilarAPIView, JobApplicationCreateAPIView, 
    JobCategoriesGetAPIView, ManageJobAPIView, 
    JobApplicationDeleteAPIView, JobApplicationCountAPIView,
    JobApplicationAcceptAPIView,
    MyJobApplicationsAPIView,
    TaskBiddingCreateAPIView, TaskBiddingGetAPIView, 
    TaskBiddingAcceptAPIView, TaskBiddingRejectAPIView, 
    TaskBiddingCountAPIView, TaskBidWonAndJobAppliedView, OnSJPTaskBiddingGetAPIView,
    JobGetAPIView, FeaturedJobsAPIView, FeaturedJobsCitiesAPIView
    )

urlpatterns = [
    path('jobs/update/<int:pk>/', JobCreateAPIView.as_view(), name='job-create'),
    path('jobs/create/', JobCreateAPIView.as_view(), name='job-create'),
    path('jobs/list/', JobGetAPIView.as_view(), name='job-list'),
    path('jobs/detail/<int:pk>/', JobDetailAPIView.as_view(), name='job-detail'),
    path('jobs/<int:pk>/delete/', JobCreateAPIView.as_view(), name='job-delete'),
    path('jobs/similar/<int:pk>/', JobSimilarAPIView.as_view(), name='job-delete'),
    path('jobs/application/', JobApplicationCreateAPIView.as_view(), name='job-application'),
    path('jobs/getapplication/<int:jobId>/', JobApplicationCreateAPIView.as_view(), name='job-getapplication'),
    path('jobs/myapplications/', MyJobApplicationsAPIView.as_view(), name='job-myapplications'),
    path('jobs/deleteapplication/<int:pk>/', JobApplicationDeleteAPIView.as_view(), name='job-deleteapplication'),
    path('jobs/acceptapplication/<int:pk>/', JobApplicationAcceptAPIView.as_view(), name='job-application-accept'),
    path('jobs/getapplicantcount/<int:pk>/', JobApplicationCountAPIView.as_view(), name='job-countapplication'),
    path('jobs/job-categories/', JobCategoriesGetAPIView.as_view(), name='job-categories'),
    path('jobs/managelist/', ManageJobAPIView.as_view(), name='manage-list'),
    path('jobs/featured-jobs/', FeaturedJobsAPIView.as_view(), name='featured-jobs'),
    path('jobs/featured-city/', FeaturedJobsCitiesAPIView.as_view(), name='featured-city'),

    path('tasks/update/<int:pk>/', TaskCreateAPIView.as_view(), name='job-create'),
    path('tasks/create/', TaskCreateAPIView.as_view(), name='task-create'),
    path('tasks/managelist/', TaskManageAPIView.as_view(), name='task-managelist'),
    path('tasks/createbidding/', TaskBiddingCreateAPIView.as_view(), name='task-bidding-create'),
    path('tasks/getbidding/', TaskBiddingCreateAPIView.as_view(), name='task-bidding-get'),
    path('tasks/gettaskbidings/<int:pk>/', TaskBiddingGetAPIView.as_view(), name='task-biddings-get'),
    path('tasks/task-bidings/<int:pk>/', OnSJPTaskBiddingGetAPIView.as_view(), name='task-biddings-get-on-sjp'),

    
    path('tasks/updatebidding/<int:pk>/', TaskBiddingCreateAPIView.as_view(), name='task-bidding-update'),
    path('tasks/deletebidding/<int:pk>/', TaskBiddingCreateAPIView.as_view(), name='task-bidding-delete'),
    path('tasks/acceptbid/<int:pk>/', TaskBiddingAcceptAPIView.as_view(), name='task-bidding-accept'),
    path('tasks/rejectbid/<int:pk>/', TaskBiddingRejectAPIView.as_view(), name='task-bidding-reject'),
    path('tasks/gettaskbidcount/<int:pk>/', TaskBiddingCountAPIView.as_view(), name='task-bidding-count'),
    path('tasks/list/', TaskCreateAPIView.as_view(), name='task-list'),
    path('tasks/detail/<int:pk>/', TaskDetailAPIView.as_view(), name='job-detail'),
    path('tasks/<int:pk>/delete/', TaskCreateAPIView.as_view(), name='task-delete'),


    #task and job count
    path('taskandbidcount/', TaskBidWonAndJobAppliedView.as_view(), name='taskbidcount'),
]