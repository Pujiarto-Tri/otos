#!/usr/bin/env python
"""Debug script to find questions with images"""

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

def find_questions_with_images():
    """Find questions with images that might be causing the display issue"""
    print("=== Questions with Images ===")
    
    # Find questions with images in the text
    questions = Question.objects.filter(question_text__contains='<img').order_by('id')
    
    print(f"Found {questions.count()} questions with images")
    
    for q in questions:
        print(f"\nQuestion ID: {q.id}")
        print(f"Question Text: {repr(q.question_text[:200])}")
        print(f"Difficulty Coefficient: {q.difficulty_coefficient}")
        print(f"Custom Weight: {q.custom_weight}")
        print("-" * 50)
    
    # Also check for questions with specific text pattern
    print("\n=== Questions with 'perhatikan gambar' ===")
    questions_gambar = Question.objects.filter(question_text__icontains='perhatikan gambar').order_by('id')
    
    for q in questions_gambar:
        print(f"\nQuestion ID: {q.id}")
        print(f"Question Text: {repr(q.question_text[:200])}")
        print(f"Difficulty Coefficient: {q.difficulty_coefficient}")
        print(f"Custom Weight: {q.custom_weight}")
        print("-" * 50)

if __name__ == "__main__":
    find_questions_with_images()