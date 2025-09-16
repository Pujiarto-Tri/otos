#!/usr/bin/env python
"""Debug script to inspect question data"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Setup Django
django.setup()

from otosapp.models import Question

def debug_questions():
    """Debug questions to find the data issue"""
    print("=== Debugging Questions ===")
    
    # Get first few questions to see the data
    questions = Question.objects.all().order_by('id')[:5]
    
    for q in questions:
        print(f"\nQuestion ID: {q.id}")
        print(f"Question Text: {repr(q.question_text)}")
        print(f"Difficulty Coefficient: {q.difficulty_coefficient}")
        print(f"Custom Weight: {q.custom_weight}")
        print(f"Question Text Length: {len(q.question_text) if q.question_text else 0}")
        print("-" * 50)

if __name__ == "__main__":
    debug_questions()