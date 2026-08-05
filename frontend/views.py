from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model

from datetime import timedelta
from django.utils import timezone

from company.models import Company, VERIFIABLE_FIELDS
from users.models import UserKYC
from users.forms import KYCSubmitForm
from company.forms import CompanyResubmitForm
from authentication.models import EmailVerificationCode
from authentication.utils import send_verification_email

# How long an emailed verification code stays valid.
EMAIL_CODE_VALIDITY_MINUTES = 10


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
    # Freelancers use the Wallet as their earnings hub; employers manage the
    # payments they make to freelancers here.
    if getattr(request.user, "role", None) == "freelancer":
        return redirect('wallet_page')
    return render(request, 'frontend/employer-payments.html')

def wallet_page(request):
    # Dedicated wallet: balances (available/pending) + transaction history.
    # Balances/transactions are loaded client-side from the payments API.
    return render(request, 'frontend/wallet.html')

def billing_history_page(request):
    return render(request, 'frontend/billing-history.html')

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
def dashboard_contracts(request):
    return render(request, 'frontend/dashboard-contracts.html')

@login_required(login_url='/login/')
def dashboard_contract_detail(request, pk=None):
    # Render the employer or freelancer view depending on which party the viewer
    # is on THIS contract (not their global account role). Non-parties are sent
    # back to the contracts list. Live data is still fetched client-side from
    # /api/contracts/<id>/, which independently enforces party-only access.
    from contracts.models import Contract

    contract = Contract.objects.filter(pk=pk).first()
    if contract is None:
        return redirect('dashboard_contracts')

    if request.user.id == contract.employer_id:
        return render(request, 'frontend/dashboard-contract-detail-employer.html')
    if request.user.id == contract.freelancer_id:
        return render(request, 'frontend/dashboard-contract-detail-freelancer.html')

    return redirect('dashboard_contracts')

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
def dashboard_my_applications(request):
    return render(request, 'frontend/dashboard-my-applications.html')

@login_required(login_url='/login/')
def dashboard_post_a_job(request):
    from ManageJobsTasks.models import JobCategory
    return render(request, 'frontend/dashboard-post-a-job.html', {
        'job_categories': JobCategory.objects.filter(is_active=True),
    })

@login_required(login_url='/login/')
def dashboard_post_a_task(request):
    return render(request, 'frontend/dashboard-post-a-task.html')

@login_required(login_url='/login/')
def dashboard_post_a_company(request):
    return render(request, 'frontend/dashboard-post-a-company.html')

@login_required(login_url='/login/', redirect_field_name='redirect')
def verify_identity(request):
    if request.user.role != 'freelancer':
        messages.info(request, 'Identity verification is for freelancer accounts.')
        return redirect('dashboard')
    kyc = UserKYC.objects.filter(user=request.user).first()
    if request.method == 'POST':
        action = request.POST.get('action')

        # Freelancer requests an email verification code.
        if action == 'send_email_code':
            if request.user.verified_email:
                messages.info(request, 'Your email is already verified.')
            else:
                send_verification_email(request.user)
                messages.success(request, f'A verification code was sent to {request.user.email}.')
            return redirect('verify_identity')

        # Freelancer submits the code to verify their email.
        if action == 'verify_email_code':
            if request.user.verified_email:
                messages.info(request, 'Your email is already verified.')
                return redirect('verify_identity')
            code = (request.POST.get('email_code') or '').strip()
            cutoff = timezone.now() - timedelta(minutes=EMAIL_CODE_VALIDITY_MINUTES)
            record = (
                EmailVerificationCode.objects
                .filter(user=request.user, code=code, created_at__gte=cutoff)
                .first()
            )
            if record:
                request.user.verified_email = True
                request.user.save(update_fields=['verified_email'])
                EmailVerificationCode.objects.filter(user=request.user).delete()
                messages.success(request, 'Your email has been verified.')
            else:
                messages.error(request, 'Invalid or expired verification code. Please request a new one.')
            return redirect('verify_identity')

        form = KYCSubmitForm(request.POST, request.FILES, instance=kyc)
        if form.is_valid():
            kyc = form.save(commit=False)
            kyc.user = request.user
            kyc.verification_status = 'pending'   # resubmitting resets to pending
            kyc.notes = ''
            kyc.save()
            messages.success(request, 'Your identity documents were submitted for review.')
            return redirect('verify_identity')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = KYCSubmitForm(instance=kyc)
    return render(request, 'frontend/verify-identity.html', {'form': form, 'kyc': kyc})

@login_required(login_url='/login/', redirect_field_name='redirect')
def company_edit_resubmit(request):
    company = Company.objects.filter(created_by=request.user).first()
    if not company:
        return redirect('dashboard_post_a_company')

    if request.method == 'POST':
        form = CompanyResubmitForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save(commit=False)
            # Any field the admin flagged is reset to pending so only changed
            # fields get re-checked; already-approved fields keep their status.
            reviews = company.field_reviews or {}
            for name, meta in list(reviews.items()):
                if meta.get('status') == 'rejected':
                    reviews[name] = {'status': 'pending', 'note': ''}
            company.field_reviews = reviews
            company.recompute_verification()
            company.save()
            messages.success(request, 'Your changes were resubmitted for review.')
            return redirect('company_edit_resubmit')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = CompanyResubmitForm(instance=company)

    rejected = [
        (label, company.get_field_note(name))
        for name, label in VERIFIABLE_FIELDS
        if company.get_field_status(name) == 'rejected'
    ]
    return render(request, 'frontend/company-edit-resubmit.html',
                  {'form': form, 'company': company, 'rejected': rejected})

@login_required(login_url='/login/')
def dashboard_reviews(request):
    return render(request, 'frontend/dashboard-reviews.html')

@login_required(login_url='/login/')
def dashboard_settings(request):
    return render(request, 'frontend/dashboard-settings.html')

@login_required(login_url='/login/')
def dashboard_edit_job(request, job_id=None):
    from ManageJobsTasks.models import JobCategory
    return render(request, 'frontend/dashboard-edit-job.html', {
        'job_categories': JobCategory.objects.filter(is_active=True),
    })

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
    return render(request, 'frontend/pages-contact.html', {
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    })

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


def account_suspended(request):
    return render(request, 'frontend/account-suspended.html')



def pages_404(request):
    return render(request, 'frontend/pages-404.html')

@login_required(login_url='/login/')
def pages_order_confirmation(request):
    return render(request, 'frontend/pages-order-confirmation.html')

@login_required(login_url='/login/')
def pages_payment_confirmation(request):
    # Employer returns here from African Money after paying a freelancer; the
    # page JS verifies the collection and moves the payment into escrow.
    return render(request, 'frontend/pages-payment-confirmation.html')

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

def single_company_profile(request, id=None):
    return render(request, 'frontend/single-company-profile.html', {
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    })

def single_freelancer_profile(request, id=None):
    return render(request, 'frontend/single-freelancer-profile.html')

def single_job_page_openstreetmap(request):
    return render(request, 'frontend/single-job-page-OpenStreetMap.html')

def single_job_page(request, job_id=None):
    return render(request, 'frontend/single-job-page.html', {
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    })

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

@login_required(login_url='/login/')
def dashboard_my_profile(request):
    return render(request, 'frontend/dashboard-my-profile.html')

def custom_404(request, exception=None):
    return render(request, 'frontend/pages-404.html', status=404)
