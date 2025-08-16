from django.core.management.base import BaseCommand
from otosapp.models import Test
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Print all tryout test scores for a specific user (by email or username)'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, help='User email or username')

    def handle(self, *args, **options):
        user_identifier = options['user']
        User = get_user_model()
        try:
            user = User.objects.get(email=user_identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=user_identifier)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User not found: {user_identifier}'))
                return

        tests = Test.objects.filter(student=user, is_submitted=True, tryout_package__isnull=False)
        if not tests.exists():
            self.stdout.write(self.style.WARNING(f'No tryout tests found for user: {user_identifier}'))
            return

        for test in tests:
            self.stdout.write(f"Test ID: {test.id}, Score: {test.score}, Answers: {test.answers.count()}, Tryout: {test.tryout_package_id}, Categories: {[c.category_name for c in test.categories.all()]}")
