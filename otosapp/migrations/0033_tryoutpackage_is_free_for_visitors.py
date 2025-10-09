from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("otosapp", "0032_broadcastmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="tryoutpackage",
            name="is_free_for_visitors",
            field=models.BooleanField(
                default=False,
                help_text="Centang jika paket ini dapat diakses gratis oleh pengguna role Visitor",
            ),
        ),
    ]
