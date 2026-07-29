from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone

from company.models import Company, VERIFIABLE_FIELDS
from adminpanel.forms import AdminCompanyForm
from adminpanel.utils.base_utils import log_admin_action


@staff_member_required
def admin_company_list(request):
    companies = Company.objects.select_related("created_by").order_by("-created_at")

    q = request.GET.get("q")
    if q:
        companies = companies.filter(
            Q(company_name__icontains=q)
            | Q(brand_name__icontains=q)
            | Q(created_by__email__icontains=q)
        )

    paginator = Paginator(companies, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "adminpanel/company_management/list.html",
        {"page_obj": page_obj, "q": q or ""},
    )


@staff_member_required
def admin_company_create(request):
    if request.method == "POST":
        form = AdminCompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            log_admin_action(
                request.user,
                company.created_by,
                "create_company",
                f"Created company '{company.company_name}' (id {company.id}).",
            )
            messages.success(request, f"Company '{company.company_name}' created.")
            return redirect("admin_company_list")
        messages.error(request, "Please correct the errors below.")
    else:
        form = AdminCompanyForm()

    return render(
        request,
        "adminpanel/company_management/create.html",
        {"form": form},
    )


def _build_field_rows(company):
    """One display row per verifiable field, carrying its current review state."""
    rows = []
    for name, label in VERIFIABLE_FIELDS:
        rows.append({
            "name": name,
            "label": label,
            "value": getattr(company, name),
            "status": company.get_field_status(name),
            "note": company.get_field_note(name),
            "is_file": name in ("logo", "documents"),
        })
    return rows


@staff_member_required
def admin_company_detail(request, pk):
    company = get_object_or_404(Company.objects.select_related("created_by"), pk=pk)
    return render(
        request,
        "adminpanel/company_management/detail.html",
        {"company": company, "fields": _build_field_rows(company)},
    )


@staff_member_required
def admin_review_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method != "POST":
        return redirect("admin_company_detail", pk=pk)

    reviews = {}
    for name, _label in VERIFIABLE_FIELDS:
        status = request.POST.get(f"status_{name}", "pending")
        if status not in ("pending", "approved", "rejected"):
            status = "pending"
        reviews[name] = {
            "status": status,
            "note": (request.POST.get(f"note_{name}") or "").strip(),
        }

    company.field_reviews = reviews
    company.reviewed_at = timezone.now()
    company.reviewed_by = request.user
    company.recompute_verification()
    company.save()

    rejected = [
        (label, reviews[name]["note"])
        for name, label in VERIFIABLE_FIELDS
        if reviews[name]["status"] == "rejected"
    ]

    log_admin_action(
        request.user,
        company.created_by,
        "review_company",
        f"Reviewed '{company.company_name}' (id {company.id}); "
        f"status={company.verification_status}, {len(rejected)} field(s) rejected.",
    )

    if company.verification_status == "rejected" and rejected:
        _email_rejected_fields(request, company, rejected)
        messages.success(
            request,
            f"Saved. {len(rejected)} field(s) flagged; employer notified.",
        )
    elif company.verification_status == "approved":
        messages.success(request, f"'{company.company_name}' fully verified.")
    else:
        messages.success(request, "Review saved.")
    return redirect("admin_company_list")


def _email_rejected_fields(request, company, rejected):
    owner = company.created_by
    if not (owner and owner.email):
        return
    # Build the link from the current host so it points at the same environment
    # the admin is reviewing on (local in dev, real domain in production).
    edit_url = request.build_absolute_uri(reverse("company_edit_resubmit"))
    lines = "\n".join(
        f"- {label}: {note or 'needs correction'}" for label, note in rejected
    )
    send_mail(
        subject="Your company submission needs corrections",
        message=(
            f"Hello,\n\nSome details for '{company.company_name}' could not be verified:\n\n"
            f"{lines}\n\nPlease correct these and resubmit here:\n{edit_url}\n\n"
            f"Thank you,\nOne Million Jobs"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[owner.email],
        fail_silently=False,
    )
