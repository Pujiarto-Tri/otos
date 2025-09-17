#!/usr/bin/env python
"""Debug script to get full question text for specific question"""

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

def get_full_question_171():
    """Get full question text for question 171"""
    try:
        q = Question.objects.get(id=171)
        print(f"Question ID: {q.id}")
        print(f"Full Question Text: {repr(q.question_text)}")
        print(f"Difficulty Coefficient: {q.difficulty_coefficient}")
        print(f"Custom Weight: {q.custom_weight}")
        print(f"Text Length: {len(q.question_text) if q.question_text else 0}")
        
        # Check if there are any weird characters or patterns
        if "1.0" in q.question_text:
            print("WARNING: '1.0' found in question text!")
            
        # Show characters around any digits
        text = q.question_text
        import re
        for match in re.finditer(r'\d+\.\d+', text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            print(f"Found number pattern: ...{text[start:end]}...")
            
    except Question.DoesNotExist:
        print("Question 171 not found")

if __name__ == "__main__":
    get_full_question_171()