#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test, Answer, User, Category, TryoutPackage
from django.utils import timezone
from datetime import timedelta

print("=== DEBUGGING RECENT TEST DATA ===")

# Check the most recent tests
recent_tests = Test.objects.order_by('-date_taken')[:10]
print(f"\nMost recent 10 tests:")
for test in recent_tests:
    tryout_name = test.tryout_package.package_name if test.tryout_package else "No Package"
    categories = ", ".join([cat.category_name for cat in test.categories.all()]) if test.categories.exists() else "No Categories"
    print(f"Test ID: {test.id}, User: {test.student.username}, Package: {tryout_name}, Categories: {categories}, Score: {test.score}, Submitted: {test.is_submitted}, Date: {test.date_taken}")

# Check test ID 243 specifically (from the logs)
try:
    test_243 = Test.objects.get(id=243)
    print(f"\n=== TEST 243 DETAILS ===")
    print(f"User: {test_243.student.username}")
    print(f"Package: {test_243.tryout_package.package_name if test_243.tryout_package else 'None'}")
    print(f"Categories: {', '.join([cat.category_name for cat in test_243.categories.all()])}")
    print(f"Score: {test_243.score}")
    print(f"Submitted: {test_243.is_submitted}")
    print(f"Date taken: {test_243.date_taken}")
    print(f"Answers count: {test_243.answers.count()}")
    
    # Check answers
    answers = Answer.objects.filter(test=test_243)
    print(f"\nAnswers for test 243:")
    for answer in answers:
        choice_text = answer.selected_choice.choice_text if answer.selected_choice else "None"
        print(f"  Question {answer.question.id}: Choice: {choice_text}, Text: {answer.text_answer}, Type: {answer.question.question_type}")
        
except Test.DoesNotExist:
    print("Test 243 not found!")

# Check for any tests with tryout packages
tryout_tests = Test.objects.filter(tryout_package__isnull=False).order_by('-date_taken')[:5]
print(f"\n=== RECENT TRYOUT PACKAGE TESTS ===")
for test in tryout_tests:
    print(f"Test {test.id}: {test.student.username} - Package: {test.tryout_package.package_name} - Score: {test.score} - Submitted: {test.is_submitted} - Date: {test.date_taken}")

# Check for any tests submitted in the last hour
one_hour_ago = timezone.now() - timedelta(hours=1)
recent_hour_tests = Test.objects.filter(date_taken__gte=one_hour_ago).order_by('-date_taken')
print(f"\nTests submitted in the last hour: {recent_hour_tests.count()}")
for test in recent_hour_tests:
    tryout_name = test.tryout_package.package_name if test.tryout_package else "No Package"
    print(f"  Test {test.id}: {test.student.username} - Package: {tryout_name} - Score: {test.score} - Submitted: {test.is_submitted}")

# Check specifically for any tests that might be in the teacher view
print(f"\n=== CHECKING TEACHER VIEW LOGIC ===")
# This is similar to what the teacher view would show
submitted_tests = Test.objects.filter(is_submitted=True).order_by('-date_taken')[:10]
print(f"Recently submitted tests (what teacher should see): {submitted_tests.count()}")
for test in submitted_tests:
    tryout_name = test.tryout_package.package_name if test.tryout_package else "No Package"
    categories = ", ".join([cat.category_name for cat in test.categories.all()]) if test.categories.exists() else "No Categories"
    print(f"  Test {test.id}: {test.student.username} - Package: {tryout_name} - Categories: {categories} - Score: {test.score} - Date: {test.date_taken}")
