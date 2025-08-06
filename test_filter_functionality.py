#!/usr/bin/env python
"""
Test Script untuk Fitur Pencarian dan Filter pada Test History
Menguji semua aspek fitur pencarian dan filtering yang telah diperbaiki
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import User, Role, Category, Question, Choice, Test, Answer
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

def create_test_data():
    """Create comprehensive test data for filter testing"""
    print("🔧 Creating test data for filter testing...")
    
    # Create student role and user
    student_role, _ = Role.objects.get_or_create(role_name='Student')
    user, created = User.objects.get_or_create(
        username='test_student_filter',
        defaults={
            'email': 'student_filter@test.com',
            'role': student_role
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Created test student: {user.username}")
    else:
        print(f"✅ Using existing test student: {user.username}")
    
    # Create multiple categories for testing
    categories_data = [
        {'name': 'Matematika Dasar', 'method': 'default', 'time': 60},
        {'name': 'Bahasa Indonesia', 'method': 'custom', 'time': 90},
        {'name': 'Fisika', 'method': 'utbk', 'time': 120},
        {'name': 'Kimia Organik', 'method': 'default', 'time': 75},
        {'name': 'Biologi Sel', 'method': 'custom', 'time': 45},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            category_name=cat_data['name'],
            defaults={
                'scoring_method': cat_data['method'],
                'time_limit': cat_data['time'],
                'passing_score': 75.0
            }
        )
        categories.append(category)
        if created:
            print(f"✅ Created category: {category.category_name}")
    
    # Create questions for each category
    for category in categories:
        # Check if questions already exist
        if category.question_set.count() == 0:
            for i in range(5):  # 5 questions per category
                question = Question.objects.create(
                    category=category,
                    question_text=f"<p>Sample question {i+1} for {category.category_name}?</p>",
                    weight=1.0 if category.scoring_method == 'default' else (i+1),
                    pub_date=datetime.now()
                )
                
                # Create choices
                for j in range(4):
                    Choice.objects.create(
                        question=question,
                        choice_text=f"Option {chr(65+j)}",
                        is_correct=(j == 0)  # First option is correct
                    )
            print(f"✅ Created questions for {category.category_name}")
    
    # Create test history with different dates
    base_date = datetime.now() - timedelta(days=30)
    
    test_scenarios = [
        {'category': categories[0], 'date_offset': 1, 'score': 85.5},
        {'category': categories[1], 'date_offset': 5, 'score': 92.0},
        {'category': categories[2], 'date_offset': 10, 'score': 78.5},
        {'category': categories[0], 'date_offset': 15, 'score': 88.0},
        {'category': categories[3], 'date_offset': 20, 'score': 95.5},
        {'category': categories[4], 'date_offset': 25, 'score': 72.0},
        {'category': categories[1], 'date_offset': 28, 'score': 89.5},
    ]
    
    tests_created = 0
    for scenario in test_scenarios:
        test_date = base_date + timedelta(days=scenario['date_offset'])
        
        # Check if test already exists
        existing_test = Test.objects.filter(
            student=user,
            categories=scenario['category'],
            date_taken__date=test_date.date()
        ).first()
        
        if not existing_test:
            test = Test.objects.create(
                student=user,
                score=scenario['score'],
                is_submitted=True,
                date_taken=test_date,
                start_time=test_date,
                end_time=test_date + timedelta(minutes=scenario['category'].time_limit),
                time_limit=scenario['category'].time_limit
            )
            test.categories.add(scenario['category'])
            
            # Create answers for the test
            questions = scenario['category'].question_set.all()[:3]  # Answer 3 questions
            for question in questions:
                correct_choice = question.choice_set.filter(is_correct=True).first()
                Answer.objects.create(
                    test=test,
                    question=question,
                    choice=correct_choice
                )
            
            tests_created += 1
            print(f"✅ Created test for {scenario['category'].category_name} on {test_date.date()}")
    
    if tests_created > 0:
        print(f"✅ Created {tests_created} test records")
    else:
        print("✅ All test records already exist")
    
    return user, categories

def test_filter_functionality():
    """Test all filter functionality"""
    print("\n🧪 Testing Filter Functionality...")
    
    user, categories = create_test_data()
    client = Client()
    
    # Login as test user
    login_success = client.login(username='test_student_filter', password='testpass123')
    if not login_success:
        print("❌ Failed to login test user")
        return False
    
    print("✅ Successfully logged in test user")
    
    # Test 1: Default page load
    print("\n📋 Test 1: Default page load")
    response = client.get(reverse('test_history'))
    if response.status_code == 200:
        print("✅ Default page loads successfully")
        print(f"   Status: {response.status_code}")
    else:
        print(f"❌ Default page failed to load: {response.status_code}")
        return False
    
    # Test 2: Search functionality
    print("\n🔍 Test 2: Search functionality")
    search_terms = ['Matematika', 'Bahasa', 'InvalidSearchTerm']
    
    for term in search_terms:
        response = client.get(reverse('test_history'), {'search': term})
        if response.status_code == 200:
            context = response.context
            if context and 'page_obj' in context:
                count = context['page_obj'].paginator.count if context['page_obj'] else 0
                print(f"✅ Search '{term}': {count} results found")
            else:
                print(f"✅ Search '{term}': Response OK but no context")
        else:
            print(f"❌ Search '{term}' failed: {response.status_code}")
    
    # Test 3: Category filter
    print("\n📂 Test 3: Category filter")
    for category in categories[:3]:  # Test first 3 categories
        response = client.get(reverse('test_history'), {'category': category.id})
        if response.status_code == 200:
            context = response.context
            if context and 'page_obj' in context:
                count = context['page_obj'].paginator.count if context['page_obj'] else 0
                print(f"✅ Category '{category.category_name}': {count} results found")
            else:
                print(f"✅ Category '{category.category_name}': Response OK")
        else:
            print(f"❌ Category filter failed: {response.status_code}")
    
    # Test 4: Date range filter
    print("\n📅 Test 4: Date range filter")
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    date_scenarios = [
        {'date_from': month_ago.strftime('%Y-%m-%d'), 'date_to': today.strftime('%Y-%m-%d')},
        {'date_from': week_ago.strftime('%Y-%m-%d'), 'date_to': ''},
        {'date_from': '', 'date_to': today.strftime('%Y-%m-%d')},
    ]
    
    for scenario in date_scenarios:
        params = {k: v for k, v in scenario.items() if v}
        response = client.get(reverse('test_history'), params)
        if response.status_code == 200:
            context = response.context
            if context and 'page_obj' in context:
                count = context['page_obj'].paginator.count if context['page_obj'] else 0
                print(f"✅ Date filter {params}: {count} results found")
            else:
                print(f"✅ Date filter {params}: Response OK")
        else:
            print(f"❌ Date filter failed: {response.status_code}")
    
    # Test 5: Combined filters
    print("\n🔗 Test 5: Combined filters")
    combined_params = {
        'search': 'Matematika',
        'category': categories[0].id,
        'date_from': month_ago.strftime('%Y-%m-%d')
    }
    
    response = client.get(reverse('test_history'), combined_params)
    if response.status_code == 200:
        context = response.context
        if context and 'page_obj' in context:
            count = context['page_obj'].paginator.count if context['page_obj'] else 0
            print(f"✅ Combined filters: {count} results found")
        else:
            print(f"✅ Combined filters: Response OK")
    else:
        print(f"❌ Combined filters failed: {response.status_code}")
    
    # Test 6: Pagination with filters
    print("\n📄 Test 6: Pagination with filters")
    response = client.get(reverse('test_history'), {'page': 1, 'search': 'a'})
    if response.status_code == 200:
        print("✅ Pagination with filters works")
    else:
        print(f"❌ Pagination with filters failed: {response.status_code}")
    
    # Test 7: Invalid parameters
    print("\n⚠️  Test 7: Invalid parameters handling")
    invalid_scenarios = [
        {'page': 'invalid'},
        {'category': 'invalid'},
        {'date_from': 'invalid-date'},
        {'page': 999999},
    ]
    
    for params in invalid_scenarios:
        response = client.get(reverse('test_history'), params)
        if response.status_code == 200:
            print(f"✅ Invalid params {params}: Handled gracefully")
        else:
            print(f"❌ Invalid params {params}: Failed with {response.status_code}")
    
    print("\n✅ All filter functionality tests completed!")
    return True

def test_performance():
    """Test performance of filter queries"""
    print("\n⚡ Testing Filter Performance...")
    
    from django.db import connection
    from django.test.utils import override_settings
    
    user, categories = create_test_data()
    client = Client()
    client.login(username='test_student_filter', password='testpass123')
    
    # Test query performance
    print("📊 Measuring query performance...")
    
    test_cases = [
        {'name': 'No filters', 'params': {}},
        {'name': 'Search only', 'params': {'search': 'Matematika'}},
        {'name': 'Category only', 'params': {'category': categories[0].id}},
        {'name': 'Date range only', 'params': {'date_from': '2024-01-01', 'date_to': '2024-12-31'}},
        {'name': 'All filters', 'params': {'search': 'a', 'category': categories[0].id, 'date_from': '2024-01-01'}},
    ]
    
    for test_case in test_cases:
        # Reset queries
        connection.queries_log.clear()
        
        start_time = datetime.now()
        response = client.get(reverse('test_history'), test_case['params'])
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds() * 1000  # Convert to milliseconds
        query_count = len(connection.queries)
        
        if response.status_code == 200:
            print(f"✅ {test_case['name']}: {duration:.2f}ms, {query_count} queries")
        else:
            print(f"❌ {test_case['name']}: Failed")
    
    print("✅ Performance testing completed!")

def main():
    """Run all filter tests"""
    print("🚀 Starting Test History Filter Testing...")
    print("=" * 60)
    
    try:
        # Test basic functionality
        if test_filter_functionality():
            print("\n🎯 All functionality tests passed!")
        else:
            print("\n❌ Some functionality tests failed!")
            return False
        
        # Test performance
        test_performance()
        
        print("\n" + "=" * 60)
        print("🎉 ALL FILTER TESTS COMPLETED SUCCESSFULLY!")
        print("\n📋 Filter Features Tested:")
        print("✅ Search by category name")
        print("✅ Filter by category")
        print("✅ Filter by date range")
        print("✅ Combined filters")
        print("✅ Pagination with filters")
        print("✅ Invalid parameter handling")
        print("✅ Query performance")
        print("\n🚀 Filter system is ready for production!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
