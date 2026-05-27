from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from offers.models import Offer
from faker import Faker
import random

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Seed Offer model with fake data."

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of offers to create'
        )

    def handle(self, *args, **options):
        count = options['count']

        users = list(User.objects.all())
        if len(users) < 2:
            self.stdout.write(self.style.ERROR("❌ Need at least 2 users to generate offers."))
            return

        created = 0

        for _ in range(count):
            sender, receiver = random.sample(users, 2)  # ensures they aren't the same

            offer = Offer.objects.create(
                sender=sender,
                receiver=receiver,

                sender_full_name=f"{sender.first_name} {sender.last_name}".strip() or fake.name(),
                sender_email=sender.email,

                message=fake.paragraph(nb_sentences=5),

                is_read=random.choice([True, False])
            )

            created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully created {created} Offer records."))
        self.stdout.write(self.style.SUCCESS("🎯 Offer seeding completed!"))
