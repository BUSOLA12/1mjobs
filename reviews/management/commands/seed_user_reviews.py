from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.apps import apps
from django.contrib.auth import get_user_model
from faker import Faker
import random

# Import helper functions
from reviews.utils import has_collaborated_on_object, update_user_aggregate_rating

class Command(BaseCommand):
    help = "Seed Reviews for a single user based on random collaborations"

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, required=True, help="Email of the user to generate reviews for")
        parser.add_argument("--reviews", type=int, default=10, help="Number of random reviews to create")

    def handle(self, *args, **options):
        fake = Faker()
        user_email = options["email"]
        num_reviews = options["reviews"]

        User = get_user_model()
        Review = apps.get_model('reviews', 'Review')
        Job = apps.get_model('ManageJobsTasks', 'Job')
        Task = apps.get_model('ManageJobsTasks', 'Task')

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ No user found with email {user_email}"))
            return

        users = list(User.objects.exclude(id=user.id))
        jobs = list(Job.objects.all())
        tasks = list(Task.objects.all())

        if not users:
            self.stdout.write(self.style.ERROR("⚠️ No other users available for collaboration"))
            return
        if not (jobs or tasks):
            self.stdout.write(self.style.ERROR("⚠️ No jobs or tasks available to review"))
            return

        self.stdout.write(self.style.NOTICE(f"Seeding reviews for user: {user_email}..."))

        job_ct = ContentType.objects.get_for_model(Job)
        task_ct = ContentType.objects.get_for_model(Task)

        # Step 1: Generate random collaborations for this user
        collaborators = random.sample(users, min(len(users), random.randint(2, 5)))

        created_count = 0

        # Step 2: Create reviews for random Jobs/Tasks where user collaborated with others
        for _ in range(num_reviews):
            reviewee = random.choice(collaborators)
            model_choice = random.choice(["job", "task"])

            if model_choice == "job" and jobs:
                obj = random.choice(jobs)
                content_type = job_ct
            elif tasks:
                obj = random.choice(tasks)
                content_type = task_ct
            else:
                continue

            # Ensure the user actually collaborated with the reviewee on this object
            if not has_collaborated_on_object(user, reviewee, obj):
                continue

            # Avoid duplicates
            if Review.objects.filter(reviewer=user, content_type=content_type, object_id=obj.pk).exists():
                continue

            Review.objects.create(
                reviewer=user,
                reviewee=reviewee,
                content_type=content_type,
                object_id=obj.pk,
                rating=random.randint(3, 5),
                review_text=fake.sentence(nb_words=12),
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            created_count += 1

            # Update reviewee aggregate rating
            update_user_aggregate_rating(reviewee)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Created {created_count} reviews for {user_email} based on collaborations."
        ))
