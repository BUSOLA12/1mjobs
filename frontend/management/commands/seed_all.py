from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Run all seeding commands currently available"

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=20, help="Number of users to create")
        parser.add_argument('--skills', type=int, default=10, help="Number of skills to create")
        parser.add_argument('--conversations', type=int, default=5, help="Number of conversations to create")
        parser.add_argument('--messages', type=int, default=20, help="Number of messages to create")
        parser.add_argument('--orders', type=int, default=5, help="Number of orders to create")
        parser.add_argument('--subscriptions', type=int, default=5, help="Number of subscriptions to create")
        parser.add_argument('--transactions', type=int, default=5, help="Number of transactions to create")

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("🚀 Starting full database seeding..."))

        # 1. Seed Users, Profiles, Skills, Categories
        call_command(
            'seed_users',
            users=options['users'],
            skills=options['skills'],
        )

        # 5. Seed Reviews
        call_command(
            'seed_reviews',
        )

        # # 3. Seed Conversations and Messages
        # call_command(
        #     'seed_messaging',
        #     conversations=options['conversations'],
        #     messages=options['messages']
        # )

        # 4. Seed Pricing, Orders, Subscriptions, Transactions
        call_command(
            'seed_pricing',
            orders=options['orders'],
            subscriptions=options['subscriptions'],
            transactions=options['transactions']
        )

        call_command(
            'seed_offer'
        )

        self.stdout.write(self.style.SUCCESS("✅ Database seeding completed successfully!"))
