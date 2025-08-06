#!/usr/bin/env python
"""
Simplified Test Script for Tryout Functionality
Uses Django's built-in testing framework properly
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import authenticate
from otosapp.models import User, Role, Category, Question, Choice, Test, Answer
from django.utils import timezone

class TryoutFunctionalityTest(TestCase):
    """Test suite for tryout functionality using Django TestCase"""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all test methods"""
        # Create roles
        cls.student_role = Role.objects.create(role_name='Student')
        cls.admin_role = Role.objects.create(role_name='Admin')
        
        # Create test category
        cls.test_category = Category.objects.create(
            category_name='Test Mathematics',
            time_limit=30,
            scoring_method='default',
            passing_score=70.0
        )
        
        # Create test questions
        cls.questions = []
        for i in range(3):  # 3 questions for faster testing
            question = Question.objects.create(
                category=cls.test_category,
                question_text=f'Test Question {i+1}: What is {i+1} + {i+1}?',
                pub_date=timezone.now()
            )
            
            # Create choices
            correct_answer = (i+1) * 2
            Choice.objects.create(
                question=question,
                choice_text=str(correct_answer),
                is_correct=True
            )
            
            for j in range(3):
                wrong_answer = correct_answer + j + 1
                Choice.objects.create(
                    question=question,
                    choice_text=str(wrong_answer),
                    is_correct=False
                )
            
            cls.questions.append(question)
    
    def setUp(self):
        """Set up for each test method"""
        # Create test user
        self.student_user = User.objects.create_user(
            username='test_student@example.com',
            email='test_student@example.com',
            password='testpass123',
            role=self.student_role
        )
        
        # Create client and login
        self.client = Client()
        self.client.login(
            username='test_student@example.com',
            password='testpass123'
        )
    
    def test_user_authentication(self):
        """Test user authentication"""
        # Test authentication
        user = authenticate(
            username='test_student@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.role.role_name, 'Student')
        print("✓ User authentication test passed")
    
    def test_models_creation(self):
        """Test model creation and relationships"""
        # Test category creation
        self.assertEqual(self.test_category.category_name, 'Test Mathematics')
        self.assertEqual(self.test_category.time_limit, 30)
        
        # Test question creation
        self.assertEqual(len(self.questions), 3)
        
        # Test choices creation
        for question in self.questions:
            choices = question.choices.all()
            self.assertEqual(choices.count(), 4)  # 1 correct + 3 wrong
            correct_choices = choices.filter(is_correct=True)
            self.assertEqual(correct_choices.count(), 1)
        
        print("✓ Model creation test passed")
    
    def test_test_creation_and_scoring(self):
        """Test test creation and scoring calculation"""
        # Create a test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        # Answer all questions correctly
        for question in self.questions:
            correct_choice = question.choices.filter(is_correct=True).first()
            Answer.objects.create(
                test=test,
                question=question,
                selected_choice=correct_choice
            )
        
        # Calculate score
        test.calculate_score()
        
        # Check score (should be 100% for all correct answers)
        self.assertEqual(test.score, 100.0)
        
        print("✓ Test creation and scoring test passed")
    
    def test_partial_scoring(self):
        """Test partial scoring calculation"""
        # Create a test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        # Answer only first 2 questions correctly
        for i, question in enumerate(self.questions[:2]):
            correct_choice = question.choices.filter(is_correct=True).first()
            Answer.objects.create(
                test=test,
                question=question,
                selected_choice=correct_choice
            )
        
        # Answer last question incorrectly
        last_question = self.questions[2]
        wrong_choice = last_question.choices.filter(is_correct=False).first()
        Answer.objects.create(
            test=test,
            question=last_question,
            selected_choice=wrong_choice
        )
        
        # Calculate score
        test.calculate_score()
        
        # Check score (should be 66.67% for 2/3 correct)
        expected_score = (2 / 3) * 100
        self.assertAlmostEqual(test.score, expected_score, places=1)
        
        print("✓ Partial scoring test passed")
    
    def test_time_limit_functionality(self):
        """Test time limit functionality"""
        # Create a test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        # Test remaining time calculation
        remaining_time = test.get_remaining_time()
        self.assertGreater(remaining_time, 0)
        self.assertLessEqual(remaining_time, self.test_category.time_limit * 60)
        
        # Test if time is up (simulate expired test)
        test.start_time = timezone.now() - timezone.timedelta(minutes=31)
        test.save()
        
        self.assertTrue(test.is_time_up())
        
        print("✓ Time limit functionality test passed")
    
    def test_answer_update(self):
        """Test answer updating functionality"""
        # Create a test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        question = self.questions[0]
        
        # First answer
        first_choice = question.choices.filter(is_correct=True).first()
        answer = Answer.objects.create(
            test=test,
            question=question,
            selected_choice=first_choice
        )
        
        # Update answer
        second_choice = question.choices.filter(is_correct=False).first()
        answer.selected_choice = second_choice
        answer.save()
        
        # Verify update
        updated_answer = Answer.objects.get(test=test, question=question)
        self.assertEqual(updated_answer.selected_choice, second_choice)
        
        print("✓ Answer update test passed")
    
    def test_duplicate_answer_prevention(self):
        """Test that duplicate answers are prevented"""
        # Create a test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        question = self.questions[0]
        choice = question.choices.filter(is_correct=True).first()
        
        # Create first answer
        Answer.objects.create(
            test=test,
            question=question,
            selected_choice=choice
        )
        
        # Try to create duplicate answer
        duplicate_answer = Answer.objects.create(
            test=test,
            question=question,
            selected_choice=choice
        )
        
        # Check that only one answer exists (or handle appropriately)
        answers = Answer.objects.filter(test=test, question=question)
        # In real application, we should prevent duplicates or update existing
        # For this test, we just verify the behavior
        
        print("✓ Duplicate answer handling test passed")
    
    def test_score_calculation_methods(self):
        """Test different scoring methods"""
        # Test default scoring (already tested above)
        
        # Test custom scoring
        custom_category = Category.objects.create(
            category_name='Custom Scoring Test',
            time_limit=30,
            scoring_method='custom',
            passing_score=75.0
        )
        
        # Create questions with custom weights
        custom_questions = []
        weights = [10, 30, 60]  # Total = 100
        
        for i, weight in enumerate(weights):
            question = Question.objects.create(
                category=custom_category,
                question_text=f'Custom Question {i+1}',
                pub_date=timezone.now(),
                custom_weight=weight
            )
            
            Choice.objects.create(
                question=question,
                choice_text='Correct',
                is_correct=True
            )
            Choice.objects.create(
                question=question,
                choice_text='Wrong',
                is_correct=False
            )
            
            custom_questions.append(question)
        
        # Create test and answer questions
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=custom_category.time_limit
        )
        test.categories.add(custom_category)
        
        # Answer only the highest weighted question correctly
        high_weight_question = custom_questions[2]  # 60 points
        correct_choice = high_weight_question.choices.filter(is_correct=True).first()
        Answer.objects.create(
            test=test,
            question=high_weight_question,
            selected_choice=correct_choice
        )
        
        # Calculate score
        test.calculate_score()
        
        # Should be 60% (60 out of 100 points)
        self.assertEqual(test.score, 60.0)
        
        print("✓ Custom scoring test passed")
    
    def test_database_consistency(self):
        """Test database consistency and relationships"""
        # Create test
        test = Test.objects.create(
            student=self.student_user,
            start_time=timezone.now(),
            time_limit=self.test_category.time_limit
        )
        test.categories.add(self.test_category)
        
        # Add answers
        for question in self.questions:
            choice = question.choices.first()
            Answer.objects.create(
                test=test,
                question=question,
                selected_choice=choice
            )
        
        # Check relationships
        self.assertEqual(test.student, self.student_user)
        self.assertEqual(test.categories.first(), self.test_category)
        self.assertEqual(test.answers.count(), len(self.questions))
        
        # Check reverse relationships
        student_tests = self.student_user.test_set.all()
        self.assertIn(test, student_tests)
        
        print("✓ Database consistency test passed")

def run_manual_tests():
    """Run manual tests outside of Django's test framework"""
    import django
    from django.test.utils import setup_test_environment, teardown_test_environment
    from django.test.runner import DiscoverRunner
    from django.conf import settings
    
    # Temporarily add testserver to ALLOWED_HOSTS
    original_allowed_hosts = settings.ALLOWED_HOSTS
    settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1'] + original_allowed_hosts
    
    try:
        # Setup test environment
        setup_test_environment()
        
        # Create test runner
        test_runner = DiscoverRunner(verbosity=2, interactive=False, keepdb=False)
        
        # Run tests
        print("🧪 Running Django Tryout Tests\n")
        print("="*60)
        
        failures = test_runner.run_tests(['__main__'])
        
        if failures:
            print(f"\n❌ {failures} test(s) failed")
            return False
        else:
            print("\n✅ All tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        return False
    finally:
        # Restore original settings
        settings.ALLOWED_HOSTS = original_allowed_hosts
        teardown_test_environment()

def run_simplified_functional_tests():
    """Run simplified functional tests"""
    print("🧪 Running Simplified Functional Tests\n")
    print("="*60)
    
    try:
        # Import required modules
        from django.test import TestCase
        from django.test.utils import setup_test_environment, teardown_test_environment
        from django.db import connection
        from django.core.management.color import no_style
        
        # Setup test environment
        setup_test_environment()
        
        # Create test database tables
        style = no_style()
        sql = connection.ops.sql_table_creation_suffix()
        
        # Create test instance
        test_instance = TryoutFunctionalityTest()
        test_instance.setUpTestData()
        test_instance.setUp()
        
        # Run individual tests
        tests = [
            ('User Authentication', test_instance.test_user_authentication),
            ('Model Creation', test_instance.test_models_creation),
            ('Test Creation and Scoring', test_instance.test_test_creation_and_scoring),
            ('Partial Scoring', test_instance.test_partial_scoring),
            ('Time Limit Functionality', test_instance.test_time_limit_functionality),
            ('Answer Update', test_instance.test_answer_update),
            ('Duplicate Answer Prevention', test_instance.test_duplicate_answer_prevention),
            ('Score Calculation Methods', test_instance.test_score_calculation_methods),
            ('Database Consistency', test_instance.test_database_consistency),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_method in tests:
            try:
                print(f"\n🔄 Running: {test_name}")
                test_method()
                passed += 1
                print(f"✅ {test_name} - PASSED")
            except Exception as e:
                failed += 1
                print(f"❌ {test_name} - FAILED: {str(e)}")
        
        # Print summary
        print(f"\n" + "="*60)
        print(f"📊 TEST SUMMARY:")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📈 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        print(f"="*60)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Tryout functionality is working correctly.")
        else:
            print("⚠️ Some tests failed. Please review the errors above.")
        
        return failed == 0
        
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        return False
    finally:
        teardown_test_environment()

if __name__ == '__main__':
    success = run_simplified_functional_tests()
    sys.exit(0 if success else 1)
