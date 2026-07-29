import random
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

from ManageJobsTasks.models import (
    Job,
    Task,
    JOB_TYPES,
    JOB_CATEGORIES,
    JOB_STATUS,
    TASK_CATEGORIES,
    PROJECT_TYPES,
    TASK_STATUS,
)
from company.models import Company
from users.models import UserProfile, Skill, Category
from users.management.commands.seed_freelancers import (
    NIGERIAN_FIRST_NAMES,
    NIGERIAN_LAST_NAMES,
    NIGERIAN_CITIES,
    PROFESSIONAL_ROLES,
    TAGLINES,
    fake,
)
from adminpanel.utils.base_utils import log_admin_action

User = get_user_model()


def _lines(raw):
    """Split a textarea into a list of non-empty, stripped lines."""
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _decimal_or_none(raw):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def _int_or(raw, default):
    raw = (raw or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _float_or(raw, default):
    raw = (raw or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


@staff_member_required
def bulk_add(request):
    """
    Dev utility: bulk-create Jobs (linked to a Company) and Tasks (linked to an
    employer) in one place. Each line in the title/name textarea becomes one
    record; the surrounding fields are applied to every record in the batch.
    """
    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == "job":
            _handle_bulk_jobs(request)
        elif form_type == "task":
            _handle_bulk_tasks(request)
        else:
            messages.error(request, "Unknown form submission.")

        return redirect("admin_bulk_add")

    context = {
        "companies": Company.objects.select_related("created_by", "members").order_by("company_name"),
        "employers": User.objects.filter(role="employer").order_by("email"),
        "job_types": JOB_TYPES,
        "job_categories": JOB_CATEGORIES,
        "job_statuses": JOB_STATUS,
        "task_categories": TASK_CATEGORIES,
        "project_types": PROJECT_TYPES,
        "task_statuses": TASK_STATUS,
    }
    return render(request, "adminpanel/dev/bulk_add.html", context)


def _handle_bulk_jobs(request):
    company_id = request.POST.get("company")
    titles = _lines(request.POST.get("titles"))
    job_type = request.POST.get("job_type")
    category = request.POST.get("category")
    location = (request.POST.get("location") or "").strip()
    description = (request.POST.get("description") or "").strip()
    status = request.POST.get("status") or "pending"

    company = Company.objects.filter(pk=company_id).first()
    if not company:
        messages.error(request, "Please select a valid company.")
        return

    # A Job is owned by a user; link it to the company via that company's owner.
    owner = company.created_by or company.members
    if not owner:
        messages.error(
            request,
            f"'{company.company_name}' has no linked user (created_by/members), so jobs can't be attached to it.",
        )
        return

    missing = [
        label
        for value, label in [
            (titles, "job titles"),
            (job_type, "job type"),
            (category, "category"),
            (location, "location"),
            (description, "description"),
        ]
        if not value
    ]
    if missing:
        messages.error(request, "Missing required field(s): " + ", ".join(missing) + ".")
        return

    country = (request.POST.get("country") or "").strip() or None
    city = (request.POST.get("city") or "").strip() or None
    tags = (request.POST.get("tags") or "").strip()
    salary_min = _decimal_or_none(request.POST.get("salary_min"))
    salary_max = _decimal_or_none(request.POST.get("salary_max"))
    approved = request.POST.get("approved") == "on"
    is_featured = request.POST.get("is_featured") == "on"

    created = 0
    for title in titles:
        Job.objects.create(
            user=owner,
            title=title,
            job_type=job_type,
            category=category,
            location=location,
            description=description,
            status=status,
            country=country,
            city=city,
            tags=tags,
            salary_min=salary_min,
            salary_max=salary_max,
            approved=approved,
            is_featured=is_featured,
        )
        created += 1

    log_admin_action(
        request.user,
        owner,
        "bulk_create_jobs",
        f"Created {created} job(s) for company '{company.company_name}' (owner {owner.email}).",
    )
    messages.success(
        request,
        f"Created {created} job(s) linked to '{company.company_name}'.",
    )


def _handle_bulk_tasks(request):
    employer_id = request.POST.get("employer")
    names = _lines(request.POST.get("project_names"))
    category = request.POST.get("category")
    project_type = request.POST.get("project_type")
    skills = (request.POST.get("skills") or "").strip()
    description = (request.POST.get("description") or "").strip()
    status = request.POST.get("status") or "draft"
    budget_min = _decimal_or_none(request.POST.get("budget_min"))
    budget_max = _decimal_or_none(request.POST.get("budget_max"))

    employer = User.objects.filter(pk=employer_id, role="employer").first()
    if not employer:
        messages.error(request, "Please select a valid employer.")
        return

    missing = [
        label
        for value, label in [
            (names, "project names"),
            (category, "category"),
            (project_type, "project type"),
            (skills, "required skills"),
            (budget_min, "minimum budget"),
            (budget_max, "maximum budget"),
        ]
        if value in (None, "", [])
    ]
    if missing:
        messages.error(request, "Missing required field(s): " + ", ".join(missing) + ".")
        return

    location = (request.POST.get("location") or "").strip() or None
    is_featured = request.POST.get("is_featured") == "on"

    created = 0
    for name in names:
        Task.objects.create(
            user=employer,
            project_name=name,
            category=category,
            project_type=project_type,
            skills=skills,
            description=description or "A task",
            status=status,
            budget_min=budget_min,
            budget_max=budget_max,
            location=location,
            is_featured=is_featured,
        )
        created += 1

    log_admin_action(
        request.user,
        employer,
        "bulk_create_tasks",
        f"Created {created} task(s) for employer {employer.email}.",
    )
    messages.success(
        request,
        f"Created {created} task(s) linked to {employer.email}.",
    )


# ---------------------------------------------------------------------------
# Bulk freelancers (so the "Highest Rated Freelancers" section has data to show)
# ---------------------------------------------------------------------------

DEFAULT_FREELANCER_SKILLS = [
    "Python", "Django", "JavaScript", "React", "Node.js", "PHP", "Laravel",
    "Graphic Design", "UI/UX Design", "Figma", "Photoshop", "Illustrator",
    "Copywriting", "SEO", "Content Writing", "Digital Marketing", "Sales",
    "Data Analysis", "Excel", "Power BI", "Bookkeeping", "Accounting",
    "Customer Service", "Translation", "Project Management", "WordPress",
    "Mobile Development", "Flutter", "Android", "iOS",
]


def _ensure_skills():
    existing = {s.name.lower(): s for s in Skill.objects.all()}
    for name in DEFAULT_FREELANCER_SKILLS:
        if name.lower() not in existing:
            existing[name.lower()] = Skill.objects.create(name=name)
    return list(existing.values())


@staff_member_required
def bulk_add_freelancers(request):
    """
    Dev utility: bulk-create top-rated freelancer accounts so the public
    "Highest Rated Freelancers" carousel (fed by /api/users/profiles/ ordered
    by -rating) has something to display. Each created user gets a freelancer
    role and a UserProfile with a high rating within the chosen range.
    """
    if request.method == "POST":
        _handle_bulk_freelancers(request)
        return redirect("admin_bulk_add_freelancers")

    context = {
        "freelancer_count": User.objects.filter(role="freelancer").count(),
        "categories": Category.objects.order_by("name"),
    }
    return render(request, "adminpanel/dev/bulk_freelancers.html", context)


def _handle_bulk_freelancers(request):
    count = _int_or(request.POST.get("count"), 10)
    if count < 1:
        messages.error(request, "Count must be at least 1.")
        return
    count = min(count, 200)  # safety cap for a test utility

    password = (request.POST.get("password") or "").strip() or "password123"

    rating_min = max(0.0, min(5.0, _float_or(request.POST.get("rating_min"), 4.5)))
    rating_max = max(0.0, min(5.0, _float_or(request.POST.get("rating_max"), 5.0)))
    if rating_min > rating_max:
        rating_min, rating_max = rating_max, rating_min

    success_min = max(0, min(100, _int_or(request.POST.get("job_success_min"), 85)))
    success_max = max(0, min(100, _int_or(request.POST.get("job_success_max"), 100)))
    if success_min > success_max:
        success_min, success_max = success_max, success_min

    rate_min = _int_or(request.POST.get("hourly_rate_min"), 5000)
    rate_max = _int_or(request.POST.get("hourly_rate_max"), 25000)
    if rate_min > rate_max:
        rate_min, rate_max = rate_max, rate_min

    votes_min = max(0, _int_or(request.POST.get("rating_count_min"), 10))
    votes_max = max(0, _int_or(request.POST.get("rating_count_max"), 80))
    if votes_min > votes_max:
        votes_min, votes_max = votes_max, votes_min

    verified = request.POST.get("verified") == "on"
    kyc_verified = request.POST.get("kyc_verified") == "on"
    attach_skills = request.POST.get("attach_skills") == "on"

    category_id = request.POST.get("category")
    fixed_category = Category.objects.filter(pk=category_id).first() if category_id else None

    skills = _ensure_skills() if attach_skills else []
    categories = list(Category.objects.all())

    created = 0
    attempts = 0
    # Allow a few retries per record in case of random email collisions.
    while created < count and attempts < count * 5:
        attempts += 1
        first_name = random.choice(NIGERIAN_FIRST_NAMES)
        last_name = random.choice(NIGERIAN_LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99999)}@example.com"

        if User.objects.filter(email__iexact=email).exists():
            continue

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="freelancer",
            is_active=True,
            verified_email=True,
            account_status="active",
        )

        role = random.choice(PROFESSIONAL_ROLES)
        city = random.choice(NIGERIAN_CITIES)
        tagline = random.choice(TAGLINES).format(role=role, city=city)
        rating = round(random.uniform(rating_min, rating_max), 1)
        category = fixed_category or (random.choice(categories) if categories else None)

        # The post_save signal already created a UserProfile; update it.
        profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "bio": fake.paragraph(nb_sentences=4),
                "tagline": tagline,
                "category": category,
                "hourly_rate": Decimal(random.randint(rate_min, rate_max)),
                "nationality": "Nigeria",
                "status": "active",
                "job_success": random.randint(success_min, success_max),
                "rating": rating,
                "avg_rating": rating,
                "rating_count": random.randint(votes_min, votes_max),
                "kyc_verified": kyc_verified,
                "verified": verified,
            },
        )
        if skills:
            profile.skills.set(random.sample(skills, k=min(5, max(3, random.randint(3, 5)))))

        created += 1

    if not created:
        messages.error(request, "No freelancers were created (email collisions). Try again.")
        return

    log_admin_action(
        request.user,
        request.user,
        "bulk_create_freelancers",
        f"Created {created} top-rated freelancer(s) "
        f"(rating {rating_min}-{rating_max}). Password: '{password}'.",
    )
    messages.success(
        request,
        f"Created {created} freelancer(s) with ratings between {rating_min} and {rating_max}. "
        f"Login password for all: '{password}'.",
    )
