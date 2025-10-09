from django.db import migrations, models


TIER_REMAP_FORWARD = {
    "basic": "silver",
    "pro": "gold",
    "elite": "tuntas",
}


TIER_REMAP_REVERSE = {v: k for k, v in TIER_REMAP_FORWARD.items()}


def replace_access_levels_forward(apps, schema_editor):
    SubscriptionPackage = apps.get_model("otosapp", "SubscriptionPackage")
    TryoutPackage = apps.get_model("otosapp", "TryoutPackage")

    for old_value, new_value in TIER_REMAP_FORWARD.items():
        SubscriptionPackage.objects.filter(access_level=old_value).update(access_level=new_value)
        TryoutPackage.objects.filter(required_access_level=old_value).update(required_access_level=new_value)


def replace_access_levels_reverse(apps, schema_editor):
    SubscriptionPackage = apps.get_model("otosapp", "SubscriptionPackage")
    TryoutPackage = apps.get_model("otosapp", "TryoutPackage")

    for new_value, old_value in TIER_REMAP_REVERSE.items():
        SubscriptionPackage.objects.filter(access_level=new_value).update(access_level=old_value)
        TryoutPackage.objects.filter(required_access_level=new_value).update(required_access_level=old_value)


class Migration(migrations.Migration):

    dependencies = [
        ("otosapp", "0034_access_levels"),
    ]

    operations = [
        migrations.RunPython(replace_access_levels_forward, replace_access_levels_reverse),
        migrations.AlterField(
            model_name="subscriptionpackage",
            name="access_level",
            field=models.CharField(
                choices=[
                    ("visitor", "Visitor / Gratis"),
                    ("silver", "Silver"),
                    ("gold", "Gold"),
                    ("tuntas", "Tuntas"),
                ],
                default="silver",
                help_text="Tentukan tier akses yang diberikan paket ini",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="tryoutpackage",
            name="required_access_level",
            field=models.CharField(
                choices=[
                    ("visitor", "Visitor / Gratis"),
                    ("silver", "Silver"),
                    ("gold", "Gold"),
                    ("tuntas", "Tuntas"),
                ],
                default="silver",
                help_text="Tingkat akses minimum yang dibutuhkan untuk mengerjakan paket",
                max_length=20,
            ),
        ),
    ]
