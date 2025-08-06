#!/usr/bin/env python
"""
Simple Tryout Functionality Test
Tests core business logic and model functionality
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import User, Role, Category, Question, Choice, Test, Answer
from django.utils import timezone
from django.db import transaction

class SimpleTryoutTest:
    def __init__(self):
        print("🧪 Simple Tryout Functionality Test")
        print("="*50)
        self.setup_test_data()
    
    def setup_test_data(self):
        """Setup basic test data"""
        print("\n📋 Setting up test data...")
        
        # Cleanup any existing test data
        self.cleanup()
        
        # Create role
        self.student_role, created = Role.objects.get_or_create(role_name='Student')
        if created:
            print("✓ Created Student role")
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='simple_test_user@example.com',
            email='simple_test_user@example.com',
            password='test123',
            role=self.student_role
        )
        print("✓ Created test user")
        
        # Create test category
        self.test_category = Category.objects.create(
            category_name='Simple Test Category',
            time_limit=30,
            scoring_method='default',
            passing_score=70.0
        )
        print("✓ Created test category")
        
        # Create test questions
        self.questions = []
        for i in range(3):
            question = Question.objects.create(
                category=self.test_category,
                question_text=f'Question {i+1}: What is 2 + {i+1}?',
                pub_date=timezone.now()
            )
            
            # Correct answer
            correct_answer = 2 + (i + 1)
            Choice.objects.create(
                question=question,
                choice_text=str(correct_answer),
                is_correct=True
            )
            
            # Wrong answers
            for j in range(3):
                wrong_answer = correct_answer + j + 1
                Choice.objects.create(
                    question=question,
                    choice_text=str(wrong_answer),
                    is_correct=False
                )
            
            self.questions.append(question)
        
        print(f"✓ Created {len(self.questions)} test questions")
        print("✓ Test data setup complete\n")
    
    def test_basic_model_creation(self):
        """Test basic model creation and relationships"""
        print("1️⃣ Testing Basic Model Creation...")
        
        try:
            # Test user creation
            assert self.test_user.email == 'simple_test_user@example.com'
            assert self.test_user.role.role_name == 'Student'
            print("  ✓ User model working correctly")
            
            # Test category creation
            assert self.test_category.category_name == 'Simple Test Category'
            assert self.test_category.time_limit == 30
            print("  ✓ Category model working correctly")
            
            # Test question and choice creation
            assert len(self.questions) == 3
            for question in self.questions:
                choices = question.choices.all()
                assert choices.count() == 4  # 1 correct + 3 wrong
                correct_choices = choices.filter(is_correct=True)
                assert correct_choices.count() == 1
            print("  ✓ Question and Choice models working correctly")
            
            print("  ✅ Basic model creation test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Basic model creation test FAILED: {str(e)}\n")
            return False
    
    def test_test_creation_and_scoring(self):
        """Test test creation and score calculation"""
        print("2️⃣ Testing Test Creation and Scoring...")
        
        try:
            # Create a test
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=self.test_category.time_limit
            )
            test.categories.add(self.test_category)
            print("  ✓ Test object created")
            
            # Answer all questions correctly
            for question in self.questions:
                correct_choice = question.choices.filter(is_correct=True).first()
                Answer.objects.create(
                    test=test,
                    question=question,
                    selected_choice=correct_choice
                )
            print("  ✓ All answers submitted correctly")
            
            # Calculate score
            test.calculate_score()
            print(f"  ✓ Score calculated: {test.score}%")
            
            # Verify perfect score
            assert test.score == 100.0, f"Expected 100%, got {test.score}%"
            print("  ✓ Perfect score verification passed")
            
            # Test submission
            test.is_submitted = True
            test.end_time = timezone.now()
            test.save()
            assert test.is_submitted == True
            print("  ✓ Test submission working")
            
            print("  ✅ Test creation and scoring test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Test creation and scoring test FAILED: {str(e)}\n")
            return False
    
    def test_partial_scoring(self):
        """Test partial scoring calculation"""
        print("3️⃣ Testing Partial Scoring...")
        
        try:
            # Create another test
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=self.test_category.time_limit
            )
            test.categories.add(self.test_category)
            
            # Answer only 2 out of 3 questions correctly
            for i, question in enumerate(self.questions):
                if i < 2:  # First 2 questions correct
                    choice = question.choices.filter(is_correct=True).first()
                else:  # Last question wrong
                    choice = question.choices.filter(is_correct=False).first()
                
                Answer.objects.create(
                    test=test,
                    question=question,
                    selected_choice=choice
                )
            
            print("  ✓ Answered 2/3 questions correctly")
            
            # Calculate score
            test.calculate_score()
            
            # Should be 66.67% (2/3 * 100)
            expected_score = (2 / 3) * 100
            assert abs(test.score - expected_score) < 0.1, f"Expected {expected_score:.1f}%, got {test.score}%"
            print(f"  ✓ Partial score calculated correctly: {test.score:.1f}%")
            
            print("  ✅ Partial scoring test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Partial scoring test FAILED: {str(e)}\n")
            return False
    
    def test_time_functionality(self):
        """Test time-related functionality"""
        print("4️⃣ Testing Time Functionality...")
        
        try:
            # Create test with current time
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=30  # 30 minutes
            )
            test.categories.add(self.test_category)
            
            # Test remaining time calculation
            remaining_time = test.get_remaining_time()
            assert remaining_time > 0, "Remaining time should be positive"
            assert remaining_time <= 30 * 60, "Remaining time shouldn't exceed time limit"
            print(f"  ✓ Remaining time calculated: {remaining_time} seconds")
            
            # Test if time is not up yet
            assert not test.is_time_up(), "Test should not be timed out yet"
            print("  ✓ Time up check working (not expired)")
            
            # Simulate expired test
            test.start_time = timezone.now() - timedelta(minutes=31)  # 31 minutes ago
            test.save()
            
            assert test.is_time_up(), "Test should be timed out"
            print("  ✓ Time up check working (expired)")
            
            print("  ✅ Time functionality test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Time functionality test FAILED: {str(e)}\n")
            return False
    
    def test_custom_scoring(self):
        """Test custom scoring functionality"""
        print("5️⃣ Testing Custom Scoring...")
        
        try:
            # Create custom scoring category
            custom_category = Category.objects.create(
                category_name='Custom Scoring Category',
                time_limit=45,
                scoring_method='custom',
                passing_score=75.0
            )
            
            # Create questions with different weights
            custom_questions = []
            weights = [20, 30, 50]  # Total = 100
            
            for i, weight in enumerate(weights):
                question = Question.objects.create(
                    category=custom_category,
                    question_text=f'Custom Question {i+1}',
                    pub_date=timezone.now(),
                    custom_weight=weight
                )
                
                # Add choices
                Choice.objects.create(
                    question=question,
                    choice_text='Correct Answer',
                    is_correct=True
                )
                Choice.objects.create(
                    question=question,
                    choice_text='Wrong Answer',
                    is_correct=False
                )
                
                custom_questions.append(question)
            
            print("  ✓ Created custom scoring questions with weights: 20, 30, 50")
            
            # Create test
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=custom_category.time_limit
            )
            test.categories.add(custom_category)
            
            # Answer only the highest weighted question (50 points)
            highest_weight_question = custom_questions[2]
            correct_choice = highest_weight_question.choices.filter(is_correct=True).first()
            Answer.objects.create(
                test=test,
                question=highest_weight_question,
                selected_choice=correct_choice
            )
            
            # Calculate score
            test.calculate_score()
            
            # Should be 50% (50 out of 100 points)
            assert test.score == 50.0, f"Expected 50%, got {test.score}%"
            print(f"  ✓ Custom scoring calculated correctly: {test.score}%")
            
            print("  ✅ Custom scoring test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Custom scoring test FAILED: {str(e)}\n")
            return False
    
    def test_answer_management(self):
        """Test answer creation and updating"""
        print("6️⃣ Testing Answer Management...")
        
        try:
            # Create test
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=30
            )
            test.categories.add(self.test_category)
            
            question = self.questions[0]
            
            # Create initial answer
            initial_choice = question.choices.filter(is_correct=False).first()
            answer = Answer.objects.create(
                test=test,
                question=question,
                selected_choice=initial_choice
            )
            print("  ✓ Initial answer created")
            
            # Update answer
            new_choice = question.choices.filter(is_correct=True).first()
            answer.selected_choice = new_choice
            answer.save()
            
            # Verify update
            updated_answer = Answer.objects.get(test=test, question=question)
            assert updated_answer.selected_choice == new_choice
            print("  ✓ Answer updated successfully")
            
            # Test answer relationships
            assert answer.test == test
            assert answer.question == question
            print("  ✓ Answer relationships verified")
            
            print("  ✅ Answer management test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Answer management test FAILED: {str(e)}\n")
            return False
    
    def test_database_integrity(self):
        """Test database integrity and relationships"""
        print("7️⃣ Testing Database Integrity...")
        
        try:
            # Create test with multiple answers
            test = Test.objects.create(
                student=self.test_user,
                start_time=timezone.now(),
                time_limit=30
            )
            test.categories.add(self.test_category)
            
            # Add answers for all questions
            for question in self.questions:
                choice = question.choices.first()
                Answer.objects.create(
                    test=test,
                    question=question,
                    selected_choice=choice
                )
            
            # Test forward relationships
            assert test.student == self.test_user
            assert test.categories.first() == self.test_category
            assert test.answers.count() == len(self.questions)
            print("  ✓ Forward relationships verified")
            
            # Test reverse relationships
            user_tests = Test.objects.filter(student=self.test_user)
            assert test in user_tests
            print("  ✓ Reverse relationships verified")
            
            # Test category questions
            category_questions = self.test_category.question_set.all()
            assert set(category_questions) == set(self.questions)
            print("  ✓ Category-question relationships verified")
            
            # Test cascade behavior (cleanup)
            test_id = test.id
            answer_count_before = Answer.objects.filter(test_id=test_id).count()
            assert answer_count_before > 0
            
            test.delete()
            answer_count_after = Answer.objects.filter(test_id=test_id).count()
            assert answer_count_after == 0
            print("  ✓ Cascade deletion working")
            
            print("  ✅ Database integrity test PASSED\n")
            return True
            
        except Exception as e:
            print(f"  ❌ Database integrity test FAILED: {str(e)}\n")
            return False
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("🚀 Starting Simple Tryout Tests...\n")
        
        tests = [
            self.test_basic_model_creation,
            self.test_test_creation_and_scoring,
            self.test_partial_scoring,
            self.test_time_functionality,
            self.test_custom_scoring,
            self.test_answer_management,
            self.test_database_integrity
        ]
        
        passed = 0
        failed = 0
        
        for test_method in tests:
            try:
                if test_method():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                print(f"❌ {test_method.__name__} FAILED with exception: {str(e)}\n")
        
        # Print final summary
        print("="*60)
        print("📊 FINAL TEST SUMMARY")
        print("="*60)
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📈 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        print("="*60)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Core tryout functionality is working correctly")
            print("✅ Models, scoring, and timing functions are operational")
            print("✅ Database relationships are properly configured")
        else:
            print("⚠️ Some tests failed")
            print("🔧 Please review the failed tests above")
        
        return failed == 0
    
    def cleanup(self):
        """Clean up test data"""
        try:
            # Delete in proper order to avoid foreign key constraints
            Answer.objects.filter(test__student__email='simple_test_user@example.com').delete()
            Test.objects.filter(student__email='simple_test_user@example.com').delete()
            User.objects.filter(email='simple_test_user@example.com').delete()
            
            # Clean up questions and choices
            Choice.objects.filter(question__category__category_name__contains='Test Category').delete()
            Question.objects.filter(category__category_name__contains='Test Category').delete()
            Category.objects.filter(category_name__contains='Test Category').delete()
            
        except Exception as e:
            print(f"Cleanup warning: {str(e)}")

def main():
    """Main function"""
    tester = SimpleTryoutTest()
    
    try:
        success = tester.run_all_tests()
        return success
    except Exception as e:
        print(f"❌ Test suite failed with error: {str(e)}")
        return False
    finally:
        print("\n🧹 Cleaning up test data...")
        tester.cleanup()
        print("✓ Cleanup completed")

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
