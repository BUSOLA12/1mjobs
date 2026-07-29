from decimal import Decimal

from django.core.management.base import BaseCommand

from pricing.models import Plan, PlanFeature


# Free + Pro model: everything core is free (profiles, applying, posting,
# payments, KYC). One Pro plan per side carries the paid perks; old tiered
# plans are deactivated (never deleted) so existing subscriptions keep working.
PLANS = [
    {
        "name": "pro",
        "user_type": "freelancer",
        "description": "Freelancer Pro — featured profile, see who viewed you, "
                       "12h early access to new jobs, higher search ranking, priority support.",
        "monthly_price": Decimal("15000.00"),
        "yearly_price": Decimal("150000.00"),
        "features": [
            {"feature_name": "featured_profile", "limit": None, "is_boolean": True},
            {"feature_name": "profile_viewers", "limit": None, "is_boolean": True},
            {"feature_name": "early_access", "limit": None, "is_boolean": True},
            {"feature_name": "search_boost", "limit": None, "is_boolean": True},
            {"feature_name": "priority_support", "limit": None, "is_boolean": True},
        ],
    },
    {
        "name": "pro",
        "user_type": "employer",
        "description": "Employer Pro — featured job posts, direct offers to freelancers, "
                       "premium badge, advanced hiring analytics, priority support.",
        "monthly_price": Decimal("25000.00"),
        "yearly_price": Decimal("250000.00"),
        "features": [
            {"feature_name": "featured_job", "limit": 5, "is_boolean": False},
            {"feature_name": "offers", "limit": None, "is_boolean": False},
            {"feature_name": "premium_badge", "limit": None, "is_boolean": True},
            {"feature_name": "hiring_analytics", "limit": None, "is_boolean": True},
            {"feature_name": "priority_support", "limit": None, "is_boolean": True},
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

        # Deactivate plans not in the Free + Pro lineup. Never delete: existing
        # subscriptions keep their plan FK and stay valid until they expire.
        keep = {(p["user_type"], p["name"]) for p in PLANS}
        for plan in Plan.objects.filter(is_active=True):
            if (plan.user_type, plan.name) not in keep:
                plan.is_active = False
                plan.save(update_fields=["is_active"])
                self.stdout.write(f"  - Deactivated {plan.user_type}/{plan.name}")

        self.stdout.write(self.style.SUCCESS(
            f"🎉 Done. {Plan.objects.count()} total plans, "
            f"{PlanFeature.objects.count()} total features."
        ))
