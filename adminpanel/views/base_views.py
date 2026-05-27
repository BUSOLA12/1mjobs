# ------------------
# HASSAN
# ------------------
from django.contrib.admin.views.decorators import staff_member_required
from adminpanel.utils.base_utils import log_admin_action
from users.models import UserActivityLog

@staff_member_required
def admin_subscription_deactivate(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)

    subscription.is_active = False
    subscription.save(update_fields=["is_active"])

    log_admin_action(request.user, subscription, "Deactivated Subscription")

    messages.success(request, "Subscription deactivated.")
    return redirect("admin_subscription_detail", pk=pk)


@staff_member_required
def admin_subscription_activate(request, pk):
    subscription = get_object_or_404(Subscription, pk=pk)

    if subscription.has_expired():
        messages.warning(request, "Cannot activate expired subscription.")
        return redirect("admin_subscription_detail", pk=pk)

    subscription.is_active = True
    subscription.save(update_fields=["is_active"])

    log_admin_action(request.user, subscription, "Activated Subscription")

    messages.success(request, "Subscription activated.")
    return redirect("admin_subscription_detail", pk=pk)


@staff_member_required
def admin_subscription_detail(request, pk):
    subscription = get_object_or_404(
        Subscription.objects.select_related("user", "plan", "order"),
        pk=pk
    )

    return render(request, "adminpanel/subscriptions/detail.html", {
        "subscription": subscription
    })


from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from pricing.models import Subscription


@staff_member_required
def admin_subscription_list(request):
    subscriptions = Subscription.objects.select_related(
        "user", "plan", "order"
    ).order_by("-start_date")

    # Filters
    status = request.GET.get("status")
    if status == "active":
        subscriptions = subscriptions.filter(is_active=True, end_date__gt=timezone.now())
    elif status == "expired":
        subscriptions = subscriptions.filter(end_date__lt=timezone.now())
    elif status == "inactive":
        subscriptions = subscriptions.filter(is_active=False)

    search = request.GET.get("search")
    if search:
        subscriptions = subscriptions.filter(
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(plan__name__icontains=search)
        )

    paginator = Paginator(subscriptions, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "adminpanel/subscriptions/list.html", {
        "page_obj": page_obj,
        "status": status,
        "search": search if search else "",
    })


@staff_member_required
def admin_transaction_detail(request, pk):
    transaction = get_object_or_404(
        Transaction.objects.select_related("order", "order__user"),
        pk=pk
    )

    return render(request, "adminpanel/transactions/detail.html", {
        "transaction": transaction
    })


from django.core.paginator import Paginator
from django.db.models import Q
from pricing.models import Transaction


@staff_member_required
def admin_transaction_list(request):
    transactions = Transaction.objects.select_related(
        "order", "order__user"
    ).order_by("-created_at")

    # Filters
    status = request.GET.get("status")
    if status:
        transactions = transactions.filter(status=status)

    search = request.GET.get("search")
    if search:
        transactions = transactions.filter(
            Q(reference__icontains=search) |
            Q(order__payment_reference__icontains=search) |
            Q(order__id__icontains=search) |
            Q(order__user__email__icontains=search)
        )

    paginator = Paginator(transactions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "adminpanel/transactions/list.html", {
        "page_obj": page_obj,
        "status": status,
        "search": search if search else "",
    })




from pricing.helper import create_subscription_from_order
from django.db import transaction


@staff_member_required
def admin_mark_order_paid(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.status in ["paid", "cancelled"]:
        messages.warning(request, "This order cannot be modified.")
        return redirect("admin_order_detail", pk=pk)

    with transaction.atomic():
        order.status = "paid"
        order.save(update_fields=["status"])

        subscription = create_subscription_from_order(order.id)

    log_admin_action(request.user, order, "Marked Order as Paid")

    messages.success(
        request,
        f"Order marked as PAID. Subscription created (ID: {subscription.id})."
    )

    return redirect("admin_order_detail", pk=pk)


from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from pricing.models import Order

@staff_member_required
def admin_cancel_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.status in ["paid", "cancelled"]:
        messages.warning(request, "This order cannot be cancelled.")
        return redirect("admin_order_detail", pk=pk)

    order.status = "cancelled"
    order.save(update_fields=["status"])

    log_admin_action(request.user, order, "Cancelled Order")
    messages.success(request, "Order cancelled successfully.")
    return redirect("admin_order_detail", pk=pk)


@staff_member_required
def admin_fail_order(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if order.status in ["paid", "cancelled"]:
        messages.warning(request, "This order cannot be modified.")
        return redirect("admin_order_detail", pk=pk)

    order.status = "failed"
    order.save(update_fields=["status"])

    log_admin_action(request.user, order, "Marked Order as Failed")

    messages.success(request, "Order marked as FAILED.")
    return redirect("admin_order_detail", pk=pk)


from django.shortcuts import get_object_or_404
from pricing.models import Subscription

def admin_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    subscription = Subscription.objects.filter(order=order).first()

    context = {
        "order": order,
        "subscription": subscription,
    }
    return render(request, "adminpanel/orders/detail.html", context)


from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from pricing.models import Order

def admin_order_list(request):
    orders = Order.objects.select_related("user", "plan").order_by("-created_at")

    # Filters
    status = request.GET.get("status")
    billing_cycle = request.GET.get("billing_cycle")
    search = request.GET.get("search")

    if status:
        orders = orders.filter(status=status)

    if billing_cycle:
        orders = orders.filter(billing_cycle=billing_cycle)

    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(payment_reference__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) 
        )

    paginator = Paginator(orders, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "status": status,
        "billing_cycle": billing_cycle,
        "search": search if search else "",
    }
    return render(request, "adminpanel/orders/list.html", context)


from django.views.generic import DetailView
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from pricing.models import Plan, PlanFeature
from ..forms import AdminPlanFeatureForm


class AdminPlanDetailView(DetailView):
    model = Plan
    template_name = "adminpanel/pricing_management/detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return Plan.objects.prefetch_related("features")
    from ..forms import AdminPlanFeatureForm

class AdminPlanDetailView(DetailView):
    model = Plan
    template_name = "adminpanel/pricing_management/detail.html"
    context_object_name = "plan"

    def get_queryset(self):
        return Plan.objects.prefetch_related("features")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["feature_form"] = AdminPlanFeatureForm()
        return context
    
class AdminPlanFeatureCreateView(View):
    def post(self, request, plan_id):
        plan = get_object_or_404(Plan, id=plan_id)
        form = AdminPlanFeatureForm(request.POST)

        if form.is_valid():
            feature = form.save(commit=False)
            feature.plan = plan
            feature.save()

        log_admin_action(request.user, plan, "Added Feature")

        return redirect("admin-pricing-detail", pk=plan.id)

class AdminPlanFeatureUpdateView(View):
    def post(self, request, feature_id):
        feature = get_object_or_404(PlanFeature, id=feature_id)
        form = AdminPlanFeatureForm(request.POST, instance=feature)

        if form.is_valid():
            form.save()

        log_admin_action(request.user, feature.plan, f"Updated {feature}")
        return redirect("admin-pricing-detail", pk=feature.plan.id)

class AdminPlanFeatureDeleteView(View):
    def post(self, request, feature_id):
        feature = get_object_or_404(PlanFeature, id=feature_id)
        plan_id = feature.plan.id
        feature.delete()

        log_admin_action(request.user, feature.plan, f"Deleted {feature}")
        return redirect("admin-pricing-detail", pk=plan_id)

# admin_panel/views.py

from django.views.generic import UpdateView
from django.urls import reverse
from pricing.models import Plan
from ..forms import AdminPlanForm


class AdminPlanEditView(UpdateView):
    model = Plan
    form_class = AdminPlanForm
    template_name = "adminpanel/pricing_management/edit.html"

    def form_valid(self, form):
        plan = form.save()
        log_admin_action(self.request.user, plan, f"Updated {plan}")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin-pricing-detail", kwargs={"pk": self.object.id})


from django.views.generic import CreateView
from django.urls import reverse_lazy
from pricing.models import Plan
from ..forms import AdminPlanForm

class AdminPlanCreateView(CreateView):
    model = Plan
    form_class = AdminPlanForm
    template_name = "adminpanel/pricing_management/create.html"
    success_url = reverse_lazy("admin-pricing-detail")

    def form_valid(self, form):
        plan = form.save()
        log_admin_action(self.request.user, plan, f"Created {plan}")
        return super().form_valid(form)




# admin_panel/views.py
from django.views.generic import ListView
from django.db.models import Count
from pricing.models import Plan

class AdminPlanListView(ListView):
    model = Plan
    template_name = "adminpanel/pricing_management/list.html"
    context_object_name = "plans"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Plan.objects
            .annotate(feature_count=Count("features"))
            .order_by("user_type", "name")
        )

        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(name__icontains=q)

        user_type = self.request.GET.get("user_type")
        if user_type:
            queryset = queryset.filter(user_type=user_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_types"] = Plan.USER_TYPES
        context["current_q"] = self.request.GET.get("q", "")
        context["current_user_type"] = self.request.GET.get("user_type", "")
        return context



from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from ..decorators import admin_required

@method_decorator(admin_required, name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = "adminpanel/user_management/dashboard.html"


from django.views.generic import ListView
from django.db.models import Q
from django.contrib.auth import get_user_model

User = get_user_model()

class UserListView(ListView):
    model = User
    template_name = 'adminpanel/user_management/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = User.objects.select_related('user_profile').all()

        search_query = self.request.GET.get('search', '')
        role_filter = self.request.GET.get('role', '')

        if search_query:
            queryset = queryset.filter(
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )

        if role_filter:
            queryset = queryset.filter(role=role_filter)

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search'] = self.request.GET.get('search', '')
        ctx['selected_role'] = self.request.GET.get('role', '')
        ctx['roles'] = ['freelancer', 'employer', 'admin']
        return ctx


from django.views.generic import DetailView, UpdateView
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden

User = get_user_model()


class UserDetailView(DetailView):
    model = User
    template_name = "adminpanel/user_management/user_detail.html"
    context_object_name = "user_obj"


class UserUpdateView(UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'role', 'is_active']
    template_name = "adminpanel/user_management/user_edit.html"
    success_url = reverse_lazy("admin-user-list")

    # log admin action
    def form_valid(self, form):
        user = form.save()
        log_admin_action(self.request.user, user, f"Updated {user}")
        return super().form_valid(form)


from ..utils.base_utils import log_admin_action
from django.contrib import messages
from django.utils import timezone


def suspend_user(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    user = get_object_or_404(User, pk=pk)
    days = int(request.POST.get("days", 7))  # default 7 days
    reason = request.POST.get("reason", "")

    user.suspend(days=days, reason=reason)
    log_admin_action(request.user, user, "Suspended Account", reason)

    messages.success(request, f"{user.email} suspended successfully.")
    return redirect("admin_user_detail", user_id=pk)


def unsuspend_user(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    user = get_object_or_404(User, pk=pk)
    user.unsuspend()
    log_admin_action(request.user, user, "Unsuspended Account")

    messages.success(request, f"{user.email} unsuspended.")
    return redirect("admin_user_detail", user_id=pk)


def ban_user(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    user = get_object_or_404(User, pk=pk)
    reason = request.POST.get("reason", "")

    user.ban(reason=reason)
    log_admin_action(request.user, user, "Banned Account", reason)

    messages.success(request, f"{user.email} banned!")
    return redirect("admin_user_detail", user_id=pk)


def unban_user(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("Unauthorized")

    user = get_object_or_404(User, pk=pk)
    user.unban()
    log_admin_action(request.user, user, "Unbanned Account")

    messages.success(request, f"{user.email} unbanned!")
    return redirect("admin_user_detail", user_id=pk)

from ..models import AdminActionLog
from django.db.models import Q
from django.core.paginator import Paginator

def admin_action_logs(request):
    query = request.GET.get("q", "")

    logs = AdminActionLog.objects.all().select_related("admin", "target_user")

    if query:
        logs = logs.filter(
            Q(action__icontains=query) |
            Q(admin__email__icontains=query) |
            Q(target_user__email__icontains=query)
        )

    paginator = Paginator(logs, 20)
    logs_page = paginator.get_page(request.GET.get("page"))

    context = {
        "logs": logs_page,
        "search_query": query
    }
    return render(request, "adminpanel/admin/logs.html", context)

def user_activity_logs(request):
    query = request.GET.get("q", "")

    logs = UserActivityLog.objects.all().select_related("user")

    if query:
        logs = logs.filter(
            Q(action__icontains=query) |
            Q(user__email__icontains=query)
        )

    paginator = Paginator(logs, 20)
    logs_page = paginator.get_page(request.GET.get("page"))

    context = {
        "logs": logs_page,
        "search_query": query
    }
    return render(request, "adminpanel/admin/user-activity-log.html", context)








# ------------------
# BUSOLA
# ------------------


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ManageJobsTasks.models import Job # Import your actual Job model
from company.models import Company

@login_required
def manage_jobs(request):
    # 1. Get the status from URL, default to 'pending'
    status_filter = request.GET.get('status', 'pending')
    
    # 2. Filter jobs based on the status
    # Assuming your model field is named 'status' and values are lowercase
    jobs = (
    Job.objects
    .select_related('user')
    .filter(status=status_filter)
    .order_by('-created_at')
)

    # company = Company.objects.select_related('created_by')

    # company_map = {
    #     com.created_by_id: com
    #     for com in company
    # }

    job_list = []
    for job in jobs:
        print(job.user.creator.first().logo.url)
        job_list.append({
            'job': job,
            'company': job.user.creator.first()
        })

    print(job_list)
    context = {
        'job_list': job_list,
        'current_status': status_filter,
    }
    return render(request, 'adminpanel/job_management/manage_job.html', context)

@login_required
def change_job_status(request, job_id, action):
    # This replaces your API endpoint
    job = get_object_or_404(Job, id=job_id)
    
    if action == 'approve':
        job.status = 'approved'
        messages.success(request, f"Job '{job.title}' has been approved.")
    elif action == 'reject':
        job.status = 'rejected'
        messages.warning(request, f"Job '{job.title}' has been rejected.")
        
    job.save()
    
    # Redirect back to the page the user was on (preserving the tab they were on)
    previous_status = request.GET.get('from_status', 'pending')
    return redirect(f'/site-admin/admin-jobs/?status={previous_status}')