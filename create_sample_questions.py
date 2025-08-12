#!/usr/bin/env python
"""
Script untuk membuat contoh questions untuk testing fitur pencarian dan filter
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Category, Question, Choice
from django.contrib.auth import get_user_model

User = get_user_model()

def create_sample_questions():
    """Create sample questions for testing"""
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'role': 'admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Get first category
    category = Category.objects.first()
    if not category:
        print("No categories found! Please create categories first.")
        return
    
    print(f"Creating sample questions for category: {category.category_name}")
    
    # Sample questions data
    sample_questions = [
        {
            'text': 'Apa yang dimaksud dengan fotosintesis dalam biologi?',
            'choices': [
                ('Proses pembuatan makanan oleh tumbuhan menggunakan cahaya matahari', True),
                ('Proses respirasi pada tumbuhan', False),
                ('Proses reproduksi pada tumbuhan', False),
                ('Proses penyerapan air oleh akar', False),
            ],
            'weight': 2.5,
            'coefficient': 0.8
        },
        {
            'text': 'Dalam matematika, berapa hasil dari 2x + 5 = 15?',
            'choices': [
                ('x = 5', True),
                ('x = 10', False),
                ('x = 7', False),
                ('x = 3', False),
            ],
            'weight': 3.0,
            'coefficient': 0.6
        },
        {
            'text': 'Siapa penemu teori relativitas?',
            'choices': [
                ('Albert Einstein', True),
                ('Isaac Newton', False),
                ('Galileo Galilei', False),
                ('Charles Darwin', False),
            ],
            'weight': 2.0,
            'coefficient': 0.7
        },
        {
            'text': 'Apa ibu kota Indonesia?',
            'choices': [
                ('Jakarta', True),
                ('Surabaya', False),
                ('Bandung', False),
                ('Medan', False),
            ],
            'weight': 1.5,
            'coefficient': 0.9
        },
        {
            'text': 'Dalam kimia, apa simbol untuk unsur emas?',
            'choices': [
                ('Au', True),
                ('Ag', False),
                ('Al', False),
                ('As', False),
            ],
            'weight': 0,  # No weight for testing filter
            'coefficient': 0.5
        },
        {
            'text': 'Berapa jumlah provinsi di Indonesia saat ini?',
            'choices': [
                ('34 provinsi', True),
                ('33 provinsi', False),
                ('35 provinsi', False),
                ('32 provinsi', False),
            ],
            'weight': 2.8,
            'coefficient': 0.4
        },
        {
            'text': 'Apa gas yang paling banyak di atmosfer bumi?',
            'choices': [
                ('Nitrogen', True),
                ('Oksigen', False),
                ('Karbon dioksida', False),
                ('Argon', False),
            ],
            'weight': 0,  # No weight for testing filter
            'coefficient': 0.6
        },
        {
            'text': 'Siapa presiden pertama Indonesia?',
            'choices': [
                ('Soekarno', True),
                ('Soeharto', False),
                ('Habibie', False),
                ('Megawati', False),
            ],
            'weight': 3.5,
            'coefficient': 0.8
        }
    ]
    
    # Create questions with different dates
    base_date = datetime.now() - timedelta(days=30)
    
    for i, q_data in enumerate(sample_questions):
        # Create question with different dates
        pub_date = base_date + timedelta(days=i*4)
        
        question = Question.objects.create(
            question_text=q_data['text'],
            pub_date=pub_date,
            category=category,
            custom_weight=q_data['weight'],
            difficulty_coefficient=q_data['coefficient']
        )
        
        # Create choices
        for choice_text, is_correct in q_data['choices']:
            Choice.objects.create(
                question=question,
                choice_text=choice_text,
                is_correct=is_correct
            )
        
        print(f"Created question: {q_data['text'][:50]}...")
    
    print(f"\n✅ Successfully created {len(sample_questions)} sample questions!")
    print(f"📊 Questions with custom weight: {len([q for q in sample_questions if q['weight'] > 0])}")
    print(f"📊 Questions without custom weight: {len([q for q in sample_questions if q['weight'] == 0])}")

if __name__ == '__main__':
    create_sample_questions()
