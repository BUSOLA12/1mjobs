"""
Seed four known test personas plus the data needed to walk the whole revenue
model in a browser as a normal user. Idempotent: safe to re-run.

    python manage.py seed_plans          # once, creates the Free + Pro plans
    python manage.py seed_test_accounts

Logins (all password: password123):
    free.freelancer@test.local   free freelancer
    pro.freelancer@test.local    Pro freelancer
    free.employer@test.local     free employer
    pro.employer@test.local      Pro employer
"""
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from pricing.models import Plan, Subscription
from company.models import Company
from ManageJobsTasks.models import Job, Task, TaskBidding, JobApplication
from payments.models import Payment, Wallet
from users.models import ProfileView

User = get_user_model()

PASSWORD = "password123"

PERSONAS = [
    ("free.freelancer@test.local", "freelancer", "Free", "Freelancer", False),
    ("pro.freelancer@test.local", "freelancer", "Pat", "Pro-Freelancer", True),
    ("free.employer@test.local", "employer", "Free", "Employer", False),
    ("pro.employer@test.local", "employer", "Priya", "Pro-Employer", True),
]


class Command(BaseCommand):
    help = "Seed test personas + data to exercise the revenue model in a browser."

    def handle(self, *args, **options):
        out = self.stdout
        style = self.style

        # --- Plans must exist first ---
        fre_plan = Plan.objects.filter(user_type="freelancer", name="pro", is_active=True).first()
        emp_plan = Plan.objects.filter(user_type="employer", name="pro", is_active=True).first()
        if not fre_plan or not emp_plan:
            out.write(style.ERROR(
                "Pro plans not found. Run `python manage.py seed_plans` first."
            ))
            return

        out.write(style.NOTICE("Seeding test accounts..."))

        users = {}
        for email, role, first, last, is_pro in PERSONAS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"role": role, "first_name": first, "last_name": last},
            )
            # Always normalize the fields that matter for a clean local login.
            user.role = role
            user.first_name = first
            user.last_name = last
            user.two_step_verification = False
            user.verified_email = True
            user.onboarding_completed = True
            user.account_status = "active"
            user.is_banned = False
            user.set_password(PASSWORD)
            user.save()
            users[email] = user

            # Signals create the profile; enrich it so cards look real.
            profile = user.user_profile
            profile.verified = True
            if role == "freelancer":
                profile.tagline = f"{first} the developer"
                profile.hourly_rate = Decimal("50")
                profile.job_success = 90
            profile.save()

            # Pro state = an active subscription (no payment needed for perks).
            if is_pro:
                plan = fre_plan if role == "freelancer" else emp_plan
                sub = Subscription.objects.filter(user=user, plan=plan, is_active=True).first()
                if not sub:
                    Subscription.objects.create(
                        user=user, plan=plan, billing_cycle="monthly",
                        start_date=timezone.now(),
                        end_date=timezone.now() + timedelta(days=30),
                        is_active=True,
                    )

        free_f = users["free.freelancer@test.local"]
        pro_f = users["pro.freelancer@test.local"]
        free_e = users["free.employer@test.local"]
        pro_e = users["pro.employer@test.local"]

        # --- Companies (premium badge derives from the subscription, not verified) ---
        for owner, name, verified in [
            (pro_e, "Priya Ventures", True),
            (free_e, "Free Co", False),
        ]:
            Company.objects.get_or_create(
                created_by=owner,
                defaults={
                    "company_name": name,
                    "industry": "information_technology",
                    "description": f"{name} test company.",
                    "company_country": "Nigeria",
                    "verified": verified,
                    "verification_status": "approved" if verified else "pending",
                },
            )

        # --- Jobs: old + fresh (early access) + featured (ranking) ---
        job_defaults = dict(
            user=pro_e, job_type="full-time", category="information_technology",
            country="Nigeria", location="Remote", city="Lagos",
            salary_min=200000, salary_max=400000, tags="Python, Django",
            description="Test job for local walkthrough.", approved=True,
        )
        old_job, _ = Job.objects.get_or_create(title="TEST Old Job (visible to all)", defaults=job_defaults)
        Job.objects.filter(id=old_job.id).update(created_at=timezone.now() - timedelta(hours=48))

        Job.objects.get_or_create(title="TEST Fresh Job (Pro early access)", defaults=job_defaults)

        featured_defaults = dict(job_defaults)
        featured_defaults["is_featured"] = True
        Job.objects.get_or_create(title="TEST Featured Job", defaults=featured_defaults)

        # --- Profile views on the Pro freelancer (who-viewed panel) ---
        for viewer in [pro_e, free_e, free_f]:
            ProfileView.objects.get_or_create(
                profile=pro_f.user_profile, viewer=viewer,
                defaults={"ip_address": "127.0.0.1"},
            )

        # --- Job applications on the employer's jobs (hiring analytics) ---
        for i, status_val in enumerate(["pending", "accepted", "pending"]):
            JobApplication.objects.get_or_create(
                job=old_job, user=pro_f,
                name=f"Applicant {i}",
                defaults={"email": f"applicant{i}@test.local", "status": status_val},
            )

        # --- Task + accepted bid: the manage-bidders -> Pay Freelancer flow ---
        task, _ = Task.objects.get_or_create(
            user=pro_e, project_name="TEST Task to Pay",
            defaults=dict(
                category="software_developing", location="Remote",
                budget_min=Decimal("10000"), budget_max=Decimal("20000"),
                project_type="fixed", skills="Python, Django",
                description="Test task for the pay-freelancer flow.",
                expiration_date=timezone.now() + timedelta(days=30), status="active",
            ),
        )
        TaskBidding.objects.get_or_create(
            task=task, freelancer=pro_f,
            defaults=dict(bid_amount=Decimal("15000"), delivery_time="7 days",
                          status="accepted", read_TC=True),
        )

        # --- Ready-made payments for the commission demo ---
        # 1) ESCROWED payment: releasing it demonstrates the 10% split instantly.
        escrow_ref = "PAY-TESTESCROW01"
        escrow_pay, created = Payment.objects.get_or_create(
            payment_reference=escrow_ref,
            defaults=dict(employer=pro_e, freelancer=pro_f, task=task,
                          amount=Decimal("10000"), status="ESCROWED"),
        )
        if created:
            wallet, _ = Wallet.objects.get_or_create(user=pro_f)
            wallet.pending_balance += Decimal("10000")
            wallet.save()

        # 2) NOT_INITIATED payment: initiate + pay it in the browser (test card).
        Payment.objects.get_or_create(
            payment_reference="PAY-TESTNEW01",
            defaults=dict(employer=pro_e, freelancer=pro_f, task=task,
                          amount=Decimal("5000"), status="NOT_INITIATED"),
        )

        # --- Summary ---
        out.write(style.SUCCESS("\nDone. Test logins (password: password123):"))
        for email, role, *_ in PERSONAS:
            out.write(f"  {email}  ({role})")
        out.write("")
        out.write(f"  ESCROWED payment id (release to see the 10% split): {escrow_pay.id}")
        out.write(f"  Task with accepted bid for the Pay Freelancer flow: task id {task.id}")
        out.write(style.SUCCESS(
            "\nShell release demo:\n"
            "  python manage.py shell\n"
            "  >>> from payments.models import Payment\n"
            "  >>> from payments.services.payment_service import PaymentService\n"
            f"  >>> PaymentService.release_payment(Payment.objects.get(id={escrow_pay.id}))\n"
        ))
