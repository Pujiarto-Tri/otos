from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('otosapp', '0013_subscriptionpackage_paymentproof_usersubscription'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscriptionpackage',
            name='package_type',
        ),
    ]
