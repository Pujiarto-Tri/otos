from django.core.management.base import BaseCommand
from otosapp.models import Test, Answer

class Command(BaseCommand):
    help = 'Print test scores and correct answer counts for all submitted tests of all users.'

    def handle(self, *args, **options):
        tests = Test.objects.filter(is_submitted=True)
        for test in tests:
            total_answers = test.answers.count()
            correct_answers = test.answers.filter(selected_choice__is_correct=True).count()
            self.stdout.write(f"Test ID: {test.id}, Score: {test.score}, Total Answers: {total_answers}, Correct Answers: {correct_answers}, Tryout: {test.tryout_package_id}, Categories: {[c.category_name for c in test.categories.all()]}")
