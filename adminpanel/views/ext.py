from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from users.models import CustomUser, UserActivityLog


@staff_member_required
def admin_user_list(request):
    users = CustomUser.objects.select_related().order_by("-date_joined")

    # --------------------
    # Filters
    # --------------------
    role = request.GET.get("role")
    if role:
        users = users.filter(role=role)

    account_status = request.GET.get("account_status")
    if account_status:
        users = users.filter(account_status=account_status)

    is_active = request.GET.get("is_active")
    if is_active in ["true", "false"]:
        users = users.filter(is_active=(is_active == "true"))

    verified = request.GET.get("verified")
    if verified in ["true", "false"]:
        users = users.filter(user_profile__verified=(verified == "true"))

    # --------------------
    # Search
    # --------------------
    search = request.GET.get("search")
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "adminpanel/users/list.html", {
        "page_obj": page_obj,
        "search": search if search else "",
        "role": role,
        "account_status": account_status,
        "is_active": is_active,
        "verified": verified,
    })

from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST

from users.models import CustomUser
from pricing.models import Subscription, Order, Transaction


@staff_member_required
def admin_user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    subscription = Subscription.objects.filter(
        user=user,
        is_active=True
    ).select_related("plan").first()

    recent_orders = Order.objects.filter(
        user=user
    ).select_related("plan").order_by("-created_at")[:5]

    user_recent_activities = UserActivityLog.objects.filter(user=user).order_by("-created_at")[:10]

    return render(request, "adminpanel/users/detail.html", {
        "user_obj": user,
        "subscription": subscription,
        "recent_orders": recent_orders,
        "user_recent_activities": user_recent_activities,
    })


@staff_member_required
@require_POST
def admin_user_delete(request, user_id):
    """Permanently delete a (non-admin) user account.

    Guards: you can't delete yourself, and admin/staff/superuser accounts are
    protected here (manage those from the Admins page). The deletion is logged
    with the email in the details, because the AdminActionLog target FK cascades
    away with the user.
    """
    from adminpanel.utils.base_utils import log_admin_action

    target = get_object_or_404(CustomUser, id=user_id)

    if target.id == request.user.id:
        messages.error(request, "You cannot delete your own account.")
        return redirect("admin_user_detail", user_id=user_id)

    if target.is_staff or target.is_superuser or target.role == "admin":
        messages.error(request, "Admin accounts can't be deleted from here.")
        return redirect("admin_user_detail", user_id=user_id)

    info = f"Deleted user {target.email} (id {target.id}, role {target.role})."
    target.delete()
    log_admin_action(request.user, None, "user_delete", info)
    messages.success(request, f"User {target.email} has been permanently deleted.")
    return redirect("admin_user_list")


from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from users.models import CustomUser


@staff_member_required
def admin_user_billing_history(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    status = request.GET.get("status")
    q = request.GET.get("q")

    orders = Order.objects.filter(user=user).select_related(
        "pricing_plan"
    ).order_by("-created_at")

    transactions = Transaction.objects.filter(
        user=user
    ).order_by("-created_at")

    if status:
        orders = orders.filter(status=status)
        transactions = transactions.filter(status=status)

    if q:
        orders = orders.filter(
            Q(reference__icontains=q) |
            Q(pricing_plan__name__icontains=q)
        )

    paginator = Paginator(orders, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "adminpanel/users/billing_history.html", {
        "user_obj": user,
        "orders": page_obj,
        "transactions": transactions[:10],  # recent tx snapshot
        "status": status,
        "q": q,
    })
