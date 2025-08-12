#!/usr/bin/env python
"""
Script untuk membuat kategori UTBK dan soal contoh
"""
import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Category, Question, Choice

def create_utbk_categories():
    """Create UTBK categories"""
    categories_data = [
        {
            'category_name': 'Tes Potensi Skolastik (TPS)',
            'time_limit': 120,  # 2 hours
            'scoring_method': 'utbk',
            'passing_score': 600.0
        },
        {
            'category_name': 'Literasi dalam Bahasa Indonesia',
            'time_limit': 90,  # 1.5 hours
            'scoring_method': 'utbk',
            'passing_score': 500.0
        },
        {
            'category_name': 'Literasi dalam Bahasa Inggris',
            'time_limit': 90,  # 1.5 hours
            'scoring_method': 'utbk',
            'passing_score': 500.0
        },
        {
            'category_name': 'Penalaran Matematika',
            'time_limit': 90,  # 1.5 hours
            'scoring_method': 'utbk',
            'passing_score': 550.0
        },
    ]
    
    created_count = 0
    
    for data in categories_data:
        category, created = Category.objects.get_or_create(
            category_name=data['category_name'],
            defaults=data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created category: {category.category_name}")
        else:
            print(f"⟳ Category exists: {category.category_name}")
    
    print(f"\n🎉 Created {created_count} new categories")
    return Category.objects.filter(scoring_method='utbk')

def create_sample_questions(categories):
    """Create sample questions for each category"""
    sample_questions = {
        'Tes Potensi Skolastik (TPS)': [
            {
                'question_text': 'Jika 2x + 3 = 11, maka nilai x adalah...',
                'choices': [
                    {'text': '2', 'is_correct': False},
                    {'text': '3', 'is_correct': False},
                    {'text': '4', 'is_correct': True},
                    {'text': '5', 'is_correct': False},
                    {'text': '6', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Sinonim dari kata "ELABORASI" adalah...',
                'choices': [
                    {'text': 'Penyederhanaan', 'is_correct': False},
                    {'text': 'Penjelasan detail', 'is_correct': True},
                    {'text': 'Ringkasan', 'is_correct': False},
                    {'text': 'Abstraksi', 'is_correct': False},
                    {'text': 'Generalisasi', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Dalam barisan geometri 2, 6, 18, 54, ..., suku ke-6 adalah...',
                'choices': [
                    {'text': '162', 'is_correct': False},
                    {'text': '324', 'is_correct': False},
                    {'text': '486', 'is_correct': True},
                    {'text': '648', 'is_correct': False},
                    {'text': '972', 'is_correct': False},
                ]
            },
        ],
        'Literasi dalam Bahasa Indonesia': [
            {
                'question_text': 'Gagasan utama dalam paragraf biasanya terdapat pada...',
                'choices': [
                    {'text': 'Kalimat pertama saja', 'is_correct': False},
                    {'text': 'Kalimat terakhir saja', 'is_correct': False},
                    {'text': 'Kalimat pertama atau terakhir', 'is_correct': True},
                    {'text': 'Kalimat tengah', 'is_correct': False},
                    {'text': 'Setiap kalimat', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Konjungsi yang menyatakan hubungan sebab-akibat adalah...',
                'choices': [
                    {'text': 'Tetapi', 'is_correct': False},
                    {'text': 'Karena', 'is_correct': True},
                    {'text': 'Kemudian', 'is_correct': False},
                    {'text': 'Selain itu', 'is_correct': False},
                    {'text': 'Meskipun', 'is_correct': False},
                ]
            },
        ],
        'Literasi dalam Bahasa Inggris': [
            {
                'question_text': 'Choose the correct form: "She _____ to the office every day."',
                'choices': [
                    {'text': 'go', 'is_correct': False},
                    {'text': 'goes', 'is_correct': True},
                    {'text': 'going', 'is_correct': False},
                    {'text': 'gone', 'is_correct': False},
                    {'text': 'went', 'is_correct': False},
                ]
            },
            {
                'question_text': 'What is the synonym of "MAGNIFICENT"?',
                'choices': [
                    {'text': 'Ordinary', 'is_correct': False},
                    {'text': 'Splendid', 'is_correct': True},
                    {'text': 'Simple', 'is_correct': False},
                    {'text': 'Small', 'is_correct': False},
                    {'text': 'Poor', 'is_correct': False},
                ]
            },
        ],
        'Penalaran Matematika': [
            {
                'question_text': 'Jika f(x) = 2x² + 3x - 1, maka f(2) = ...',
                'choices': [
                    {'text': '7', 'is_correct': False},
                    {'text': '9', 'is_correct': False},
                    {'text': '11', 'is_correct': True},
                    {'text': '13', 'is_correct': False},
                    {'text': '15', 'is_correct': False},
                ]
            },
            {
                'question_text': 'Limit dari (x² - 4)/(x - 2) ketika x mendekati 2 adalah...',
                'choices': [
                    {'text': '0', 'is_correct': False},
                    {'text': '2', 'is_correct': False},
                    {'text': '4', 'is_correct': True},
                    {'text': '8', 'is_correct': False},
                    {'text': 'Tidak terdefinisi', 'is_correct': False},
                ]
            },
        ],
    }
    
    created_questions = 0
    
    for category in categories:
        if category.category_name in sample_questions:
            questions_data = sample_questions[category.category_name]
            
            for q_data in questions_data:
                # Check if question already exists
                existing = Question.objects.filter(
                    category=category,
                    question_text=q_data['question_text']
                ).first()
                
                if existing:
                    print(f"  → Question exists: {q_data['question_text'][:50]}...")
                    continue
                
                # Create question
                question = Question.objects.create(
                    category=category,
                    question_text=q_data['question_text'],
                    pub_date=datetime.now(),
                    difficulty_coefficient=1.0  # Will be calculated later
                )
                
                # Create choices
                for choice_data in q_data['choices']:
                    Choice.objects.create(
                        question=question,
                        choice_text=choice_data['text'],
                        is_correct=choice_data['is_correct']
                    )
                
                created_questions += 1
                print(f"  ✓ Created question: {q_data['question_text'][:50]}...")
    
    print(f"\n🎉 Created {created_questions} sample questions")
    
    # Update UTBK coefficients for all categories
    for category in categories:
        print(f"📊 Updating UTBK coefficients for {category.category_name}...")
        # Since we don't have test data yet, set default coefficients
        questions = Question.objects.filter(category=category)
        total_questions = questions.count()
        
        if total_questions > 0:
            # Set equal coefficients that sum to 1000
            coefficient_per_question = 1000 / total_questions
            for question in questions:
                question.difficulty_coefficient = coefficient_per_question
                question.save()
            print(f"  → Set coefficient {coefficient_per_question:.2f} for {total_questions} questions")

if __name__ == '__main__':
    print("🚀 Creating UTBK categories and sample questions...\n")
    
    # Create categories
    categories = create_utbk_categories()
    
    # Create sample questions
    if categories:
        print("\n📝 Creating sample questions...")
        create_sample_questions(categories)
    
    print("\n✅ Setup complete! You can now:")
    print("1. Visit admin panel to manage universities")
    print("2. Create student accounts and set university targets")
    print("3. Take UTBK tests to get university recommendations")
    print("4. View university recommendations based on scores")
