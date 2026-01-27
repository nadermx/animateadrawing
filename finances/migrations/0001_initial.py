# This migration represents the original state of the finances_plan table.
# The table already exists in the database, so we use state_operations
# to update Django's state without modifying the database.
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code_name', models.CharField(max_length=250, unique=True)),
                ('price', models.IntegerField(default=1)),
                ('label_price', models.IntegerField(blank=True, null=True)),
                ('credits', models.IntegerField(default=0)),
                ('paypal_product_key', models.CharField(blank=True, max_length=250, null=True)),
                ('paypal_key', models.CharField(blank=True, max_length=250, null=True)),
                ('coinbase_key', models.CharField(blank=True, max_length=250, null=True)),
                ('stripe_key', models.CharField(blank=True, max_length=250, null=True)),
                ('square_key', models.CharField(blank=True, max_length=250, null=True)),
                ('days', models.IntegerField(blank=True, null=True)),
                ('yearly_subscription', models.BooleanField(default=False)),
                ('is_subscription', models.BooleanField(default=False)),
                ('is_api_plan', models.BooleanField(default=False)),
            ],
        ),
    ]
