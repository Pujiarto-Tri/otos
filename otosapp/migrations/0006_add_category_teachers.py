# Generated minimal migration for adding teachers M2M to Category
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('otosapp', '0005_alter_question_pub_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='teachers',
            field=models.ManyToManyField(related_name='teaching_categories', to='otosapp.User', blank=True),
        ),
    ]
