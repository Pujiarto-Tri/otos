#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test
from django.db.models import Count

print("=== DEBUG DUPLICATE TESTS ===")

# Find tests with same student and date_taken
duplicates = Test.objects.values('student', 'date_taken').annotate(
    count=Count('id')
).filter(count__gt=1)

print(f"Found {duplicates.count()} groups of duplicate tests")

for dup in duplicates:
    student_id = dup['student']
    date_taken = dup['date_taken']
    count = dup['count']
    
    print(f"\nStudent ID: {student_id}, Date: {date_taken}, Count: {count}")
    
    # Get all tests for this student/date
    tests = Test.objects.filter(
        student_id=student_id,
        date_taken=date_taken
    ).order_by('-score', '-id')  # Keep the one with highest score, or newest
    
    for i, test in enumerate(tests):
        print(f"  Test {i+1}: ID={test.id}, Score={test.score}, Submitted={test.is_submitted}")
        
    # Keep only the first one (highest score/newest), delete the rest
    if tests.count() > 1:
        keep_test = tests.first()
        delete_tests = tests.exclude(id=keep_test.id)
        print(f"  KEEPING: Test ID {keep_test.id} (Score: {keep_test.score})")
        print(f"  DELETING: {delete_tests.count()} duplicate tests")
        
        # Uncomment the line below to actually delete duplicates
        # delete_tests.delete()

print("\n=== DUPLICATE CLEANUP SIMULATION COMPLETE ===")
print("To actually delete duplicates, uncomment the delete line in the script")
