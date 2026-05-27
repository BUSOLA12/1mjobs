import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from faker import Faker

from users.models import CustomUser, UserProfile, Skill, Category, WorkHistory

fake = Faker()

NIGERIAN_FIRST_NAMES = [
    "Chinedu", "Adaeze", "Tunde", "Funmi", "Emeka", "Ngozi", "Yusuf", "Aisha",
    "Bola", "Kemi", "Ifeoma", "Obinna", "Hauwa", "Segun", "Chidinma", "Uche",
    "Folake", "Ibrahim", "Zainab", "Olumide", "Blessing", "Ahmed", "Chioma",
    "Tobi", "Damilola", "Ekene", "Fatima", "Gbenga",
]

NIGERIAN_LAST_NAMES = [
    "Okafor", "Adeyemi", "Eze", "Bello", "Obi", "Mohammed", "Adekunle", "Nwosu",
    "Okonkwo", "Ibrahim", "Lawal", "Ogunleye", "Balogun", "Onyeka", "Yakubu",
    "Adesanya", "Olawale", "Abubakar", "Chukwu", "Ojo", "Akinyemi", "Sanni",
]

NIGERIAN_CITIES = [
    "Lagos", "Abuja", "Port Harcourt", "Ibadan", "Kano", "Benin City",
    "Kaduna", "Enugu", "Jos", "Calabar", "Uyo", "Owerri", "Abeokuta",
    "Warri", "Onitsha", "Aba", "Ilorin", "Akure", "Asaba", "Sokoto",
]

DEFAULT_SKILLS = [
    "Python", "Django", "JavaScript", "React", "Node.js", "PHP", "Laravel",
    "Graphic Design", "UI/UX Design", "Figma", "Photoshop", "Illustrator",
    "Copywriting", "SEO", "Content Writing", "Digital Marketing", "Sales",
    "Data Analysis", "Excel", "Power BI", "Bookkeeping", "Accounting",
    "Customer Service", "Translation", "Project Management", "WordPress",
    "Mobile Development", "Flutter", "Android", "iOS",
]

TAGLINES = [
    "Experienced {role} with a passion for delivering quality work",
    "Reliable {role} based in {city}, Nigeria",
    "Senior {role} | 5+ years of hands-on experience",
    "Detail-oriented {role} helping businesses grow",
    "Freelance {role} available for remote and on-site work",
]

PROFESSIONAL_ROLES = [
    "Software Developer", "Web Designer", "Graphic Designer", "Content Writer",
    "Digital Marketer", "Data Analyst", "Accountant", "Virtual Assistant",
    "Mobile Developer", "Project Manager", "Translator", "Social Media Manager",
]


class Command(BaseCommand):
    help = "Seed the database with Nigerian freelancer accounts and profiles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=15,
            help="Number of freelancers to create (default: 15)",
        )
        parser.add_argument(
            "--password", type=str, default="password123",
            help="Password to set on all created accounts (default: password123)",
        )
        parser.add_argument(
            "--with-work-history", action="store_true",
            help="Also create 1-3 WorkHistory entries per freelancer",
        )

    def handle(self, *args, **options):
        count = options["count"]
        password = options["password"]
        with_work_history = options["with_work_history"]

        self.stdout.write(self.style.NOTICE(f"🚀 Seeding {count} Nigerian freelancers..."))

        skills = self._ensure_skills()
        categories = self._ensure_categories()

        created = 0
        for _ in range(count):
            first_name = random.choice(NIGERIAN_FIRST_NAMES)
            last_name = random.choice(NIGERIAN_LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 9999)}@example.com"

            if CustomUser.objects.filter(email__iexact=email).exists():
                continue

            user = CustomUser.objects.create_user(
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

            profile, _ = UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "bio": fake.paragraph(nb_sentences=4),
                    "tagline": tagline,
                    "category": random.choice(categories) if categories else None,
                    "hourly_rate": Decimal(random.randint(2000, 25000)),  # NGN/hour
                    "nationality": "Nigeria",
                    "status": "active",
                    "job_success": random.randint(60, 100),
                    "rating": round(random.uniform(3.5, 5.0), 1),
                    "avg_rating": round(random.uniform(3.5, 5.0), 1),
                    "rating_count": random.randint(0, 50),
                    "kyc_verified": random.choice([True, False]),
                    "verified": random.choice([True, False]),
                },
            )
            profile.skills.set(random.sample(skills, k=min(5, random.randint(3, 5))))

            if with_work_history:
                self._seed_work_history(user)

            created += 1
            self.stdout.write(f"  ✓ {user.email} ({role}, {city})")

        self.stdout.write(self.style.SUCCESS(
            f"✅ Done. Created {created} freelancers. Password for all: '{password}'"
        ))

    def _ensure_skills(self):
        existing = {s.name.lower(): s for s in Skill.objects.all()}
        for name in DEFAULT_SKILLS:
            if name.lower() not in existing:
                existing[name.lower()] = Skill.objects.create(name=name)
        return list(existing.values())

    def _ensure_categories(self):
        # Reuse existing Category rows if seeded elsewhere; otherwise create a baseline.
        if Category.objects.exists():
            return list(Category.objects.all())
        baseline = [
            "Software Development", "Design & Creative", "Writing & Translation",
            "Sales & Marketing", "Admin Support", "Data & Analytics",
            "Accounting & Finance", "Customer Service",
        ]
        return [
            Category.objects.create(name=n, slug=slugify(n))
            for n in baseline
        ]

    def _seed_work_history(self, user):
        for _ in range(random.randint(1, 3)):
            start_year = random.randint(2015, 2023)
            end_year = random.randint(start_year, 2025)
            WorkHistory.objects.create(
                user=user,
                company_name=fake.company(),
                work_role=random.choice(PROFESSIONAL_ROLES),
                start_month_year=f"{random.choice(['Jan', 'Mar', 'Jun', 'Sep'])} {start_year}",
                end_month_year=("Present" if end_year == 2025 and random.random() < 0.3
                                else f"{random.choice(['Feb', 'Apr', 'Aug', 'Dec'])} {end_year}"),
                responsibilities=fake.paragraph(nb_sentences=3),
            )
