"""
Management command to set up default pricing plans.

GPU Cost Analysis:
- Server with 4x P40 GPUs: ~$500/month total infrastructure
- Transform animations: Nearly free (CPU, milliseconds)
- AI animations: ~30-60 per GPU per hour
- Target: 90% profit margin

Credit System:
- 1 credit = 1 transform animation (fast, preserves artwork)
- 5 credits = 1 AI video animation (SVD, more realistic)
- 2 credits = 1 HD export
- 5 credits = 1 4K export

Run with: python manage.py setup_pricing
"""
from django.core.management.base import BaseCommand
from finances.models.plan import Plan


DEFAULT_PLANS = [
    # Free Trial
    {
        'name': 'Free',
        'code_name': 'free',
        'description': 'Try Animate a Drawing with limited features',
        'price': 0,
        'price_cents': 0,
        'credits': 10,
        'monthly_exports': 3,
        'max_resolution': '720p',
        'priority_rendering': False,
        'commercial_use': False,
        'is_subscription': False,
        'is_featured': False,
        'is_active': True,
        'sort_order': 0,
        'features': [
            '10 credits to start',
            '3 exports per month',
            '720p resolution',
            'Watermarked exports',
            'Transform animations only',
        ],
    },
    # Starter
    {
        'name': 'Starter',
        'code_name': 'starter',
        'description': 'Perfect for hobbyists and casual creators',
        'price': 9,
        'price_cents': 900,
        'credits': 50,
        'monthly_exports': 10,
        'max_resolution': '1080p',
        'priority_rendering': False,
        'commercial_use': True,
        'is_subscription': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 1,
        'features': [
            '50 credits/month',
            '10 exports per month',
            'Full HD (1080p) exports',
            'No watermarks',
            'Transform + AI animations',
            'Commercial use license',
        ],
    },
    # Creator (Most Popular)
    {
        'name': 'Creator',
        'code_name': 'creator',
        'description': 'Best value for content creators and artists',
        'price': 29,
        'price_cents': 2900,
        'credits': 200,
        'monthly_exports': 0,  # Unlimited
        'max_resolution': '1080p',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': True,
        'is_featured': True,  # Most Popular
        'is_active': True,
        'sort_order': 2,
        'features': [
            '200 credits/month',
            'Unlimited exports',
            'Full HD (1080p) exports',
            'Priority rendering queue',
            'All animation types',
            'Commercial use license',
            'Email support',
        ],
    },
    # Pro
    {
        'name': 'Pro',
        'code_name': 'pro',
        'description': 'For professional animators and studios',
        'price': 79,
        'price_cents': 7900,
        'credits': 1000,
        'monthly_exports': 0,  # Unlimited
        'max_resolution': '4K',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 3,
        'features': [
            '1,000 credits/month',
            'Unlimited exports',
            '4K Ultra HD exports',
            'Priority rendering queue',
            'All animation types',
            'Full commercial license',
            'API access included',
            'Priority email support',
        ],
    },
    # Business
    {
        'name': 'Business',
        'code_name': 'business',
        'description': 'For agencies, teams, and high-volume users',
        'price': 199,
        'price_cents': 19900,
        'credits': 5000,
        'monthly_exports': 0,  # Unlimited
        'max_resolution': '4K',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 4,
        'features': [
            '5,000 credits/month',
            'Unlimited exports',
            '4K Ultra HD exports',
            'Highest priority rendering',
            'All animation types',
            'Full commercial license',
            'API access with higher limits',
            'Up to 5 team members',
            'Dedicated support',
        ],
    },
    # API Pay-as-you-go plans
    {
        'name': 'API - 500 Credits',
        'code_name': 'api-500',
        'description': 'Pay-as-you-go API credits',
        'price': 20,
        'price_cents': 2000,
        'credits': 500,
        'monthly_exports': 0,
        'max_resolution': '4K',
        'priority_rendering': False,
        'commercial_use': True,
        'is_subscription': False,
        'is_api_plan': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 10,
        'features': [
            '500 API credits',
            '$0.04 per credit',
            'Never expires',
            'Full API access',
            'All animation types',
        ],
    },
    {
        'name': 'API - 2,000 Credits',
        'code_name': 'api-2000',
        'description': 'Bulk API credits with discount',
        'price': 60,
        'price_cents': 6000,
        'credits': 2000,
        'monthly_exports': 0,
        'max_resolution': '4K',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': False,
        'is_api_plan': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 11,
        'features': [
            '2,000 API credits',
            '$0.03 per credit (25% off)',
            'Never expires',
            'Priority processing',
            'All animation types',
        ],
    },
    {
        'name': 'API - 10,000 Credits',
        'code_name': 'api-10000',
        'description': 'High-volume API credits',
        'price': 200,
        'price_cents': 20000,
        'credits': 10000,
        'monthly_exports': 0,
        'max_resolution': '4K',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': False,
        'is_api_plan': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 12,
        'features': [
            '10,000 API credits',
            '$0.02 per credit (50% off)',
            'Never expires',
            'Highest priority processing',
            'All animation types',
            'Dedicated support',
        ],
    },
    # Yearly plans (20% discount)
    {
        'name': 'Creator Yearly',
        'code_name': 'creator-yearly',
        'description': 'Creator plan billed annually - save 20%',
        'price': 278,  # $29 * 12 * 0.8 = $278.40
        'price_cents': 27840,
        'label_price': 348,  # Original yearly price
        'credits': 200,  # Monthly credits
        'monthly_exports': 0,
        'max_resolution': '1080p',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': True,
        'yearly_subscription': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 20,
        'features': [
            '200 credits/month (2,400/year)',
            'Save 20% vs monthly',
            'Unlimited exports',
            'Full HD (1080p) exports',
            'Priority rendering queue',
            'All animation types',
            'Commercial use license',
        ],
    },
    {
        'name': 'Pro Yearly',
        'code_name': 'pro-yearly',
        'description': 'Pro plan billed annually - save 20%',
        'price': 758,  # $79 * 12 * 0.8 = $758.40
        'price_cents': 75840,
        'label_price': 948,  # Original yearly price
        'credits': 1000,  # Monthly credits
        'monthly_exports': 0,
        'max_resolution': '4K',
        'priority_rendering': True,
        'commercial_use': True,
        'is_subscription': True,
        'yearly_subscription': True,
        'is_featured': False,
        'is_active': True,
        'sort_order': 21,
        'features': [
            '1,000 credits/month (12,000/year)',
            'Save 20% vs monthly',
            'Unlimited exports',
            '4K Ultra HD exports',
            'Priority rendering queue',
            'API access included',
            'Full commercial license',
        ],
    },
]


class Command(BaseCommand):
    help = 'Set up default pricing plans for Animate a Drawing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing plans with same code_name',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all existing plans before creating new ones',
        )

    def handle(self, *args, **options):
        force = options['force']
        clear = options['clear']

        if clear:
            deleted_count = Plan.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing plans'))

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for plan_data in DEFAULT_PLANS:
            code_name = plan_data['code_name']
            existing = Plan.objects.filter(code_name=code_name).first()

            if existing:
                if force:
                    for key, value in plan_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'Updated: {plan_data["name"]}'))
                else:
                    skipped_count += 1
                    self.stdout.write(f'Skipped (exists): {plan_data["name"]}')
            else:
                Plan.objects.create(**plan_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {plan_data["name"]}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Summary: {created_count} created, {updated_count} updated, {skipped_count} skipped'
        ))
        self.stdout.write('')
        self.stdout.write('Pricing tiers:')
        self.stdout.write('  Free:     $0    - 10 credits (trial)')
        self.stdout.write('  Starter:  $9/mo - 50 credits')
        self.stdout.write('  Creator:  $29/mo - 200 credits (Most Popular)')
        self.stdout.write('  Pro:      $79/mo - 1,000 credits')
        self.stdout.write('  Business: $199/mo - 5,000 credits')
        self.stdout.write('')
        self.stdout.write('API pricing:')
        self.stdout.write('  500 credits:   $20  ($0.04/credit)')
        self.stdout.write('  2,000 credits: $60  ($0.03/credit)')
        self.stdout.write('  10,000 credits: $200 ($0.02/credit)')
        self.stdout.write('')
        self.stdout.write('Credit costs:')
        self.stdout.write('  Transform animation: 1 credit')
        self.stdout.write('  AI video animation:  5 credits')
        self.stdout.write('  HD export:           2 credits')
        self.stdout.write('  4K export:           5 credits')
