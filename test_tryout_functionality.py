#!/usr/bin/env python
"""
Comprehensive Test Script for Student Tryout Functionality
Tests all aspects of the tryout process including:
- User authentication and permissions
- Test session management
- Question navigation
- Answer saving and updating
- Time management
- Test submission
- Score calculation
- Results display
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import User, Role, Category, Question, Choice, Test, Answer
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

class TryoutTestSuite:
    def __init__(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.setup_test_data()
        print("=== Comprehensive Tryout Testing Suite ===\n")
    
    def setup_test_data(self):
        """Setup test data including users, categories, questions, and choices"""
        print("Setting up test data...")
        
        # Create roles
        self.student_role, _ = Role.objects.get_or_create(role_name='Student')
        self.admin_role, _ = Role.objects.get_or_create(role_name='Admin')
        
        # Create test users
        self.student_user = User.objects.create_user(
            username='test_student@example.com',
            email='test_student@example.com',
            password='testpass123',
            role=self.student_role
        )
        
        self.admin_user = User.objects.create_user(
            username='test_admin@example.com',
            email='test_admin@example.com',
            password='testpass123',
            role=self.admin_role,
            is_staff=True
        )
        
        # Create test category
        self.test_category = Category.objects.create(
            category_name='Test Mathematics',
            time_limit=30,  # 30 minutes
            scoring_method='default',
            passing_score=70.0
        )
        
        # Create test questions and choices
        self.questions = []
        for i in range(5):
            question = Question.objects.create(
                category=self.test_category,
                question_text=f'Test Question {i+1}: What is {i+1} + {i+1}?',
                pub_date=timezone.now()
            )
            
            # Create choices (one correct, three incorrect)
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
            
            self.questions.append(question)
        
        print(f"✓ Created test data: 2 users, 1 category, {len(self.questions)} questions")
    
    def test_student_authentication(self):
        """Test student login and access control"""
        print("\n1. Testing Student Authentication...")
        
        # Test login
        login_success = self.client.login(
            username='test_student@example.com',
            password='testpass123'
        )
        
        if login_success:
            print("✓ Student login successful")
        else:
            print("✗ Student login failed")
            return False
        
        # Test access to tryout list
        response = self.client.get('/tryouts/')
        if response.status_code == 200:
            print("✓ Student can access tryout list")
        else:
            print(f"✗ Student cannot access tryout list (Status: {response.status_code})")
            return False
        
        return True
    
    def test_tryout_list_display(self):
        """Test tryout list page functionality"""
        print("\n2. Testing Tryout List Display...")
        
        response = self.client.get('/tryouts/')
        
        if response.status_code == 200:
            print("✓ Tryout list page loads successfully")
            
            # Check if test category is displayed
            if self.test_category.category_name.encode() in response.content:
                print("✓ Test category is displayed in tryout list")
            else:
                print("✗ Test category not found in tryout list")
                return False
        else:
            print(f"✗ Tryout list page failed to load (Status: {response.status_code})")
            return False
        
        return True
    
    def test_test_session_creation(self):
        """Test test session initialization"""
        print("\n3. Testing Test Session Creation...")
        
        # Start a test
        response = self.client.get(f'/test/{self.test_category.id}/0/')
        
        if response.status_code == 200:
            print("✓ Test session created successfully")
            
            # Check if test object was created in database
            test_exists = Test.objects.filter(
                student=self.student_user,
                is_submitted=False,
                categories=self.test_category
            ).exists()
            
            if test_exists:
                print("✓ Test object created in database")
                self.current_test = Test.objects.get(
                    student=self.student_user,
                    is_submitted=False,
                    categories=self.test_category
                )
            else:
                print("✗ Test object not created in database")
                return False
            
            # Check if session data is set
            session = self.client.session
            session_key = f'test_session_{self.test_category.id}_{self.student_user.id}'
            
            if session_key in session:
                print("✓ Test session data initialized")
                print(f"  Session contains: {list(session[session_key].keys())}")
            else:
                print("✗ Test session data not initialized")
                return False
                
        else:
            print(f"✗ Test session creation failed (Status: {response.status_code})")
            return False
        
        return True
    
    def test_question_navigation(self):
        """Test navigation between questions"""
        print("\n4. Testing Question Navigation...")
        
        # Test accessing different questions
        for i in range(len(self.questions)):
            response = self.client.get(f'/test/{self.test_category.id}/{i}/')
            
            if response.status_code == 200:
                print(f"✓ Question {i+1} loads successfully")
                
                # Check if correct question is displayed
                question_text = self.questions[i].question_text
                if question_text.encode() in response.content:
                    print(f"  ✓ Correct question text displayed")
                else:
                    print(f"  ✗ Incorrect question text displayed")
                    return False
            else:
                print(f"✗ Question {i+1} failed to load (Status: {response.status_code})")
                return False
        
        return True
    
    def test_answer_submission(self):
        """Test answer submission and saving"""
        print("\n5. Testing Answer Submission...")
        
        correct_answers = 0
        
        # Submit answers for each question
        for i, question in enumerate(self.questions):
            # Get the correct choice for this question
            correct_choice = question.choices.filter(is_correct=True).first()
            
            # Submit the answer
            response = self.client.post(f'/test/{self.test_category.id}/{i}/', {
                'answer': correct_choice.id
            })
            
            if response.status_code == 302:  # Redirect expected
                print(f"✓ Answer {i+1} submitted successfully")
                
                # Verify answer was saved in database
                answer_exists = Answer.objects.filter(
                    test=self.current_test,
                    question=question,
                    selected_choice=correct_choice
                ).exists()
                
                if answer_exists:
                    print(f"  ✓ Answer {i+1} saved to database")
                    correct_answers += 1
                else:
                    print(f"  ✗ Answer {i+1} not saved to database")
                    return False
            else:
                print(f"✗ Answer {i+1} submission failed (Status: {response.status_code})")
                return False
        
        print(f"✓ All {correct_answers} answers submitted and saved successfully")
        return True
    
    def test_ajax_answer_saving(self):
        """Test AJAX answer saving without navigation"""
        print("\n6. Testing AJAX Answer Saving...")
        
        # Test AJAX answer submission
        question = self.questions[0]
        wrong_choice = question.choices.filter(is_correct=False).first()
        
        response = self.client.post(
            f'/test/{self.test_category.id}/0/',
            {'answer': wrong_choice.id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        if response.status_code == 200:
            print("✓ AJAX answer submission successful")
            
            # Check JSON response
            try:
                json_response = response.json()
                if json_response.get('status') == 'success':
                    print("✓ AJAX response indicates success")
                else:
                    print(f"✗ AJAX response indicates failure: {json_response}")
                    return False
            except:
                print("✗ Invalid JSON response from AJAX request")
                return False
            
            # Verify answer was updated in database
            updated_answer = Answer.objects.filter(
                test=self.current_test,
                question=question
            ).first()
            
            if updated_answer and updated_answer.selected_choice == wrong_choice:
                print("✓ AJAX answer update saved to database")
            else:
                print("✗ AJAX answer update not saved to database")
                return False
        else:
            print(f"✗ AJAX answer submission failed (Status: {response.status_code})")
            return False
        
        return True
    
    def test_session_management(self):
        """Test session data consistency"""
        print("\n7. Testing Session Management...")
        
        session = self.client.session
        session_key = f'test_session_{self.test_category.id}_{self.student_user.id}'
        
        if session_key in session:
            session_data = session[session_key]
            print("✓ Session data exists")
            
            # Check session structure
            required_keys = ['test_id', 'answered_questions', 'category_id']
            for key in required_keys:
                if key in session_data:
                    print(f"  ✓ Session contains '{key}'")
                else:
                    print(f"  ✗ Session missing '{key}'")
                    return False
            
            # Check if answered questions match database
            db_answers = Answer.objects.filter(test=self.current_test)
            session_answers = session_data['answered_questions']
            
            if len(db_answers) == len(session_answers):
                print(f"✓ Session and database answer count match ({len(db_answers)})")
            else:
                print(f"✗ Session ({len(session_answers)}) and database ({len(db_answers)}) answer count mismatch")
                return False
        else:
            print("✗ Session data not found")
            return False
        
        return True
    
    def test_time_management(self):
        """Test time limit and remaining time calculation"""
        print("\n8. Testing Time Management...")
        
        # Check if test has proper time setup
        if self.current_test.start_time:
            print("✓ Test has start time set")
            
            # Check remaining time calculation
            remaining_time = self.current_test.get_remaining_time()
            if remaining_time > 0:
                print(f"✓ Remaining time calculated: {remaining_time} seconds")
            else:
                print("✗ Remaining time calculation failed or time expired")
                return False
            
            # Check time limit
            if self.current_test.time_limit == self.test_category.time_limit:
                print(f"✓ Time limit set correctly: {self.current_test.time_limit} minutes")
            else:
                print("✗ Time limit not set correctly")
                return False
        else:
            print("✗ Test start time not set")
            return False
        
        return True
    
    def test_manual_submission(self):
        """Test manual test submission"""
        print("\n9. Testing Manual Test Submission...")
        
        # Submit the test manually
        response = self.client.post(f'/submit_test/{self.current_test.id}/')
        
        if response.status_code == 302:  # Redirect to results expected
            print("✓ Manual test submission successful")
            
            # Refresh test object from database
            self.current_test.refresh_from_db()
            
            # Check if test is marked as submitted
            if self.current_test.is_submitted:
                print("✓ Test marked as submitted in database")
            else:
                print("✗ Test not marked as submitted")
                return False
            
            # Check if end time is set
            if self.current_test.end_time:
                print("✓ Test end time recorded")
            else:
                print("✗ Test end time not recorded")
                return False
                
        else:
            print(f"✗ Manual test submission failed (Status: {response.status_code})")
            return False
        
        return True
    
    def test_score_calculation(self):
        """Test score calculation accuracy"""
        print("\n10. Testing Score Calculation...")
        
        # Check if score was calculated
        if self.current_test.score is not None:
            print(f"✓ Score calculated: {self.current_test.score}")
            
            # Verify score calculation
            total_questions = self.questions.count()
            correct_answers = Answer.objects.filter(
                test=self.current_test,
                selected_choice__is_correct=True
            ).count()
            
            expected_score = (correct_answers / total_questions) * 100
            
            if abs(self.current_test.score - expected_score) < 0.1:  # Allow small floating point differences
                print(f"✓ Score calculation correct: {correct_answers}/{total_questions} = {expected_score:.1f}%")
            else:
                print(f"✗ Score calculation incorrect. Expected: {expected_score:.1f}%, Got: {self.current_test.score}")
                return False
        else:
            print("✗ Score not calculated")
            return False
        
        return True
    
    def test_results_display(self):
        """Test test results page"""
        print("\n11. Testing Results Display...")
        
        # Access results page
        response = self.client.get(f'/test_results/{self.current_test.id}/')
        
        if response.status_code == 200:
            print("✓ Results page loads successfully")
            
            # Check if score is displayed
            score_text = f"{self.current_test.score:.1f}".encode()
            if score_text in response.content:
                print("✓ Score displayed on results page")
            else:
                print("✗ Score not displayed on results page")
                return False
                
        else:
            print(f"✗ Results page failed to load (Status: {response.status_code})")
            return False
        
        return True
    
    def test_detailed_results(self):
        """Test detailed results page"""
        print("\n12. Testing Detailed Results...")
        
        # Access detailed results page
        response = self.client.get(f'/test_results_detail/{self.current_test.id}/')
        
        if response.status_code == 200:
            print("✓ Detailed results page loads successfully")
            
            # Check if questions and answers are displayed
            for question in self.questions:
                if question.question_text.encode() in response.content:
                    print(f"  ✓ Question displayed: {question.question_text[:50]}...")
                else:
                    print(f"  ✗ Question not displayed: {question.question_text[:50]}...")
                    return False
                    
        else:
            print(f"✗ Detailed results page failed to load (Status: {response.status_code})")
            return False
        
        return True
    
    def test_test_history(self):
        """Test test history page"""
        print("\n13. Testing Test History...")
        
        # Access test history page
        response = self.client.get('/test_history/')
        
        if response.status_code == 200:
            print("✓ Test history page loads successfully")
            
            # Check if completed test is listed
            if self.test_category.category_name.encode() in response.content:
                print("✓ Completed test appears in history")
            else:
                print("✗ Completed test not found in history")
                return False
                
        else:
            print(f"✗ Test history page failed to load (Status: {response.status_code})")
            return False
        
        return True
    
    def test_session_cleanup(self):
        """Test session cleanup after test completion"""
        print("\n14. Testing Session Cleanup...")
        
        session = self.client.session
        session_key = f'test_session_{self.test_category.id}_{self.student_user.id}'
        
        if session_key not in session:
            print("✓ Session data cleaned up after test submission")
        else:
            print("✗ Session data not cleaned up after test submission")
            return False
        
        return True
    
    def test_multiple_test_prevention(self):
        """Test prevention of multiple simultaneous tests"""
        print("\n15. Testing Multiple Test Prevention...")
        
        # Try to start another test in the same category
        response = self.client.get(f'/test/{self.test_category.id}/0/')
        
        # Should redirect to results since test is already completed
        if response.status_code == 302:
            print("✓ Multiple test prevention working - redirected")
        else:
            print(f"✗ Multiple test prevention failed (Status: {response.status_code})")
            return False
        
        return True
    
    def run_all_tests(self):
        """Run all tests and provide summary"""
        print("Starting comprehensive tryout testing...\n")
        
        tests = [
            self.test_student_authentication,
            self.test_tryout_list_display,
            self.test_test_session_creation,
            self.test_question_navigation,
            self.test_answer_submission,
            self.test_ajax_answer_saving,
            self.test_session_management,
            self.test_time_management,
            self.test_manual_submission,
            self.test_score_calculation,
            self.test_results_display,
            self.test_detailed_results,
            self.test_test_history,
            self.test_session_cleanup,
            self.test_multiple_test_prevention
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                    print(f"❌ {test.__name__} FAILED")
            except Exception as e:
                failed += 1
                print(f"❌ {test.__name__} FAILED with exception: {str(e)}")
        
        print(f"\n" + "="*50)
        print(f"TEST SUMMARY:")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        print(f"="*50)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Tryout functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the failed tests above.")
        
        return failed == 0
    
    def cleanup(self):
        """Clean up test data"""
        print("\nCleaning up test data...")
        
        # Delete test data
        Answer.objects.filter(test__student=self.student_user).delete()
        Test.objects.filter(student=self.student_user).delete()
        Choice.objects.filter(question__category=self.test_category).delete()
        Question.objects.filter(category=self.test_category).delete()
        self.test_category.delete()
        self.student_user.delete()
        self.admin_user.delete()
        
        print("✓ Test data cleaned up")

def main():
    """Main function to run the test suite"""
    suite = TryoutTestSuite()
    
    try:
        success = suite.run_all_tests()
        return success
    except Exception as e:
        print(f"Test suite failed with error: {str(e)}")
        return False
    finally:
        suite.cleanup()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
