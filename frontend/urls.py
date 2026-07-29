from django.urls import path

from . import views

urlpatterns = [
    path('testing/', views.testing, name='testing'),
    path('', views.index, name='index'),
    path('browse-companies/', views.browse_companies, name='browse_companies'),


    # # Dashboard Home
    # path('dashboard/', views.dashboard, name='dashboard'),

    # # Jobs Management
    # path('dashboard/jobs/', views.dashboard_manage_jobs, name='dashboard_manage_jobs'),
    # path('dashboard/jobs/post/', views.dashboard_post_a_job, name='dashboard_post_a_job'),
    # path('dashboard/jobs/<int:job_id>/edit/', views.dashboard_edit_job, name='dashboard_edit_job'),
    # path('dashboard/jobs/<int:job_id>/candidates/', views.dashboard_manage_candidates, name='dashboard_manage_candidates'),

    # # Tasks Management
    # path('dashboard/tasks/', views.dashboard_manage_tasks, name='dashboard_manage_tasks'),
    # path('dashboard/tasks/post/', views.dashboard_post_a_task, name='dashboard_post_a_task'),
    # path('dashboard/tasks/<int:task_id>/edit/', views.dashboard_edit_task, name='dashboard_edit_task'),
    # path('dashboard/tasks/<int:task_id>/bidders/', views.dashboard_manage_bidders, name='dashboard_manage_bidders'),

    # # Companies
    # path('dashboard/companies/post/', views.dashboard_post_a_company, name='dashboard_post_a_company'),

    # # User Activity
    # path('dashboard/bookmarks/', views.dashboard_bookmarks, name='dashboard_bookmarks'),
    # path('dashboard/active-bids/', views.dashboard_my_active_bids, name='dashboard_my_active_bids'),
    # path('dashboard/reviews/', views.dashboard_reviews, name='dashboard_reviews'),

    # # Messages and Settings
    # path('dashboard/messages/', views.dashboard_messages, name='dashboard_messages'),
    # path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/bookmarks/', views.dashboard_bookmarks, name='dashboard_bookmarks'),
    path('dashboard/manage-bidders/<int:task_id>/', views.dashboard_manage_bidders, name='dashboard_manage_bidders'),
    path('dashboard/manage-candidates/<int:job_id>/', views.dashboard_manage_candidates, name='dashboard_manage_candidates'),
    path('dashboard/contracts/', views.dashboard_contracts, name='dashboard_contracts'),
    path('dashboard/contracts/<int:pk>/', views.dashboard_contract_detail, name='dashboard_contract_detail'),
    path('dashboard/manage-jobs/', views.dashboard_manage_jobs, name='dashboard_manage_jobs'),
    path('dashboard/manage-tasks/', views.dashboard_manage_tasks, name='dashboard_manage_tasks'),
    path('dashboard/messages/', views.dashboard_messages, name='dashboard_messages'),
    path('dashboard/my-active-bids/', views.dashboard_my_active_bids, name='dashboard_my_active_bids'),
    path('dashboard/my-applications/', views.dashboard_my_applications, name='dashboard_my_applications'),
    path('dashboard/post-job/', views.dashboard_post_a_job, name='dashboard_post_a_job'),
    path('dashboard/post-task/', views.dashboard_post_a_task, name='dashboard_post_a_task'),
    path('dashboard/reviews/', views.dashboard_reviews, name='dashboard_reviews'),
    path('dashboard/settings/', views.dashboard_settings, name='dashboard_settings'),
    path('dashboard/my-profile/', views.dashboard_my_profile, name='dashboard_my_profile'),
    path('dashboard/edit-job/<int:job_id>/', views.dashboard_edit_job, name='dashboard_edit_job'),
    path('dashboard/edit-task/<int:task_id>/', views.dashboard_edit_task, name='dashboard_edit_task'),
    path('dashboard/edit-task/<int:task_id>/', views.dashboard_edit_task, name='dashboard_edit_task'),
    path('dashboard/post-a-company/', views.dashboard_post_a_company, name='dashboard_post_a_company'),
    path('dashboard/company/edit-resubmit/', views.company_edit_resubmit, name='company_edit_resubmit'),
    path('dashboard/verify-identity/', views.verify_identity, name='verify_identity'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-manage-job/', views.admin_manage_job, name='admin_manage_job'),


    # Freelancers pages
    path('freelancers/', views.freelancers_grid_layout_full_page, name='freelancers'),

    # Index variants
    path('index-2/', views.index_2, name='index_2'),
    path('index-3/', views.index_3, name='index_3'),
    path('index-logged-out/', views.index_logged_out, name='index_logged_out'),
    path('index.htm/', views.index_htm, name='index_htm'),

    # Jobs pages
    path('jobs/', views.jobs_grid_layout_full_page_map_openstreetmap, name='jobs_grid_layout_full_page_map_openstreetmap'),
    path('jobs/grid-layout-full-page-map/', views.jobs_grid_layout_full_page_map, name='jobs_grid_layout_full_page_map'),
    path('jobs/grid-layout-full-page/', views.jobs_grid_layout_full_page, name='jobs_grid_layout_full_page'),
    path('jobs/grid-layout/', views.jobs_grid_layout, name='jobs_grid_layout'),
    path('jobs/list-layout-1-openstreetmap/', views.jobs_list_layout_1_openstreetmap, name='jobs_list_layout_1_openstreetmap'),
    path('jobs/list-layout-1/', views.jobs_list_layout_1, name='jobs_list_layout_1'),
    path('jobs/list-layout-2/', views.jobs_list_layout_2, name='jobs_list_layout_2'),
    path('jobs/list-layout-full-page-map-openstreetmap/', views.jobs_list_layout_full_page_map_openstreetmap, name='jobs_list_layout_full_page_map_openstreetmap'),
    path('jobs/list-layout-full-page-map/', views.jobs_list_layout_full_page_map, name='jobs_list_layout_full_page_map'),

    # Tasks pages
    path('tasks/', views.tasks_grid_layout_full_page, name='tasks_grid_layout_full_page'),
    path('tasks/grid-layout/', views.tasks_grid_layout, name='tasks_grid_layout'),
    path('tasks/list-layout-1/', views.tasks_list_layout_1, name='tasks_list_layout_1'),
    path('tasks/list-layout-2/', views.tasks_list_layout_2, name='tasks_list_layout_2'),

    # Page components
    path('404/', views.pages_404, name='pages_404'),
    # path('pages/blog-post/', views.pages_blog_post, name='pages_blog_post'),
    path('privacy-policy/', views.pages_privacy_policy, name='privacy_policy'),
    path('term-of-use/', views.pages_term_of_use, name='term_of_use'),
    # path('pages/blog/', views.pages_blog, name='pages_blog'),
    path('checkout/<int:id>/', views.pages_checkout_page, name='checkout_page'),
    path('contact-openstreetmap/', views.pages_contact_openstreetmap, name='pages_contact_openstreetmap'),
    path('contact/', views.pages_contact, name='contact'),
    # path('pages/icons/', views.pages_icons_cheatsheet, name='pages_icons_cheatsheet'),
    path('invoice/<int:id>/', views.pages_invoice_template, name='invoice_template'),
    path('login/', views.pages_login, name='login'),
    path('account-suspended/', views.account_suspended, name='account_suspended'),
    path('reset-password/', views.password_reset_request_view, name="password-reset-request"),
    path('reset-password/<uid>/<token>/', views.reset_password_view, name="reset-password"),
    path('order-confirmation/', views.pages_order_confirmation, name='order_confirmation'),
    path('payment-confirmation/', views.pages_payment_confirmation, name='payment_confirmation'),
    path('pricing-plans/', views.pages_pricing_plans, name='pricing_plans'),
    path('register/', views.pages_register, name='register'),
    # path('pages/ui-elements/', views.pages_user_interface_elements, name='pages_user_interface_elements'),

    # Single pages
    path('single/company-profile-openstreetmap/', views.single_company_profile_openstreetmap, name='single_company_profile_openstreetmap'),
    path('single/company-profile/<int:id>/', views.single_company_profile, name='single_company_profile'),
    path('freelancer-profile/<int:id>/', views.single_freelancer_profile, name='single_freelancer_profile'),
    path('job-page-openstreetmap/', views.single_job_page_openstreetmap, name='single_job_page_openstreetmap'),
    path('job-page/<int:job_id>/', views.single_job_page, name='single_job_page'),
    path('task-page/<int:task_id>/', views.single_task_page, name='single_task_page'),
    
    # Offers pages
    path('offers/', views.offer_page, name='offer_page'),

    # payments
    path('payments/', views.payments_page, name='payments_page'),
    path('wallet/', views.wallet_page, name='wallet_page'),
    path('billing/', views.billing_history_page, name='billing_history'),
]

