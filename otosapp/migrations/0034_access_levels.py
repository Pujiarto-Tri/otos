from django.db import migrations, models


def set_free_package_levels(apps, schema_editor):
    TryoutPackage = apps.get_model('otosapp', 'TryoutPackage')
    TryoutPackage.objects.filter(is_free_for_visitors=True).update(required_access_level='visitor')


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('otosapp', '0033_tryoutpackage_is_free_for_visitors'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionpackage',
            name='access_level',
            field=models.CharField(
                choices=[('visitor', 'Visitor (Gratis)'), ('basic', 'Basic'), ('pro', 'Pro'), ('elite', 'Elite')],
                default='basic',
                help_text='Tentukan tier akses yang diberikan paket ini',
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tryoutpackage',
            name='required_access_level',
            field=models.CharField(
                choices=[('visitor', 'Visitor (Gratis)'), ('basic', 'Basic'), ('pro', 'Pro'), ('elite', 'Elite')],
                default='basic',
                help_text='Tingkat akses minimum yang dibutuhkan untuk mengerjakan paket',
                max_length=20,
            ),
            preserve_default=False,
        ),
        migrations.RunPython(set_free_package_levels, noop),
    ]
