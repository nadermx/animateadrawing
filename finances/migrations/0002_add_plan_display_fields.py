# Generated manually to add display fields to Plan model
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finances', '0001_initial'),  # Depends on the existing 0001_initial that created the table
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='name',
            field=models.CharField(default='', help_text='Display name (e.g., "Creator Plan")', max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='plan',
            name='description',
            field=models.TextField(blank=True, default='', help_text='Short description of what the plan includes'),
        ),
        migrations.AddField(
            model_name='plan',
            name='price_cents',
            field=models.IntegerField(default=100, help_text='Price in cents (for payment processing)'),
        ),
        migrations.AddField(
            model_name='plan',
            name='monthly_exports',
            field=models.IntegerField(default=10, help_text='Max exports per month (0=unlimited)'),
        ),
        migrations.AddField(
            model_name='plan',
            name='max_resolution',
            field=models.CharField(default='1080p', help_text='Max export resolution', max_length=20),
        ),
        migrations.AddField(
            model_name='plan',
            name='priority_rendering',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='plan',
            name='commercial_use',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='plan',
            name='features',
            field=models.JSONField(blank=True, default=list, help_text='List of feature strings for display'),
        ),
        migrations.AddField(
            model_name='plan',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Show as "Most Popular"'),
        ),
        migrations.AddField(
            model_name='plan',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Show on pricing page'),
        ),
        migrations.AddField(
            model_name='plan',
            name='sort_order',
            field=models.IntegerField(default=0, help_text='Display order on pricing page'),
        ),
    ]
