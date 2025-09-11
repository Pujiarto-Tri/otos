#!/usr/bin/env python3

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.http import HttpRequest
from otosapp.models import Category, Question, Choice, User
from otosapp.forms import QuestionForm
import traceback

class Command(BaseCommand):
    help = 'Test template rendering for QuillJS issues'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Testing Template Syntax ==='))
        
        try:
            # Create a mock request
            factory = RequestFactory()
            request = factory.get('/admin/questions/add/')
            
            # Get or create a user for testing
            user, created = User.objects.get_or_create(
                username='testadmin',
                defaults={'is_staff': True, 'is_superuser': True}
            )
            request.user = user
            
            # Get or create a category
            category, created = Category.objects.get_or_create(
                category_name='Test Category',
                defaults={'created_by': user}
            )
            
            # Create a form instance
            form = QuestionForm()
            
            # Test template rendering
            context = {
                'form': form,
                'categories': Category.objects.all(),
                'question': None,
                'is_edit': False,
                'request': request,
            }
            
            self.stdout.write('Attempting to render template...')
            
            # Try to render the template
            rendered = render_to_string(
                'admin/manage_questions/question_form.html',
                context,
                request=request
            )
            
            # Check for JavaScript content
            if 'quillEditor = new Quill' in rendered:
                self.stdout.write(self.style.SUCCESS('✓ QuillJS initialization code found in rendered template'))
            else:
                self.stdout.write(self.style.WARNING('⚠ QuillJS initialization code NOT found in rendered template'))
            
            if 'try {' in rendered:
                self.stdout.write(self.style.SUCCESS(f'✓ Found {rendered.count("try {")} try blocks in template'))
            
            if 'catch' in rendered:
                self.stdout.write(self.style.SUCCESS(f'✓ Found {rendered.count("catch")} catch blocks in template'))
            
            # Check for script tags
            script_count = rendered.count('<script')
            self.stdout.write(self.style.SUCCESS(f'✓ Found {script_count} script tags in template'))
            
            # Check for QuillJS CDN
            if 'cdn.quilljs.com' in rendered:
                self.stdout.write(self.style.SUCCESS('✓ QuillJS CDN link found'))
            else:
                self.stdout.write(self.style.ERROR('✗ QuillJS CDN link NOT found'))
            
            # Check for specific QuillJS elements
            if 'quill-editor' in rendered:
                self.stdout.write(self.style.SUCCESS('✓ QuillJS editor container IDs found'))
            else:
                self.stdout.write(self.style.WARNING('⚠ QuillJS editor container IDs NOT found'))
            
            # Check template size
            template_size = len(rendered)
            self.stdout.write(self.style.SUCCESS(f'✓ Template rendered successfully - {template_size} characters'))
            
            # Check for console.log statements
            console_logs = rendered.count('console.log')
            if console_logs > 0:
                self.stdout.write(self.style.SUCCESS(f'✓ Found {console_logs} debug console.log statements'))
            
            self.stdout.write(self.style.SUCCESS('=== Template Syntax Test PASSED ==='))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Template rendering failed: {str(e)}'))
            self.stdout.write(self.style.ERROR(f'Traceback:'))
            traceback.print_exc()
            
        # Test a simple edit scenario
        try:
            self.stdout.write('\n=== Testing Edit Question Template ===')
            
            # Try to get an existing question or create one
            question = Question.objects.filter(
                question_type='multiple_choice'
            ).first()
            
            if question:
                form = QuestionForm(instance=question)
                context['form'] = form
                context['question'] = question
                context['is_edit'] = True
                
                rendered_edit = render_to_string(
                    'admin/manage_questions/question_form.html',
                    context,
                    request=request
                )
                
                self.stdout.write(self.style.SUCCESS(f'✓ Edit template rendered successfully - {len(rendered_edit)} characters'))
            else:
                self.stdout.write(self.style.WARNING('⚠ No existing questions found for edit test'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Edit template rendering failed: {str(e)}'))
