from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import redirect, render

from admins.models import AdminProfile
from adminpanel.forms import AdminContactForm
from adminpanel.utils.base_utils import log_admin_action


@staff_member_required
def admin_contact_settings(request):
    """Edit the single site-wide contact profile shown on the public contact page.

    AdminProfile is treated as a singleton: we always edit the first row (creating
    one on first save) so the public contact page has a single source of truth.
    """
    profile = AdminProfile.objects.first()

    if request.method == "POST":
        form = AdminContactForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            log_admin_action(
                request.user,
                None,
                "update_contact_settings",
                "Updated site contact / social details.",
            )
            messages.success(request, "Contact details saved.")
            return redirect("admin_contact_settings")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AdminContactForm(instance=profile)

    return render(
        request,
        "adminpanel/settings/contact.html",
        {"form": form, "profile": profile},
    )
