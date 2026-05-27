from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.conf import settings
from faker import Faker
import random

from users.models import CustomUser, UserProfile, Skill, Category
from ManageJobsTasks.models import JOB_CATEGORIES

fake = Faker()

# from django.core.management.base import BaseCommand
# from faker import Faker
# import random
# from users.models import CustomUser, UserProfile, Skill, Category

# fake = Faker()

class Command(BaseCommand):
    help = "Seed database with test users and profiles (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=10, help="Number of users to create")
        parser.add_argument("--skills", type=int, default=20, help="Number of skills to create")

    def handle(self, *args, **options):
        user_count = options["users"]
        skill_count = options["skills"]

        # Create Categories
        category_names = JOB_CATEGORIES
        categories = []
        for name in category_names:
            category, _ = Category.objects.get_or_create(
                name=name,
                slug=slugify(name)
            )
            categories.append(category)
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories.'))

        # Create skills if not enough exist
        existing_skills = list(Skill.objects.all())
        while len(existing_skills) < skill_count:
            skill, created = Skill.objects.get_or_create(
                name=fake.unique.word()
            )
            existing_skills.append(skill)
        self.stdout.write(self.style.SUCCESS(f'Created {len(existing_skills)} skills.'))

        # Create users with profiles
        created_users = 0
        for _ in range(user_count):
            email = fake.unique.email()
            first_name = fake.first_name()
            last_name = fake.last_name()
            password = "password123"  # raw password

            user, user_created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                    "role": random.choice(["freelancer", "employer"]),
                    "two_step_verification": random.choice([True, False]),
                }
            )

            if user_created:
                user.set_password(password)  # hash the password properly
                user.save()
                created_users += 1
                print(f"Created: {email} | Password: {password}")

            # Create profile only if it doesn't exist
            if not hasattr(user, "user_profile"):
                profile = UserProfile.objects.create(
                    user=user,
                    bio=fake.text(),
                    tagline=fake.sentence(),
                    category=random.choice(categories),
                    hourly_rate=random.randint(20, 150),
                    nationality=fake.country(),
                    job_success=random.randint(50, 100),
                    rating=round(random.uniform(3.0, 5.0), 1),
                    verified=random.choice([True, False])
                )
                profile.skills.set(random.sample(existing_skills, random.randint(3, min(5, len(existing_skills)))))

        self.stdout.write(self.style.SUCCESS(
            f"✅ Seed completed: {created_users} new users added, {len(categories)} categories, {len(existing_skills)} skills."
        ))

