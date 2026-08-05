from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from adminpanel.utils.base_utils import log_admin_action

User = get_user_model()


@staff_member_required
def admin_admin_list(request):
    """List existing admin accounts + a form to create new ones.

    Managing admin accounts is restricted to superusers — a regular staff
    admin can use the panel but cannot mint new admins.
    """
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can manage admin accounts.")
        return redirect("admin-dashboard")

    admins = User.objects.filter(
        Q(role="admin") | Q(is_staff=True) | Q(is_superuser=True)
    ).order_by("-date_joined")

    return render(request, "adminpanel/admin_management/list.html", {"admins": admins})


@staff_member_required
@require_POST
def admin_admin_create(request):
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can create admin accounts.")
        return redirect("admin-dashboard")

    email = (request.POST.get("email") or "").strip().lower()
    first_name = (request.POST.get("first_name") or "").strip()
    last_name = (request.POST.get("last_name") or "").strip()
    password = request.POST.get("password") or ""
    make_superuser = request.POST.get("is_superuser") == "on"

    # --- Validation ---
    if not email or not password:
        messages.error(request, "Email and password are required.")
        return redirect("admin_admin_list")
    if len(password) < 8:
        messages.error(request, "Password must be at least 8 characters.")
        return redirect("admin_admin_list")
    if User.objects.filter(email__iexact=email).exists():
        messages.error(request, f"A user with the email {email} already exists.")
        return redirect("admin_admin_list")

    # --- Create the admin ---
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role="admin",
        is_staff=True,
        is_active=True,
        is_superuser=make_superuser,
        verified_email=True,
        account_status="active",
        onboarding_completed=True,
    )

    log_admin_action(
        request.user, user, "admin_create",
        f"Created {'superadmin' if make_superuser else 'admin'} account {email}.",
    )
    messages.success(request, f"Admin account created for {email}.")
    return redirect("admin_admin_list")
