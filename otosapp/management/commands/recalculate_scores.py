from django.core.management.base import BaseCommand
from otosapp.models import Test

class Command(BaseCommand):
    help = 'Recalculate scores for all submitted tests.'

    def handle(self, *args, **options):
        tests = Test.objects.filter(is_submitted=True)
        updated = 0
        for test in tests:
            test.calculate_score()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Recalculated scores for {updated} submitted tests.'))
