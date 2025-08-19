#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test, Answer, User, Category, TryoutPackage
from django.utils import timezone
from datetime import timedelta
from django.db.models import Max, Q

print("=== COMPLETE TEACHER VIEW DEBUG ===")

# Check the exact category we're looking at
try:
    category_41 = Category.objects.get(id=41)
    print(f"\nCategory 41: {category_41.category_name}")
    
    # This is the EXACT query from the teacher view
    print(f"\n=== REPRODUCING TEACHER VIEW QUERY ===")
    
    # Get tests for this category - exactly like in the teacher view
    tests_in_category = Test.objects.filter(
        categories=category_41,
        is_submitted=True
    ).select_related('student').prefetch_related('categories').order_by('-date_taken')
    
    print(f"Raw query result count: {tests_in_category.count()}")
    
    # Show all tests for this category
    for test in tests_in_category:
        print(f"  Test {test.id}: {test.student.username} - Score: {test.score} - Date: {test.date_taken}")
    
    # Now apply the aggregation logic like in the teacher view
    # Get the latest test per student
    print(f"\n=== APPLYING TEACHER VIEW AGGREGATION ===")
    
    # This mimics the teacher_view_student_scores logic
    students_with_tests = Test.objects.filter(
        categories=category_41,
        is_submitted=True
    ).values('student').annotate(
        latest_date=Max('date_taken')
    ).values('student', 'latest_date')
    
    print(f"Students with tests: {len(students_with_tests)}")
    
    # Get the actual latest tests
    latest_tests = []
    for item in students_with_tests:
        latest_test = Test.objects.filter(
            student_id=item['student'],
            categories=category_41,
            is_submitted=True,
            date_taken=item['latest_date']
        ).first()
        if latest_test:
            latest_tests.append(latest_test)
    
    print(f"Latest tests found: {len(latest_tests)}")
    for test in latest_tests:
        print(f"  Latest Test {test.id}: {test.student.username} - Score: {test.score} - Date: {test.date_taken}")
    
    # Check specific test 243
    print(f"\n=== CHECKING TEST 243 SPECIFICALLY ===")
    try:
        test_243 = Test.objects.get(id=243)
        print(f"Test 243 exists: {test_243.student.username}")
        print(f"Is submitted: {test_243.is_submitted}")
        print(f"Categories: {[cat.category_name for cat in test_243.categories.all()]}")
        print(f"Is in category 41: {category_41 in test_243.categories.all()}")
        
        # Check if it would be the latest for this student
        student_tests = Test.objects.filter(
            student=test_243.student,
            categories=category_41,
            is_submitted=True
        ).order_by('-date_taken')
        
        print(f"All tests for this student in category 41:")
        for test in student_tests:
            print(f"  Test {test.id}: Score {test.score} - Date: {test.date_taken} {'<-- LATEST' if test.id == test_243.id else ''}")
            
    except Test.DoesNotExist:
        print("Test 243 not found!")
        
    # Check for any permission/user issues
    print(f"\n=== CHECKING USER PERMISSIONS ===")
    teachers = User.objects.filter(userprofile__role__role_name='Teacher')
    print(f"Teachers in system: {teachers.count()}")
    for teacher in teachers:
        print(f"  Teacher: {teacher.username}")

except Category.DoesNotExist:
    print("Category 41 not found!")

# Final check - show exactly what the teacher view URL would return
print(f"\n=== SIMULATING TEACHER VIEW URL ===")
print("URL: /teacher/categories/41/scores/")

# Check if there are any recent changes that might not be visible
print(f"\n=== CHECKING FOR TIMING ISSUES ===")
now = timezone.now()
five_minutes_ago = now - timedelta(minutes=5)

recent_tests = Test.objects.filter(
    date_taken__gte=five_minutes_ago,
    is_submitted=True
).order_by('-date_taken')

print(f"Tests submitted in last 5 minutes: {recent_tests.count()}")
for test in recent_tests:
    categories = [cat.category_name for cat in test.categories.all()]
    print(f"  Test {test.id}: {test.student.username} - Categories: {categories} - Score: {test.score}")
