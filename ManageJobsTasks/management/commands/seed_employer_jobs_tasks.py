from decimal import Decimal
import random

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from faker import Faker

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

User = get_user_model()

NIGERIAN_CITIES = [
    "Lagos", "Abuja", "Port Harcourt", "Ibadan", "Kano", "Benin City",
    "Kaduna", "Enugu", "Jos", "Calabar", "Uyo", "Owerri", "Abeokuta",
    "Warri", "Onitsha", "Aba", "Ilorin", "Akure", "Asaba", "Sokoto",
]

NIGERIAN_AREAS = [
    "Victoria Island, Lagos", "Lekki Phase 1, Lagos", "Ikeja GRA, Lagos",
    "Yaba, Lagos", "Surulere, Lagos", "Wuse 2, Abuja", "Maitama, Abuja",
    "Garki, Abuja", "Asokoro, Abuja", "GRA Phase 2, Port Harcourt",
    "Bodija, Ibadan", "Nassarawa GRA, Kano", "Independence Layout, Enugu",
]


class Command(BaseCommand):
    help = (
        "Create Jobs and Tasks for an existing employer account, linked to the "
        "employer's company. Pass the employer's email with --email."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email of the existing employer account",
        )
        parser.add_argument(
            "--jobs",
            type=int,
            default=5,
            help="Number of jobs to create (default: 5)",
        )
        parser.add_argument(
            "--tasks",
            type=int,
            default=5,
            help="Number of tasks to create (default: 5)",
        )
        parser.add_argument(
            "--company-id",
            type=int,
            default=None,
            help="Specific company id to use (must belong to the employer). "
                 "If omitted, the employer's first company is used.",
        )

    def handle(self, *args, **options):
        fake = Faker()
        email = options["email"].strip().lower()
        jobs_count = options["jobs"]
        tasks_count = options["tasks"]
        company_id = options["company_id"]

        try:
            employer = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise CommandError(f"No user found with email '{email}'.")

        if employer.role != "employer":
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  User '{employer.email}' has role '{employer.role}', not 'employer'. "
                    "Proceeding anyway."
                )
            )

        company_qs = Company.objects.filter(created_by=employer)
        if company_id is not None:
            company = company_qs.filter(id=company_id).first()
            if company is None:
                raise CommandError(
                    f"Company id {company_id} not found for employer '{employer.email}'."
                )
        else:
            company = company_qs.order_by("id").first()
            if company is None:
                raise CommandError(
                    f"Employer '{employer.email}' has no company. Create one first, "
                    "or pass --company-id."
                )

        self.stdout.write(
            self.style.NOTICE(
                f"🚀 Seeding for employer '{employer.email}' / company "
                f"'{company.company_name}' (id={company.id})"
            )
        )

        created_jobs = []
        for _ in range(jobs_count):
            # Nigerian salary ranges in Naira (monthly)
            salary_min = Decimal(random.randint(150_000, 500_000))
            salary_max = salary_min + Decimal(random.randint(100_000, 1_500_000))
            city = random.choice(NIGERIAN_CITIES)
            job = Job.objects.create(
                user=employer,
                title=fake.job(),
                job_type=random.choice([jt[0] for jt in JOB_TYPES]),
                category=random.choice([jc[0] for jc in JOB_CATEGORIES]),
                country="Nigeria",
                location=company.headquarters_address or random.choice(NIGERIAN_AREAS),
                city=city,
                status=random.choice([js[0] for js in JOB_STATUS]),
                salary_min=salary_min,
                salary_max=salary_max,
                tags=", ".join(fake.words(nb=5)),
                description=fake.text(max_nb_chars=400),
                expiration_date=timezone.now() + timezone.timedelta(days=random.randint(15, 60)),
                is_active=True,
                approved=True,
                is_featured=random.choice([True, False]),
            )
            created_jobs.append(job)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(created_jobs)} Jobs for {employer.email}")
        )

        created_tasks = []
        for _ in range(tasks_count):
            # Nigerian budgets in Naira
            budget_min = Decimal(random.randint(50_000, 250_000))
            budget_max = budget_min + Decimal(random.randint(50_000, 750_000))
            task = Task.objects.create(
                user=employer,
                project_name=fake.catch_phrase(),
                category=random.choice([tc[0] for tc in TASK_CATEGORIES]),
                location=company.headquarters_address or random.choice(NIGERIAN_AREAS),
                budget_min=budget_min,
                budget_max=budget_max,
                project_type=random.choice([pt[0] for pt in PROJECT_TYPES]),
                skills=", ".join(fake.words(nb=5)),
                status=random.choice([ts[0] for ts in TASK_STATUS]),
                description=fake.text(max_nb_chars=400),
                expiration_date=timezone.now() + timezone.timedelta(days=random.randint(15, 60)),
                is_featured=random.choice([True, False]),
            )
            created_tasks.append(task)

        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {len(created_tasks)} Tasks for {employer.email}")
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"🎉 Done. Employer '{employer.email}' / company "
                f"'{company.company_name}' now has "
                f"{len(created_jobs)} new jobs and {len(created_tasks)} new tasks."
            )
        )
