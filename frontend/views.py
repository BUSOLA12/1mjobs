from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
import logging

from django.shortcuts import render
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='app.log',  # Log messages will be saved to 'app.log'
    filemode='a'  # Append to the log file instead of overwriting
)

logger = logging.getLogger(__name__)


def testing(request):
    return render(request, 'frontend/test.html')

def payments_page(request):
    # if request.user.role != 'employer':
    #     return render(request, 'frontend/freelancer-payments.html')
    return render(request, 'frontend/employer-payments.html')

def password_reset_request_view(request):
    return render(request, 'frontend/request-reset-password.html')

def reset_password_view(request, uid, token):
    User = get_user_model()
    token_generator = PasswordResetTokenGenerator()
    
    try:
        # Decode the uid from base64 to find the user
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Validate the token for the specific user
    if user is not None and token_generator.check_token(user, token):
        context = {
            "uid": uid,
            "token": token
        }
        return render(request, "frontend/reset-password.html", context)
    else:
        # Display unauthorized message if token is invalid or expired
        return render(request, "frontend/unauthorised.html", {"message": "Unauthorised activity or expired link."})


def browse_companies(request):
    return render(request, 'frontend/browse-companies.html')

@login_required(login_url='/login/')
def dashboard_bookmarks(request):
    return render(request, 'frontend/dashboard-bookmarks.html')

@login_required(login_url='/login/')
def dashboard_manage_bidders(request, task_id=None):
    return render(request, 'frontend/dashboard-manage-bidders.html')

@login_required(login_url='/login/')
def dashboard_manage_candidates(request, job_id=None):
    return render(request, 'frontend/dashboard-manage-candidates.html')

@login_required(login_url='/login/')
def dashboard_manage_jobs(request):
    return render(request, 'frontend/dashboard-manage-jobs.html')

@login_required(login_url='/login/')
def dashboard_manage_tasks(request):
    return render(request, 'frontend/dashboard-manage-tasks.html')

@login_required(login_url='/login/')
def dashboard_messages(request):
    return render(request, 'frontend/dashboard-messages.html')

@login_required(login_url='/login/')
def dashboard_my_active_bids(request):
    return render(request, 'frontend/dashboard-my-active-bids.html')

@login_required(login_url='/login/')
def dashboard_post_a_job(request):
    return render(request, 'frontend/dashboard-post-a-job.html')

@login_required(login_url='/login/')
def dashboard_post_a_task(request):
    return render(request, 'frontend/dashboard-post-a-task.html')

@login_required(login_url='/login/')
def dashboard_post_a_company(request):
    return render(request, 'frontend/dashboard-post-a-company.html')

@login_required(login_url='/login/')
def dashboard_reviews(request):
    return render(request, 'frontend/dashboard-reviews.html')

@login_required(login_url='/login/')
def dashboard_settings(request):
    return render(request, 'frontend/dashboard-settings.html')

@login_required(login_url='/login/')
def dashboard_edit_job(request, job_id=None):
    return render(request, 'frontend/dashboard-edit-job.html')

@login_required(login_url='/login/')
def dashboard_edit_task(request, task_id=None):
    return render(request, 'frontend/dashboard-edit-task.html')

@login_required(login_url='/login/')
def dashboard(request):
    if request.user.role == 'admin':
        return redirect("admin-dashboard")
    return render(request, 'frontend/dashboard.html')

@login_required(login_url='/login/')
def admin_manage_job(request):
    if request.user.role == 'admin':
        return render(request, 'frontend/admin-dashboard-manage-jobs.html')
    


@login_required(login_url='/login/')
def admin_dashboard(request):
    if not request.user.role == 'admin':
        return redirect("pages_404")
    return render(request, 'frontend/admin-dashboard.html')

def freelancers_grid_layout_full_page(request):
    return render(request, 'frontend/freelancers-grid-layout-full-page.html')

def freelancers_grid_layout(request):
    return render(request, 'frontend/freelancers-grid-layout.html')

def freelancers_list_layout_1(request):
    return render(request, 'frontend/freelancers-list-layout-1.html')

def freelancers_list_layout_2(request):
    return render(request, 'frontend/freelancers-list-layout-2.html')

def index_2(request):
    return render(request, 'frontend/index-2.html')

def index_3(request):
    return render(request, 'frontend/index-3.html')

def index_logged_out(request):
    return render(request, 'frontend/index-logged-out.html')

def index_htm(request):
    return render(request, 'frontend/index.htm')

def index(request):
    return render(request, 'frontend/index.html')

def jobs_grid_layout_full_page_map_openstreetmap(request):
    return render(request, 'frontend/jobs-grid-layout-full-page-map-OpenStreetMap.html')

def jobs_grid_layout_full_page_map(request):
    return render(request, 'frontend/jobs-grid-layout-full-page-map.html')

def jobs_grid_layout_full_page(request):
    return render(request, 'frontend/jobs-grid-layout-full-page.html')

def jobs_grid_layout(request):
    return render(request, 'frontend/jobs-grid-layout.html')

def jobs_list_layout_1_openstreetmap(request):
    return render(request, 'frontend/jobs-list-layout-1-OpenStreetMap.html')

def jobs_list_layout_1(request):
    return render(request, 'frontend/jobs-list-layout-1.html')

def jobs_list_layout_2(request):
    return render(request, 'frontend/jobs-list-layout-2.html')

def jobs_list_layout_full_page_map_openstreetmap(request):
    return render(request, 'frontend/jobs-list-layout-full-page-map-OpenStreetMap.html')

def jobs_list_layout_full_page_map(request):
    return render(request, 'frontend/jobs-list-layout-full-page-map.html')


def pages_404(request):
    return render(request, 'frontend/pages-404.html')

def pages_blog_post(request):
    return render(request, 'frontend/pages-blog-post.html')
    
def pages_privacy_policy(request):
    return render(request, 'frontend/pages-privacy-policy.html')

@login_required(login_url='/login/')
def offer_page(request, id=None):
    return render(request, 'frontend/offer.html')

def pages_term_of_use(request):
    return render(request, 'frontend/pages-term-of-use.html')

def pages_blog(request):
    return render(request, 'frontend/pages-blog.html')

@login_required(login_url='/login/')
def pages_checkout_page(request, id=None):
    return render(request, 'frontend/pages-checkout-page.html')

def pages_contact_openstreetmap(request):
    return render(request, 'frontend/pages-contact-OpenStreetMap.html')

def pages_contact(request):
    return render(request, 'frontend/pages-contact.html')

def pages_icons_cheatsheet(request):
    return render(request, 'frontend/pages-icons-cheatsheet.html')

@login_required(login_url='/login/')
def pages_invoice_template(request, id=None):
    return render(request, 'frontend/pages-invoice-template.html')

def pages_login(request):
    if request.user.is_authenticated:
        logger.debug(f"Redirecting {request.user} with role {request.user.role}")
        if request.user.role == 'admin':
            
            return redirect("admin-dashboard")
        return redirect("dashboard")
    return render(request, 'frontend/pages-login.html')



def pages_404(request):
    return render(request, 'frontend/pages-404.html')

@login_required(login_url='/login/')
def pages_order_confirmation(request):
    return render(request, 'frontend/pages-order-confirmation.html')

def pages_pricing_plans(request):
    return render(request, 'frontend/pages-pricing-plans.html')

def pages_register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, 'frontend/pages-register.html')

def pages_user_interface_elements(request):
    
    return render(request, 'frontend/pages-user-interface-elements.html')

def single_company_profile_openstreetmap(request):
    return render(request, 'frontend/single-company-profile-OpenStreetMap.html')

def single_company_profile(request):
    return render(request, 'frontend/single-company-profile.html')

def single_freelancer_profile(request, id=None):
    return render(request, 'frontend/single-freelancer-profile.html')

def single_job_page_openstreetmap(request):
    return render(request, 'frontend/single-job-page-OpenStreetMap.html')

def single_job_page(request, job_id=None):
    return render(request, 'frontend/single-job-page.html')

def single_task_page(request, task_id=None):
    return render(request, 'frontend/single-task-page.html')

def tasks_grid_layout_full_page(request):
    return render(request, 'frontend/tasks-grid-layout-full-page.html')

def tasks_grid_layout(request):
    return render(request, 'frontend/tasks-grid-layout.html')

def tasks_list_layout_1(request):
    return render(request, 'frontend/tasks-list-layout-1.html')

def tasks_list_layout_2(request):
    return render(request, 'frontend/tasks-list-layout-2.html')
