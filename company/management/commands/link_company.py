from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

from company.models import COMPANY_INDUSTRIES, Company


INDUSTRY_CHOICES = [key for key, _ in COMPANY_INDUSTRIES]

UNIQUE_OPTIONAL_FIELDS = ("email", "website", "facebook", "linkedin")


class Command(BaseCommand):
    help = "Create a Company and link it to an existing employer user account."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True,
                            help="Email of the existing employer user.")
        parser.add_argument("--company-name", required=True,
                            help="Company name.")
        parser.add_argument("--industry", required=True, choices=INDUSTRY_CHOICES,
                            help="Industry key (one of COMPANY_INDUSTRIES).")
        parser.add_argument("--description", required=True,
                            help="Company description.")

        parser.add_argument("--brand-name", default=None)
        parser.add_argument("--registration-number", default=None)
        parser.add_argument("--tin", default=None)
        parser.add_argument("--established-date", default=None,
                            help="ISO format, e.g. 2020-01-15 or 2020-01-15T00:00:00.")
        parser.add_argument("--company-size", default=None,
                            help="e.g. '1-10', '11-50', '51-200', '201-500', '500+'")
        parser.add_argument("--headquarters-address", default=None)
        parser.add_argument("--primary-phone", default=None)
        parser.add_argument("--secondary-phone", default=None)
        parser.add_argument("--company-email", default=None,
                            help="Company contact email (unique).")
        parser.add_argument("--website", default=None, help="Unique.")
        parser.add_argument("--facebook", default=None, help="Unique.")
        parser.add_argument("--linkedin", default=None, help="Unique.")
        parser.add_argument("--country", default=None)

        parser.add_argument("--force", action="store_true",
                            help="Create another company even if this employer already has one.")

    def handle(self, *args, **options):
        user_model = get_user_model()
        email = options["email"]

        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist:
            raise CommandError(f"No user found with email '{email}'.")

        role = getattr(user, "role", None)
        if role != "employer":
            raise CommandError(
                f"User '{email}' has role '{role}', expected 'employer'."
            )

        if not options["force"] and Company.objects.filter(created_by=user).exists():
            existing = Company.objects.filter(created_by=user).first()
            raise CommandError(
                f"User '{email}' already has a company: "
                f"'{existing.company_name}' (id={existing.id}). "
                "Pass --force to create another."
            )

        field_map = {
            "company_name": options["company_name"],
            "industry": options["industry"],
            "description": options["description"],
            "brand_name": options["brand_name"],
            "registration_number": options["registration_number"],
            "tin": options["tin"],
            "established_date": options["established_date"],
            "company_size": options["company_size"],
            "headquarters_address": options["headquarters_address"],
            "primary_phone": options["primary_phone"],
            "secondary_phone": options["secondary_phone"],
            "email": options["company_email"],
            "website": options["website"],
            "facebook": options["facebook"],
            "linkedin": options["linkedin"],
            "company_country": options["country"],
        }
        kwargs = {k: v for k, v in field_map.items() if v is not None}

        for f in UNIQUE_OPTIONAL_FIELDS:
            value = kwargs.get(f)
            if value and Company.objects.filter(**{f: value}).exists():
                raise CommandError(
                    f"A company with {f}='{value}' already exists; "
                    f"choose a different value or omit --{f.replace('_', '-')}."
                )
            if not value and Company.objects.filter(**{f: ""}).exists():
                cli_flag = "--company-email" if f == "email" else f"--{f}"
                raise CommandError(
                    f"Cannot create company: another company already has an "
                    f"empty '{f}' and this field is unique. "
                    f"Pass {cli_flag} with a unique value."
                )

        try:
            with transaction.atomic():
                company = Company.objects.create(created_by=user, **kwargs)
        except IntegrityError as exc:
            raise CommandError(f"Database integrity error: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"Created Company id={company.id} '{company.company_name}' "
            f"(industry={company.industry}) linked to {user.email} (id={user.id})."
        ))
