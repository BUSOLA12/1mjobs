from django.urls import path
from .views import base_views
from .views.dashboard import admin_dashboard
from .views import ext, ext1, dev_tools, company_views, kyc_views, settings_views, message_views, appeal_views, finance_views

# app_name = 'adminpanel'

urlpatterns = [

    # ------------------
    # HASSAN
    # ------------------

    path("", base_views.AdminDashboardView.as_view(), name="admin-user-dashboard"),
    path("dashboard/", admin_dashboard, name="admin-dashboard"),

    # User management
    path('users/<int:pk>/edit/', base_views.UserUpdateView.as_view(), name='user-edit'),

    path("users/<int:pk>/suspend/", base_views.suspend_user, name="user-suspend"),
    path("users/<int:pk>/unsuspend/", base_views.unsuspend_user, name="user-unsuspend"),
    path("users/<int:pk>/ban/", base_views.ban_user, name="user-ban"),
    path("users/<int:pk>/unban/", base_views.unban_user, name="user-unban"),

    path("users/<int:pk>/verify/", base_views.admin_verify_user, name="admin_user_verify"),
    path("users/<int:pk>/unverify/", base_views.admin_unverify_user, name="admin_user_unverify"),

    path("logs/admin-actions/", base_views.admin_action_logs, name="admin-action-logs"),
    path("logs/user-actions/", base_views.user_activity_logs, name="user-action-logs"),

    # New User Management
    path("users/", ext.admin_user_list, name="admin_user_list"),
    path("users/<int:user_id>/", ext.admin_user_detail, name="admin_user_detail"),

    path("users/<int:user_id>/billing/", ext.admin_user_billing_history, name="admin_user_billing_history"),





    # Pricing management
    path("pricing/", base_views.AdminPlanListView.as_view(), name="admin-pricing-list"),
    path("pricing/create/", base_views.AdminPlanCreateView.as_view(), name="admin-pricing-create"),
    path("pricing/<int:pk>/", base_views.AdminPlanDetailView.as_view(), name="admin-pricing-detail"),
    path("pricing/<int:pk>/edit/", base_views.AdminPlanEditView.as_view(),name="admin-pricing-edit"),
    path("pricing/<int:pk>/delete/", base_views.AdminPlanDeleteView.as_view(), name="admin-pricing-delete"),

    # Features management
    path("pricing/<int:plan_id>/features/add/", base_views.AdminPlanFeatureCreateView.as_view(), name="admin-feature-add"),
    path("features/<int:feature_id>/edit/", base_views.AdminPlanFeatureUpdateView.as_view(), name="admin-feature-edit"),
    path("features/<int:feature_id>/delete/", base_views.AdminPlanFeatureDeleteView.as_view(), name="admin-feature-delete"),

    # Order management
    path("orders/<int:pk>/mark-paid/", base_views.admin_mark_order_paid, name="admin_mark_order_paid"),
    path("orders/<int:pk>/cancel/", base_views.admin_cancel_order, name="admin_cancel_order"),
    path("orders/<int:pk>/fail/", base_views.admin_fail_order, name="admin_fail_order"),
    path("orders/", base_views.admin_order_list, name="admin_order_list"),
    path("orders/<int:pk>/", base_views.admin_order_detail, name="admin_order_detail"),

    # Transaction management
    path("transactions/", base_views.admin_transaction_list, name="admin_transaction_list"),
    path("transactions/<int:pk>/", base_views.admin_transaction_detail, name="admin_transaction_detail"),

    # Subscription management
    path("subscriptions/", base_views.admin_subscription_list, name="admin_subscription_list"),
    path("subscriptions/<int:pk>/", base_views.admin_subscription_detail, name="admin_subscription_detail"),
    path("subscriptions/<int:pk>/deactivate/", base_views.admin_subscription_deactivate, name="admin_subscription_deactivate"),
    path("subscriptions/<int:pk>/activate/", base_views.admin_subscription_activate, name="admin_subscription_activate"),


    # Job Management
    path("jobs/", ext1.admin_job_list, name="admin_job_list"),
    path("jobs/<int:job_id>/", ext1.admin_job_detail, name="admin_job_detail"),
    path('admin/job-applications/<int:job_id>/', ext1.admin_job_applications_list, name='admin_job_applications'),
    path('admin/job-applications-detail/<int:pk>/', ext1.admin_job_application_detail, name='admin_job_application_detail'),

    # Task Management
    path('admin/tasks/', ext1.admin_task_list, name='admin_task_list'),
    path('admin/tasks/<int:task_id>/', ext1.admin_task_detail, name='admin_task_detail'),
    path('admin/tasks/<int:task_id>/toggle-feature/', ext1.admin_toggle_task_feature, name='admin_toggle_task_feature'),
    path('admin/tasks/<int:task_id>/update-status/', ext1.admin_update_task_status, name='admin_update_task_status'),
    path('admin/tasks/<int:task_id>/delete/', ext1.admin_delete_task, name='admin_delete_task'),

    path('admin/tasks/<int:task_id>/bids/', ext1.admin_task_bidding_list, name='admin_task_bidding_list'),
    path('admin/task-bids/<int:bid_id>/update-status/', ext1.admin_update_task_bid_status, name='admin_update_task_bid_status'),









    # ------------------
    # COMPANY MANAGEMENT
    # ------------------

    path("companies/", company_views.admin_company_list, name="admin_company_list"),
    path("companies/create/", company_views.admin_company_create, name="admin_company_create"),
    path("companies/<int:pk>/", company_views.admin_company_detail, name="admin_company_detail"),
    path("companies/<int:pk>/review/", company_views.admin_review_company, name="admin_company_review"),


    # ------------------
    # KYC / IDENTITY VERIFICATION
    # ------------------

    path("kyc/", kyc_views.admin_kyc_list, name="admin_kyc_list"),
    path("kyc/<int:pk>/", kyc_views.admin_kyc_detail, name="admin_kyc_detail"),
    path("kyc/<int:pk>/approve/", kyc_views.admin_kyc_approve, name="admin_kyc_approve"),
    path("kyc/<int:pk>/reject/", kyc_views.admin_kyc_reject, name="admin_kyc_reject"),


    # ------------------
    # ACCOUNT APPEALS
    # ------------------

    path("appeals/", appeal_views.admin_appeal_list, name="admin_appeal_list"),
    path("appeals/<int:pk>/", appeal_views.admin_appeal_detail, name="admin_appeal_detail"),
    path("appeals/<int:pk>/approve/", appeal_views.admin_appeal_approve, name="admin_appeal_approve"),
    path("appeals/<int:pk>/reject/", appeal_views.admin_appeal_reject, name="admin_appeal_reject"),


    # ------------------
    # WITHDRAWALS (payouts)
    # ------------------

    path("withdrawals/", finance_views.admin_withdrawal_list, name="admin_withdrawal_list"),
    path("withdrawals/<int:pk>/", finance_views.admin_withdrawal_detail, name="admin_withdrawal_detail"),
    path("withdrawals/<int:pk>/mark-paid/", finance_views.admin_withdrawal_mark_paid, name="admin_withdrawal_mark_paid"),
    path("withdrawals/<int:pk>/reject/", finance_views.admin_withdrawal_reject, name="admin_withdrawal_reject"),


    # ------------------
    # DISPUTES
    # ------------------

    path("disputes/", finance_views.admin_dispute_list, name="admin_dispute_list"),
    path("disputes/<int:pk>/", finance_views.admin_dispute_detail, name="admin_dispute_detail"),
    path("disputes/<int:pk>/under-review/", finance_views.admin_dispute_under_review, name="admin_dispute_under_review"),
    path("disputes/<int:pk>/resolve-release/", finance_views.admin_dispute_resolve_release, name="admin_dispute_resolve_release"),
    path("disputes/<int:pk>/resolve-refund/", finance_views.admin_dispute_resolve_refund, name="admin_dispute_resolve_refund"),


    # ------------------
    # TERMINATIONS
    # ------------------

    path("terminations/", finance_views.admin_termination_list, name="admin_termination_list"),
    path("terminations/<int:pk>/", finance_views.admin_termination_detail, name="admin_termination_detail"),
    path("terminations/<int:pk>/execute/", finance_views.admin_termination_execute, name="admin_termination_execute"),
    path("terminations/<int:pk>/deny/", finance_views.admin_termination_deny, name="admin_termination_deny"),


    # ------------------
    # SITE SETTINGS
    # ------------------

    path("settings/contact/", settings_views.admin_contact_settings, name="admin_contact_settings"),

    # Contact messages sent from the public contact page
    path("messages/", message_views.admin_contact_message_list, name="admin_contact_message_list"),
    path("messages/<int:pk>/", message_views.admin_contact_message_detail, name="admin_contact_message_detail"),


    # ------------------
    # DEV TOOLS
    # ------------------

    path("dev/bulk-add/", dev_tools.bulk_add, name="admin_bulk_add"),
    path("dev/bulk-freelancers/", dev_tools.bulk_add_freelancers, name="admin_bulk_add_freelancers"),


    # ------------------
    # BUSOLA
    # ------------------

    
    path('admin-jobs/', base_views.manage_jobs, name='manage_jobs'),
    
    path('admin-jobs/<int:job_id>/status/<str:action>/', base_views.change_job_status, name='change_job_status'),
]


