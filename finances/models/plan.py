import requests
from django.db import models
from django.utils.text import slugify

from config import PAYPAL_KEYS


class Plan(models.Model):
    # Display info
    name = models.CharField(max_length=100, help_text='Display name (e.g., "Creator Plan")')
    code_name = models.CharField(max_length=250, unique=True)
    description = models.TextField(blank=True, help_text='Short description of what the plan includes')

    # Pricing
    price = models.IntegerField(default=1, help_text='Price in dollars (for display)')
    price_cents = models.IntegerField(default=100, help_text='Price in cents (for payment processing)')
    label_price = models.IntegerField(null=True, blank=True, help_text='Original price if discounted')

    # Credits and limits
    credits = models.IntegerField(default=0)
    monthly_exports = models.IntegerField(default=10, help_text='Max exports per month (0=unlimited)')
    max_resolution = models.CharField(max_length=20, default='1080p', help_text='Max export resolution')
    priority_rendering = models.BooleanField(default=False)
    commercial_use = models.BooleanField(default=True)

    # Features (stored as JSON for flexibility)
    features = models.JSONField(default=list, blank=True, help_text='List of feature strings for display')

    # Payment processor keys
    paypal_product_key = models.CharField(max_length=250, null=True, blank=True)
    paypal_key = models.CharField(max_length=250, null=True, blank=True)
    coinbase_key = models.CharField(max_length=250, null=True, blank=True)
    stripe_key = models.CharField(max_length=250, null=True, blank=True)
    square_key = models.CharField(max_length=250, null=True, blank=True)

    # Plan configuration
    days = models.IntegerField(null=True, blank=True)
    yearly_subscription = models.BooleanField(default=False)
    is_subscription = models.BooleanField(default=False)
    is_api_plan = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False, help_text='Show as "Most Popular"')
    is_active = models.BooleanField(default=True, help_text='Show on pricing page')
    sort_order = models.IntegerField(default=0, help_text='Display order on pricing page')

    class Meta:
        ordering = ['sort_order', 'price']

    def __str__(self):
        return f"{self.name} (${self.price}/mo)" if self.is_subscription else f"{self.name} (${self.price})"

    def get_monthly_price(self):
        """Get equivalent monthly price for display."""
        if self.yearly_subscription:
            return self.price / 12
        return self.price

    def save(self, *args, **kwargs):
        self.code_name = slugify(self.code_name)
        super().save(*args, **kwargs)

    @staticmethod
    def create_paypal_product():
        product_name = 'Services'
        params = {
            'name': product_name,
            'description': product_name,
            'type': 'SERVICE',
            'category': 'SOFTWARE'
        }
        auth_values = (PAYPAL_KEYS.get('id'), PAYPAL_KEYS.get('secret'))
        r = requests.post(
            '%s/v1/catalogs/products' % PAYPAL_KEYS.get('api'),
            auth=auth_values,
            json=params
        ).json()

        if r.get('id'):
            for plan in Plan.objects.all():
                plan.paypal_product_key = r.get('id')
                plan.save()

            print('Product created')
        else:
            print('Product not created')

    @staticmethod
    def create_update_paypal_billing_plans():
        plans = Plan.objects.filter(
            is_subscription=True
        )

        for plan in plans.filter():
            params = {
                'product_id': plan.paypal_product_key,
                'name': '%s credits' % plan.credits,
                'description': 'service',
                'status': 'ACTIVE',
                'billing_cycles': [
                    {
                        'frequency': {
                            'interval_unit': 'MONTH',
                            'interval_count': 12 if plan.yearly_subscription else 1
                        },
                        'tenure_type': 'REGULAR',
                        'sequence': 1,
                        'total_cycles': 0,
                        'pricing_scheme': {
                            'fixed_price': {
                                'value': '%s' % plan.price,
                                'currency_code': 'USD'
                            }
                        }
                    }
                ],
                'payment_preferences': {
                    'auto_bill_outstanding': False,
                    'setup_fee_failure_action': 'CONTINUE',
                    'payment_failure_threshold': 3
                }
            }
            auth_values = (PAYPAL_KEYS.get('id'), PAYPAL_KEYS.get('secret'))
            r = requests.post(
                '%s/v1/billing/plans' % PAYPAL_KEYS.get('api'),
                auth=auth_values,
                json=params
            ).json()

            if r.get('id'):
                plan.paypal_key = r.get('id')
                plan.save()
                print('Plan created')
            else:
                print(r)
                print('Plan not created')
