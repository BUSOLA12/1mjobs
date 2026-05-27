from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ManageJobsTasks.models import Job, JobApplication, Task, JOB_TYPES, JOB_CATEGORIES, TASK_CATEGORIES, PROJECT_TYPES, TASK_STATUS, APPLICATION_STATUS, TaskBidding, STATUS_CHOICES
from faker import Faker
import random
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = "Seed Jobs, Job Applications, Tasks, and Task Biddings with fake data"

    def add_arguments(self, parser):
        parser.add_argument("--jobs", type=int, default=15, help="Number of jobs to create")
        parser.add_argument("--applications", type=int, default=50, help="Number of job applications to create")
        parser.add_argument("--tasks", type=int, default=10, help="Number of tasks to create")
        parser.add_argument("--bids", type=int, default=40, help="Number of task biddings to create")

    def handle(self, *args, **options):
        fake = Faker()

        jobs_count = options["jobs"]
        applications_count = options["applications"]
        tasks_count = options["tasks"]
        bids_count = options["bids"]

        self.stdout.write(self.style.NOTICE("🚀 Seeding started..."))

        # Ensure at least 5 users exist
        if User.objects.count() < 5:
            for _ in range(5):
                User.objects.create_user(
                    email=fake.unique.email(),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    password="password123"
                )

        users = list(User.objects.all())

        # ------------------- Create Jobs -------------------
        jobs = []
        for _ in range(jobs_count):
            job = Job.objects.create(
                user=random.choice(users),
                title=fake.job(),
                job_type=random.choice([jt[0] for jt in JOB_TYPES]),
                category=random.choice([jc[0] for jc in JOB_CATEGORIES]),
                country=fake.country(),
                location=fake.city(),
                salary_min=Decimal(random.randint(1000, 5000)),
                salary_max=Decimal(random.randint(5001, 10000)),
                tags=", ".join(fake.words(nb=5)),
                description=fake.text(max_nb_chars=300),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_active=True,
                approved=random.choice([True, False]),
            )
            jobs.append(job)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(jobs)} Jobs"))

        # ------------------- Create Job Applications -------------------
        job_applications = []
        for _ in range(applications_count):
            job = random.choice(jobs)
            application = JobApplication.objects.create(
                job=job,
                user=random.choice(users),
                name=fake.name(),
                email=fake.email(),
                created_at=timezone.now()
            )
            job_applications.append(application)

        for job in jobs:
            applications_qs = job.application.all()
            if applications_qs.exists():
                random_job_application = random.choice(applications_qs)
                random_job_application.status = "accepted"
                random_job_application.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(job_applications)} Job Applications"))

        # ------------------- Create Tasks -------------------
        tasks = []
        for _ in range(tasks_count):
            task = Task.objects.create(
                user=random.choice(users),
                project_name=fake.catch_phrase(),
                category=random.choice([tc[0] for tc in TASK_CATEGORIES]),
                location=fake.city(),
                budget_min=Decimal(random.randint(500, 2000)),
                budget_max=Decimal(random.randint(2001, 5000)),
                project_type=random.choice([pt[0] for pt in PROJECT_TYPES]),
                skills=", ".join(fake.words(nb=5)),
                status=random.choice([ts[0] for ts in TASK_STATUS]),
                description=fake.text(max_nb_chars=300),
                created_at=timezone.now(),
                updated_at=timezone.now(),
                is_featured=random.choice([True, False]),
                applications_count=random.randint(0, 20),
                views_count=random.randint(0, 200),
            )
            tasks.append(task)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(tasks)} Tasks"))

        # ------------------- Create Task Biddings -------------------
        biddings = []
        for _ in range(bids_count):
            task = random.choice(tasks)
            bidding = TaskBidding.objects.create(
                task=task,
                freelancer=random.choice(users),
                bid_amount=Decimal(random.randint(500, 5000)),
                delivery_time=f"{random.randint(1, 14)} days",
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            biddings.append(bidding)

        for task in tasks:
            tasks_qs = task.bidding.all()
            if tasks_qs.exists():
                random_bidding = random.choice(tasks_qs)
                random_bidding.status = "accepted"
                random_bidding.save()

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(biddings)} Task Biddings"))
        self.stdout.write(self.style.SUCCESS("🎉 Seeding completed successfully!"))
