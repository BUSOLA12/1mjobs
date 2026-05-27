from decimal import Decimal

from django.core.management.base import BaseCommand

from pricing.models import Plan, PlanFeature


PLANS = [
    # ---------------- Freelancer ----------------
    {
        "name": "basic",
        "user_type": "freelancer",
        "description": "Basic Freelancer Plan — get started with limited applications and bids.",
        "monthly_price": Decimal("3000.00"),
        "yearly_price": Decimal("30000.00"),
        "features": [
            {"feature_name": "job_applications", "limit": 5, "is_boolean": False},
            {"feature_name": "biddings", "limit": 10, "is_boolean": False},
            {"feature_name": "offers", "limit": 5, "is_boolean": False},
        ],
    },
    {
        "name": "standard",
        "user_type": "freelancer",
        "description": "Standard Freelancer Plan — higher monthly limits for active freelancers.",
        "monthly_price": Decimal("7000.00"),
        "yearly_price": Decimal("70000.00"),
        "features": [
            {"feature_name": "job_applications", "limit": 25, "is_boolean": False},
            {"feature_name": "biddings", "limit": 100, "is_boolean": False},
            {"feature_name": "offers", "limit": 20, "is_boolean": False},
        ],
    },
    {
        "name": "pro",
        "user_type": "freelancer",
        "description": "Pro Freelancer Plan — unlimited applications, biddings, and a verified badge.",
        "monthly_price": Decimal("15000.00"),
        "yearly_price": Decimal("150000.00"),
        "features": [
            {"feature_name": "job_applications", "limit": None, "is_boolean": False},
            {"feature_name": "biddings", "limit": None, "is_boolean": False},
            {"feature_name": "offers", "limit": None, "is_boolean": False},
            {"feature_name": "verified_badge", "limit": None, "is_boolean": True},
        ],
    },

    # ---------------- Employer ----------------
    {
        "name": "basic",
        "user_type": "employer",
        "description": "Basic Employer Plan — small teams hiring occasionally.",
        "monthly_price": Decimal("5000.00"),
        "yearly_price": Decimal("50000.00"),
        "features": [
            {"feature_name": "job_listings", "limit": 4, "is_boolean": False},
            {"feature_name": "task_listings", "limit": 6, "is_boolean": False},
        ],
    },
    {
        "name": "business",
        "user_type": "employer",
        "description": "Business Employer Plan — growing companies with active hiring.",
        "monthly_price": Decimal("12000.00"),
        "yearly_price": Decimal("120000.00"),
        "features": [
            {"feature_name": "job_listings", "limit": 8, "is_boolean": False},
            {"feature_name": "task_listings", "limit": 12, "is_boolean": False},
            {"feature_name": "verified_badge", "limit": None, "is_boolean": True},
        ],
    },
    {
        "name": "enterprise",
        "user_type": "employer",
        "description": "Enterprise Employer Plan — large companies hiring at scale.",
        "monthly_price": Decimal("50000.00"),
        "yearly_price": Decimal("500000.00"),
        "features": [
            {"feature_name": "job_listings", "limit": 50, "is_boolean": False},
            {"feature_name": "task_listings", "limit": 50, "is_boolean": False},
            {"feature_name": "verified_badge", "limit": None, "is_boolean": True},
        ],
    },
]


class Command(BaseCommand):
    help = "Seed (or update) membership Plans with monthly & yearly pricing and their features."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-features",
            action="store_true",
            help="Delete and recreate all features for each plan (otherwise features are upserted by name).",
        )

    def handle(self, *args, **options):
        reset_features = options["reset_features"]

        self.stdout.write(self.style.NOTICE("🚀 Seeding membership plans (monthly & yearly)..."))

        for plan_data in PLANS:
            plan, created = Plan.objects.update_or_create(
                name=plan_data["name"],
                user_type=plan_data["user_type"],
                defaults={
                    "description": plan_data["description"],
                    "monthly_price": plan_data["monthly_price"],
                    "yearly_price": plan_data["yearly_price"],
                    "is_active": True,
                },
            )

            if reset_features:
                plan.features.all().delete()

            for f in plan_data["features"]:
                PlanFeature.objects.update_or_create(
                    plan=plan,
                    feature_name=f["feature_name"],
                    defaults={
                        "limit": f["limit"],
                        "is_boolean": f["is_boolean"],
                    },
                )

            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(
                f"  ✓ {verb} {plan.user_type}/{plan.name} "
                f"(monthly ₦{plan.monthly_price:,.0f}, yearly ₦{plan.yearly_price:,.0f})"
            ))

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Done. {Plan.objects.count()} total plans, "
            f"{PlanFeature.objects.count()} total features."
        ))
