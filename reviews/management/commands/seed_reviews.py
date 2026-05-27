from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.apps import apps
from faker import Faker
from django.contrib.auth import get_user_model
import random

# Import helper functions
from reviews.utils import has_collaborated_on_object, update_user_aggregate_rating


class Command(BaseCommand):
    help = "Seed Reviews for Jobs and Tasks with fake data (only for users who collaborated)"

    def add_arguments(self, parser):
        parser.add_argument("--reviews", type=int, default=50, help="Number of reviews to create")

    def handle(self, *args, **options):
        fake = Faker()
        reviews_count = options["reviews"]

        User = get_user_model()
        Review = apps.get_model('reviews', 'Review')
        Job = apps.get_model('ManageJobsTasks', 'Job')
        Task = apps.get_model('ManageJobsTasks', 'Task')

        users = list(User.objects.all())
        jobs = list(Job.objects.all())
        tasks = list(Task.objects.all())

        if not users or not (jobs or tasks):
            self.stdout.write(self.style.ERROR("❌ Not enough data: ensure users, jobs, and tasks exist."))
            return

        self.stdout.write(self.style.NOTICE("Seeding reviews based on collaborations..."))

        job_ct = ContentType.objects.get_for_model(Job)
        task_ct = ContentType.objects.get_for_model(Task)

        created_count = 0

        for _ in range(reviews_count):
            reviewer = random.choice(users)
            reviewee = random.choice([u for u in users if u != reviewer])

            # Randomly attach to Job or Task
            model_choice = random.choice(["job", "task"])

            if model_choice == "job" and jobs:
                obj = random.choice(jobs)
                content_type = job_ct
            elif tasks:
                obj = random.choice(tasks)
                content_type = task_ct
            else:
                continue

            # Check collaboration before allowing review
            if not has_collaborated_on_object(reviewer, reviewee, obj):
                continue  # skip users who never worked together

            # Prevent duplicate review for same reviewer-object combo
            if Review.objects.filter(reviewer=reviewer, content_type=content_type, object_id=obj.pk).exists():
                continue

            # Create the review
            Review.objects.create(
                reviewer=reviewer,
                reviewee=reviewee,
                content_type=content_type,
                object_id=obj.pk,
                rating=random.randint(1, 5),
                review_text=fake.sentence(nb_words=15),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            created_count += 1

            # Update aggregate rating for reviewee
            update_user_aggregate_rating(reviewee)

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully seeded {created_count} collaborative reviews!"))
