from django.contrib import admin

from finances.models.payment import Payment
from finances.models.plan import Plan


class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code_name',
        'price',
        'credits',
        'is_subscription',
        'is_featured',
        'is_active',
        'sort_order',
    )
    list_filter = ('is_subscription', 'is_api_plan', 'is_featured', 'is_active')
    list_editable = ('sort_order', 'is_active', 'is_featured')
    search_fields = ('name', 'code_name')
    ordering = ('sort_order', 'price')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'code_name', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'price_cents', 'label_price', 'credits')
        }),
        ('Plan Limits', {
            'fields': ('monthly_exports', 'max_resolution', 'priority_rendering', 'commercial_use')
        }),
        ('Features Display', {
            'fields': ('features',),
            'description': 'JSON list of feature strings shown on pricing page. Example: ["100 credits/month", "HD exports", "Priority support"]'
        }),
        ('Payment Processors', {
            'fields': ('stripe_key', 'paypal_key', 'paypal_product_key', 'square_key', 'coinbase_key'),
            'classes': ('collapse',),
        }),
        ('Plan Type', {
            'fields': ('is_subscription', 'yearly_subscription', 'days', 'is_api_plan')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_active', 'sort_order')
        }),
    )


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'processor',
        'amount',
        'status',
        'created_at'
    )
    search_fields = (
        'uuid',
    )


admin.site.register(Plan, PlanAdmin)
admin.site.register(Payment, PaymentAdmin)
