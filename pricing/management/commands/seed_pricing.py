from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pricing.models import Plan, PlanFeature, Order, Subscription, Transaction
from django.utils import timezone
from faker import Faker
import random
from datetime import timedelta

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Seed Plans, PlanFeatures, Orders, Subscriptions, and Transactions data"

    def add_arguments(self, parser):
        parser.add_argument('--orders', type=int, default=50, help='Number of orders to create')
        parser.add_argument('--subscriptions', type=int, default=10, help='Number of subscriptions to create')
        parser.add_argument('--transactions', type=int, default=10, help='Number of transactions to create')

    def handle(self, *args, **options):
        orders_count = options['orders']
        subs_count = options['subscriptions']
        tx_count = options['transactions']

        users = list(User.objects.all())
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Please create users first."))
            return

        # -----------------
        # 1. Clear & Seed Plans
        # -----------------
        Plan.objects.all().delete()
        PlanFeature.objects.all().delete()

        plans_data = [
            {
                'name': 'basic',
                'user_type': 'freelancer',
                'description': 'Basic Freelancer Plan',
                'monthly_price': 3000,   # NGN
                'yearly_price': 30000,   # NGN
                'features': [
                    {'feature_name': 'job_applications', 'limit': 5, 'is_boolean': False},
                    {'feature_name': 'biddings', 'limit': 10, 'is_boolean': False},
                    {'feature_name': 'offers', 'limit': 5, 'is_boolean': False},
                ]
            },
            {
                'name': 'standard',
                'user_type': 'freelancer',
                'description': 'Standard Freelancer Plan',
                'monthly_price': 7000,
                'yearly_price': 70000,
                'features': [
                    {'feature_name': 'job_applications', 'limit': 25, 'is_boolean': False},
                    {'feature_name': 'biddings', 'limit': 100, 'is_boolean': False},
                    {'feature_name': 'offers', 'limit': 20, 'is_boolean': False},
                ]
            },
            {
                'name': 'pro',
                'user_type': 'freelancer',
                'description': 'Pro Freelancer Plan',
                'monthly_price': 15000,
                'yearly_price': 150000,
                'features': [
                    {'feature_name': 'job_applications', 'limit': None, 'is_boolean': False},
                    {'feature_name': 'biddings', 'limit': None, 'is_boolean': False},
                    {'feature_name': 'offers', 'limit': None, 'is_boolean': False},
                    {'feature_name': 'verified_badge', 'limit': None, 'is_boolean': True},
                ]
            },
            {
                'name': 'basic',
                'user_type': 'employer',
                'description': 'Basic Employer Plan',
                'monthly_price': 5000,
                'yearly_price': 50000,
                'features': [
                    {'feature_name': 'job_listings', 'limit': 4, 'is_boolean': False},
                    {'feature_name': 'task_listings', 'limit': 6, 'is_boolean': False},
                ]
            },
            {
                'name': 'business',
                'user_type': 'employer',
                'description': 'Business Employer Plan',
                'monthly_price': 12000,
                'yearly_price': 120000,
                'features': [
                    {'feature_name': 'job_listings', 'limit': 8, 'is_boolean': False},
                    {'feature_name': 'task_listings', 'limit': 12, 'is_boolean': False},
                    {'feature_name': 'verified_badge', 'limit': None, 'is_boolean': True},
                ]
            },
            {
                'name': 'enterprise',
                'user_type': 'employer',
                'description': 'Enterprise Employer Plan',
                'monthly_price': 50000,
                'yearly_price': 500000,
                'features': [
                    {'feature_name': 'job_listings', 'limit': 50, 'is_boolean': False},
                    {'feature_name': 'task_listings', 'limit': 50, 'is_boolean': False},
                    {'feature_name': 'verified_badge', 'limit': None, 'is_boolean': True},
                ]
            },
        ]

        created_plans = []
        for plan_data in plans_data:
            plan, _ = Plan.objects.update_or_create(
                name=plan_data['name'],
                user_type=plan_data['user_type'],
                defaults={
                    'description': plan_data['description'],
                    'monthly_price': plan_data['monthly_price'],
                    'yearly_price': plan_data['yearly_price']
                }
            )
            # Create features
            for f in plan_data['features']:
                PlanFeature.objects.create(
                    plan=plan,
                    feature_name=f['feature_name'],
                    limit=f['limit'],
                    is_boolean=f['is_boolean']
                )

            created_plans.append(plan)
            self.stdout.write(self.style.SUCCESS(f"✅ Plan '{plan.name}' with features created/updated."))

        # -----------------
        # 2. Seed Orders
        # -----------------
        created_orders = []
        for _ in range(orders_count):
            user = random.choice(users)
            plan = random.choice(created_plans)
            billing_cycle = random.choice(['monthly', 'yearly'])
            amount = plan.monthly_price if billing_cycle == 'monthly' else plan.yearly_price

            order = Order.objects.create(
                user=user,
                plan=plan,
                plan_name_snapshot=plan.name,
                billing_cycle=billing_cycle,
                amount=amount,
                status=random.choice(['pending', 'paid', 'failed']),
                payment_reference=fake.uuid4()
            )
            created_orders.append(order)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_orders)} orders."))

        # -----------------
        # 3. Seed Subscriptions
        # -----------------
        created_subs = []
        for _ in range(subs_count):
            user = random.choice(users)
            # select a that is for employer
            plan = random.choice([p for p in created_plans if p.user_type == 'freelancer'])
            billing_cycle = random.choice(['monthly', 'yearly'])
            start_date = timezone.now()
            if billing_cycle == 'monthly':
                end_date = start_date + timedelta(days=30)
            else:
                end_date = start_date + timedelta(days=365)

            # Build remaining_features dict from plan features
            remaining_features = {f.feature_name: f.limit if not f.is_boolean else True for f in plan.features.all()}

            subscription = Subscription.objects.create(
                user=user,
                plan=plan,
                order=random.choice(created_orders),
                billing_cycle=billing_cycle,
                start_date=start_date,
                end_date=end_date,
                remaining_features=remaining_features,
                is_active=True
            )
            created_subs.append(subscription)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_subs)} subscriptions."))

        # -----------------
        # 4. Seed Transactions
        # -----------------
        created_tx = []
        for _ in range(tx_count):
            order = random.choice(created_orders)
            tx = Transaction.objects.create(
                order=order,
                reference=fake.uuid4(),
                authorization_url=fake.url(),
                amount=order.amount,
                status=random.choice(['pending', 'success'])
            )
            created_tx.append(tx)

        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(created_tx)} transactions."))

        self.stdout.write(self.style.SUCCESS("🎯 Seeding completed successfully!"))
