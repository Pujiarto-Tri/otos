#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test, Answer, User, Category, TryoutPackage

print("=== CHECKING CATEGORY 41 ===")

# Check if category 41 exists and what it is
try:
    category_41 = Category.objects.get(id=41)
    print(f"Category 41: {category_41.category_name}")
    print(f"Created by: {category_41.created_by}")
    
    # Check tests in this category
    tests_in_category = Test.objects.filter(categories=category_41, is_submitted=True).order_by('-date_taken')
    print(f"\nSubmitted tests in category 41: {tests_in_category.count()}")
    
    for test in tests_in_category[:5]:
        print(f"  Test {test.id}: {test.student.username} - Score: {test.score} - Date: {test.date_taken}")
        
    # Check test 243 specifically
    test_243 = Test.objects.get(id=243)
    print(f"\n=== TEST 243 CATEGORY CHECK ===")
    print(f"Test 243 categories:")
    for cat in test_243.categories.all():
        print(f"  - Category {cat.id}: {cat.category_name}")
        
    # Check if test 243 is in category 41
    is_in_category = test_243.categories.filter(id=41).exists()
    print(f"Test 243 is in category 41: {is_in_category}")
    
except Category.DoesNotExist:
    print("Category 41 not found!")
except Test.DoesNotExist:
    print("Test 243 not found!")

# Also check what the teacher view query would return
from django.db.models import Q, Count, Max

print(f"\n=== SIMULATING TEACHER VIEW QUERY ===")
try:
    category = Category.objects.get(id=41)
    
    # Exact same query as in the teacher view
    tests_qs = Test.objects.filter(
        categories=category, 
        is_submitted=True
    ).select_related('student').distinct()
    
    print(f"Tests found by teacher view query: {tests_qs.count()}")
    
    # Group by student and get only the latest test per student
    latest_test_dates = tests_qs.values('student').annotate(
        latest_date=Max('date_taken')
    ).values_list('student', 'latest_date')
    
    print(f"Latest test dates: {list(latest_test_dates)}")
    
    # Filter to only include the latest test per student
    latest_tests_filter = Q()
    for student_id, latest_date in latest_test_dates:
        latest_tests_filter |= Q(student_id=student_id, date_taken=latest_date)
    
    final_tests = tests_qs.filter(latest_tests_filter)
    print(f"Final tests after filtering: {final_tests.count()}")
    
    for test in final_tests:
        print(f"  Test {test.id}: {test.student.username} - Score: {test.score} - Date: {test.date_taken}")
        
except Exception as e:
    print(f"Error: {e}")
