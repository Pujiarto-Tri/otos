# Auto merge migration to resolve conflicting leaf nodes
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('otosapp', '0006_add_category_teachers'),
        ('otosapp', '0020_category_created_by'),
    ]

    operations = [
        # This merge migration intentionally has no operations; it resolves the
        # divergent migration history by creating a new migration that depends
        # on both conflicting leaf nodes.
    ]
