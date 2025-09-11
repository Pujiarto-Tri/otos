from django.core.management.base import BaseCommand
from django.test.client import Client
from django.contrib.auth import get_user_model
from otosapp.models import Question, Choice, Category
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Test choice image display on edit form'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing choice image display on edit form...'))
        
        try:
            # Find a question with choice images
            question = Question.objects.filter(
                choices__choice_image__isnull=False
            ).distinct().first()
            
            if not question:
                self.stdout.write(self.style.WARNING('No question with choice images found.'))
                return
            
            self.stdout.write(f'Testing question ID: {question.id}')
            self.stdout.write(f'Question: {question.question_text[:50]}...')
            
            # Get choices and their images
            choices = question.choices.all()
            self.stdout.write(f'Total choices: {choices.count()}')
            
            for i, choice in enumerate(choices, 1):
                self.stdout.write(f'\nChoice {i}: {choice.choice_text[:30]}...')
                if choice.choice_image:
                    self.stdout.write(f'  Has image: {choice.choice_image.name}')
                    
                    # Test URL generation
                    try:
                        if choice.choice_image.name.startswith('https://'):
                            url = choice.choice_image.name
                            self.stdout.write(f'  URL (Vercel): {url}')
                        else:
                            url = choice.choice_image.url
                            self.stdout.write(f'  URL (Local): {url}')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  Error getting URL: {e}'))
                else:
                    self.stdout.write('  No image')
            
            # Simulate what happens in view
            self.stdout.write('\n--- Simulating view logic ---')
            initial_data = {}
            for i, choice in enumerate(choices, 1):
                if choice.choice_image:
                    image_name = choice.choice_image.name
                    if image_name.startswith('https://'):
                        initial_data[f'choice_image_{i}'] = image_name
                    else:
                        try:
                            initial_data[f'choice_image_{i}'] = choice.choice_image.url
                        except Exception:
                            initial_data[f'choice_image_{i}'] = f'/media/{image_name}'
            
            self.stdout.write('Initial data that would be sent to template:')
            for key, value in initial_data.items():
                self.stdout.write(f'  {key}: {value}')
            
            # Test template filter
            from otosapp.templatetags.custom_filters import get_choice_image
            self.stdout.write('\n--- Testing template filter ---')
            for i in range(1, 6):
                result = get_choice_image(initial_data, i)
                if result:
                    self.stdout.write(f'Choice {i} image URL: {result}')
                else:
                    self.stdout.write(f'Choice {i}: No image')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            traceback.print_exc()
