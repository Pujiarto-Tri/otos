"""Simulate posting answers to a package test's question endpoints using Django test client.
This script will:
- login as a known student user
- ensure a package test exists (create if none)
- iterate over package questions and POST choice ids to the question URL using the test client
- print responses and final Answer counts for the test

Run with: python inspect_post_simulate.py
"""
import os
import django
import sys

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import TryoutPackage, Test, Question, Choice, Answer
from django.utils import timezone

User = get_user_model()

EMAIL = 'student@brainest.com'
PASSWORD = 'student123'  # assumption: known test account; if not, will attempt to find and bypass login

client = Client()

try:
    logged_in = client.login(email=EMAIL, password=PASSWORD)
except Exception as e:
    print('Login attempt failed:', e)
    logged_in = False

user = User.objects.filter(email=EMAIL).first()
if not user:
    print('User not found:', EMAIL)
    sys.exit(1)

print('Logged in via test client?', logged_in)

package = TryoutPackage.objects.first()
if not package:
    print('No TryoutPackage found in DB')
    sys.exit(1)

# Ensure there's an unsubmitted test for this user and package
test = Test.objects.filter(student=user, tryout_package=package, is_submitted=False).first()
if not test:
    print('No existing unsubmitted test found. Creating one...')
    test = Test.objects.create(student=user, tryout_package=package, start_time=timezone.now(), time_limit=package.total_time)
    for pc in package.tryoutpackagecategory_set.all():
        test.categories.add(pc.category)

print('Using Test id', test.id)

# Build ordered question list similar to view
all_questions = []
for pc in package.tryoutpackagecategory_set.all().order_by('order'):
    qs = list(Question.objects.filter(category=pc.category).order_by('id'))
    all_questions.extend(qs)

print('Total questions in package:', len(all_questions))

# For each question, pick first choice and POST as AJAX
for idx, q in enumerate(all_questions, start=1):
    choices = q.choices.all()
    if not choices:
        print('Question', q.id, 'has no choices')
        continue
    choice = choices.first()
    url = f'/students/tryouts/package/{package.id}/question/{idx}/'
    print('POSTing to', url, 'choice', choice.id)
    resp = client.post(url, {'choice': str(choice.id)}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    print('Status code:', resp.status_code)
    try:
        print('JSON:', resp.json())
    except Exception as e:
        print('Response content:', resp.content[:200])

# Final tally
answers = Answer.objects.filter(test=test)
print('Total answers saved for test', test.id, answers.count())
for a in answers:
    print('Answer', a.id, 'Q', a.question_id, 'Choice', a.selected_choice_id)

print('Done')
