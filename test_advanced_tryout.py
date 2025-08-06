#!/usr/bin/env python
"""
Advanced Test Script for Edge Cases and Stress Testing
Tests advanced scenarios including:
- Time expiration handling
- Session corruption recovery
- Concurrent user handling
- Large dataset performance
- Error handling and recovery
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
import threading
import time

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import User, Role, Category, Question, Choice, Test, Answer

class AdvancedTryoutTests:
    def __init__(self):
        self.client = Client()
        self.setup_test_data()
        print("=== Advanced Tryout Testing Suite ===\n")
    
    def setup_test_data(self):
        """Setup test data for advanced testing"""
        print("Setting up advanced test data...")
        
        # Create roles
        self.student_role, _ = Role.objects.get_or_create(role_name='Student')
        
        # Create test users
        self.student_user = User.objects.create_user(
            username='advanced_test_student@example.com',
            email='advanced_test_student@example.com',
            password='testpass123',
            role=self.student_role
        )
        
        # Create test category with short time limit for timeout testing
        self.timeout_category = Category.objects.create(
            category_name='Timeout Test Category',
            time_limit=1,  # 1 minute for quick timeout testing
            scoring_method='default',
            passing_score=70.0
        )
        
        # Create category with many questions for performance testing
        self.performance_category = Category.objects.create(
            category_name='Performance Test Category',
            time_limit=60,
            scoring_method='custom',
            passing_score=80.0
        )
        
        # Create questions for timeout testing
        self.timeout_questions = []
        for i in range(3):
            question = Question.objects.create(
                category=self.timeout_category,
                question_text=f'Timeout Test Question {i+1}',
                pub_date=timezone.now()
            )
            
            for j in range(4):
                Choice.objects.create(
                    question=question,
                    choice_text=f'Choice {j+1}',
                    is_correct=(j == 0)
                )
            
            self.timeout_questions.append(question)
        
        # Create many questions for performance testing
        self.performance_questions = []
        for i in range(50):  # 50 questions for performance test
            question = Question.objects.create(
                category=self.performance_category,
                question_text=f'Performance Test Question {i+1}: Complex mathematical problem with long text that simulates real exam questions with detailed scenarios and multiple variables to test system performance under load.',
                pub_date=timezone.now(),
                custom_weight=2  # Custom weight for scoring
            )
            
            for j in range(5):  # 5 choices per question
                Choice.objects.create(
                    question=question,
                    choice_text=f'Detailed choice {j+1} with comprehensive explanation that tests database performance',
                    is_correct=(j == 0)
                )
            
            self.performance_questions.append(question)
        
        print(f"✓ Created advanced test data: {len(self.timeout_questions)} timeout questions, {len(self.performance_questions)} performance questions")
    
    def test_time_expiration_handling(self):
        """Test automatic test submission when time expires"""
        print("\n1. Testing Time Expiration Handling...")
        
        # Login student
        self.client.login(
            username='advanced_test_student@example.com',
            password='testpass123'
        )
        
        # Start timeout test
        response = self.client.get(f'/test/{self.timeout_category.id}/0/')
        if response.status_code != 200:
            print(f"✗ Failed to start timeout test (Status: {response.status_code})")
            return False
        
        # Get the created test
        timeout_test = Test.objects.get(
            student=self.student_user,
            is_submitted=False,
            categories=self.timeout_category
        )
        
        print("✓ Timeout test started")
        
        # Answer one question
        correct_choice = self.timeout_questions[0].choices.filter(is_correct=True).first()
        response = self.client.post(f'/test/{self.timeout_category.id}/0/', {
            'answer': correct_choice.id
        })
        
        if response.status_code == 302:
            print("✓ Answer submitted before timeout")
        else:
            print("✗ Failed to submit answer before timeout")
            return False
        
        # Simulate time expiration by manually setting start time to past
        timeout_test.start_time = timezone.now() - timedelta(minutes=2)  # 2 minutes ago
        timeout_test.save()
        
        # Try to access the test after timeout
        response = self.client.get(f'/test/{self.timeout_category.id}/1/')
        
        # Should redirect to results due to timeout
        if response.status_code == 302:
            print("✓ Test auto-submitted after timeout")
            
            # Check if test is marked as submitted
            timeout_test.refresh_from_db()
            if timeout_test.is_submitted:
                print("✓ Test marked as submitted after timeout")
            else:
                print("✗ Test not marked as submitted after timeout")
                return False
        else:
            print(f"✗ Test not auto-submitted after timeout (Status: {response.status_code})")
            return False
        
        return True
    
    def test_session_corruption_recovery(self):
        """Test recovery from corrupted or missing session data"""
        print("\n2. Testing Session Corruption Recovery...")
        
        # Start performance test
        response = self.client.get(f'/test/{self.performance_category.id}/0/')
        if response.status_code != 200:
            print(f"✗ Failed to start performance test (Status: {response.status_code})")
            return False
        
        print("✓ Performance test started")
        
        # Get the created test
        performance_test = Test.objects.get(
            student=self.student_user,
            is_submitted=False,
            categories=self.performance_category
        )
        
        # Submit some answers
        for i in range(5):
            correct_choice = self.performance_questions[i].choices.filter(is_correct=True).first()
            response = self.client.post(f'/test/{self.performance_category.id}/{i}/', {
                'answer': correct_choice.id
            })
        
        print("✓ Initial answers submitted")
        
        # Simulate session corruption by clearing session
        session = self.client.session
        session_key = f'test_session_{self.performance_category.id}_{self.student_user.id}'
        if session_key in session:
            del session[session_key]
            session.save()
            print("✓ Session data corrupted (deleted)")
        
        # Try to continue the test - should recover from database
        response = self.client.get(f'/test/{self.performance_category.id}/5/')
        
        if response.status_code == 200:
            print("✓ Test continued after session corruption")
            
            # Check if session was restored
            session = self.client.session
            if session_key in session:
                restored_session = session[session_key]
                if 'answered_questions' in restored_session and len(restored_session['answered_questions']) > 0:
                    print(f"✓ Session restored with {len(restored_session['answered_questions'])} answers")
                else:
                    print("✗ Session restored but no answers found")
                    return False
            else:
                print("✗ Session not restored after corruption")
                return False
        else:
            print(f"✗ Failed to continue test after session corruption (Status: {response.status_code})")
            return False
        
        return True
    
    def test_performance_with_large_dataset(self):
        """Test performance with large number of questions"""
        print("\n3. Testing Performance with Large Dataset...")
        
        start_time = time.time()
        
        # Navigate through all 50 questions
        navigation_times = []
        
        for i in range(10):  # Test first 10 questions for performance
            question_start = time.time()
            response = self.client.get(f'/test/{self.performance_category.id}/{i}/')
            question_end = time.time()
            
            navigation_time = question_end - question_start
            navigation_times.append(navigation_time)
            
            if response.status_code == 200:
                if navigation_time > 2.0:  # Alert if takes more than 2 seconds
                    print(f"⚠️  Question {i+1} loaded slowly: {navigation_time:.2f}s")
                else:
                    print(f"✓ Question {i+1} loaded quickly: {navigation_time:.3f}s")
            else:
                print(f"✗ Question {i+1} failed to load")
                return False
        
        avg_navigation_time = sum(navigation_times) / len(navigation_times)
        print(f"✓ Average navigation time: {avg_navigation_time:.3f}s")
        
        if avg_navigation_time < 1.0:
            print("✓ Performance test passed - good response times")
        else:
            print("⚠️  Performance test warning - slow response times")
        
        return True
    
    def test_rapid_answer_submission(self):
        """Test rapid consecutive answer submissions"""
        print("\n4. Testing Rapid Answer Submission...")
        
        submission_times = []
        
        # Submit answers rapidly for 10 questions
        for i in range(10):
            correct_choice = self.performance_questions[i].choices.filter(is_correct=True).first()
            
            start_time = time.time()
            response = self.client.post(f'/test/{self.performance_category.id}/{i}/', {
                'answer': correct_choice.id
            })
            end_time = time.time()
            
            submission_time = end_time - start_time
            submission_times.append(submission_time)
            
            if response.status_code == 302:
                print(f"✓ Answer {i+1} submitted in {submission_time:.3f}s")
            else:
                print(f"✗ Answer {i+1} submission failed")
                return False
        
        avg_submission_time = sum(submission_times) / len(submission_times)
        print(f"✓ Average submission time: {avg_submission_time:.3f}s")
        
        # Verify all answers were saved
        saved_answers = Answer.objects.filter(
            test=Test.objects.get(
                student=self.student_user,
                is_submitted=False,
                categories=self.performance_category
            )
        ).count()
        
        if saved_answers >= 10:
            print(f"✓ All {saved_answers} rapid answers saved to database")
        else:
            print(f"✗ Only {saved_answers} answers saved, expected at least 10")
            return False
        
        return True
    
    def test_ajax_performance(self):
        """Test AJAX answer saving performance"""
        print("\n5. Testing AJAX Performance...")
        
        ajax_times = []
        
        # Submit AJAX answers for multiple questions
        for i in range(10, 20):  # Questions 11-20
            question = self.performance_questions[i]
            correct_choice = question.choices.filter(is_correct=True).first()
            
            start_time = time.time()
            response = self.client.post(
                f'/test/{self.performance_category.id}/{i}/',
                {'answer': correct_choice.id},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            end_time = time.time()
            
            ajax_time = end_time - start_time
            ajax_times.append(ajax_time)
            
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if json_response.get('status') == 'success':
                        print(f"✓ AJAX answer {i+1} saved in {ajax_time:.3f}s")
                    else:
                        print(f"✗ AJAX answer {i+1} failed: {json_response}")
                        return False
                except:
                    print(f"✗ AJAX answer {i+1} invalid JSON response")
                    return False
            else:
                print(f"✗ AJAX answer {i+1} submission failed")
                return False
        
        avg_ajax_time = sum(ajax_times) / len(ajax_times)
        print(f"✓ Average AJAX submission time: {avg_ajax_time:.3f}s")
        
        if avg_ajax_time < 0.5:
            print("✓ AJAX performance excellent")
        elif avg_ajax_time < 1.0:
            print("✓ AJAX performance good")
        else:
            print("⚠️  AJAX performance could be improved")
        
        return True
    
    def test_concurrent_operations(self):
        """Test concurrent answer submissions (simulated)"""
        print("\n6. Testing Concurrent Operations...")
        
        # Simulate concurrent submissions by rapid sequential calls
        # (True concurrency would require multiple test clients)
        
        results = []
        errors = []
        
        def submit_answer(question_index):
            try:
                question = self.performance_questions[question_index]
                choice = question.choices.filter(is_correct=True).first()
                
                response = self.client.post(
                    f'/test/{self.performance_category.id}/{question_index}/',
                    {'answer': choice.id},
                    HTTP_X_REQUESTED_WITH='XMLHttpRequest'
                )
                
                if response.status_code == 200:
                    results.append(f"Success: Question {question_index + 1}")
                else:
                    errors.append(f"Error: Question {question_index + 1} - Status {response.status_code}")
            except Exception as e:
                errors.append(f"Exception: Question {question_index + 1} - {str(e)}")
        
        # Submit multiple answers in rapid succession
        for i in range(20, 30):
            submit_answer(i)
        
        if len(errors) == 0:
            print(f"✓ All {len(results)} concurrent operations successful")
        else:
            print(f"✗ {len(errors)} concurrent operations failed:")
            for error in errors[:3]:  # Show first 3 errors
                print(f"  - {error}")
            return False
        
        return True
    
    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n7. Testing Error Handling...")
        
        # Test invalid question index
        response = self.client.get(f'/test/{self.performance_category.id}/999/')
        if response.status_code in [404, 302]:  # 404 or redirect to valid question
            print("✓ Invalid question index handled correctly")
        else:
            print(f"✗ Invalid question index not handled (Status: {response.status_code})")
            return False
        
        # Test invalid choice submission
        response = self.client.post(f'/test/{self.performance_category.id}/0/', {
            'answer': 99999  # Non-existent choice ID
        })
        if response.status_code in [404, 400, 302]:  # Error or redirect
            print("✓ Invalid choice ID handled correctly")
        else:
            print(f"✗ Invalid choice ID not handled (Status: {response.status_code})")
            return False
        
        # Test invalid category access
        response = self.client.get('/test/99999/0/')
        if response.status_code == 404:
            print("✓ Invalid category access handled correctly")
        else:
            print(f"✗ Invalid category access not handled (Status: {response.status_code})")
            return False
        
        return True
    
    def test_memory_usage(self):
        """Test memory usage with large session data"""
        print("\n8. Testing Memory Usage...")
        
        # Check session size
        session = self.client.session
        session_key = f'test_session_{self.performance_category.id}_{self.student_user.id}'
        
        if session_key in session:
            session_data = session[session_key]
            answered_questions = session_data.get('answered_questions', {})
            
            print(f"✓ Session contains {len(answered_questions)} answered questions")
            
            # Estimate session size (rough calculation)
            import sys
            session_size = sys.getsizeof(str(session_data))
            print(f"✓ Estimated session size: {session_size} bytes")
            
            if session_size > 10000:  # 10KB threshold
                print("⚠️  Large session size detected")
            else:
                print("✓ Session size within acceptable limits")
        else:
            print("✗ Session data not found")
            return False
        
        return True
    
    def test_database_consistency(self):
        """Test database consistency after all operations"""
        print("\n9. Testing Database Consistency...")
        
        # Get current test
        current_test = Test.objects.get(
            student=self.student_user,
            is_submitted=False,
            categories=self.performance_category
        )
        
        # Count answers in database
        db_answers = Answer.objects.filter(test=current_test).count()
        
        # Count answers in session
        session = self.client.session
        session_key = f'test_session_{self.performance_category.id}_{self.student_user.id}'
        session_answers = len(session[session_key]['answered_questions']) if session_key in session else 0
        
        if db_answers == session_answers:
            print(f"✓ Database and session consistency maintained: {db_answers} answers")
        else:
            print(f"✗ Database ({db_answers}) and session ({session_answers}) inconsistency detected")
            return False
        
        # Check for duplicate answers
        duplicates = Answer.objects.filter(test=current_test).values('question').annotate(
            count=Count('question')
        ).filter(count__gt=1)
        
        if not duplicates.exists():
            print("✓ No duplicate answers found")
        else:
            print(f"✗ {duplicates.count()} duplicate answers found")
            return False
        
        return True
    
    def run_all_advanced_tests(self):
        """Run all advanced tests"""
        print("Starting advanced tryout testing...\n")
        
        tests = [
            self.test_time_expiration_handling,
            self.test_session_corruption_recovery,
            self.test_performance_with_large_dataset,
            self.test_rapid_answer_submission,
            self.test_ajax_performance,
            self.test_concurrent_operations,
            self.test_error_handling,
            self.test_memory_usage,
            self.test_database_consistency
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
        print(f"ADVANCED TEST SUMMARY:")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%")
        print(f"="*50)
        
        return failed == 0
    
    def cleanup(self):
        """Clean up test data"""
        print("\nCleaning up advanced test data...")
        
        Answer.objects.filter(test__student=self.student_user).delete()
        Test.objects.filter(student=self.student_user).delete()
        Choice.objects.filter(question__category__in=[self.timeout_category, self.performance_category]).delete()
        Question.objects.filter(category__in=[self.timeout_category, self.performance_category]).delete()
        self.timeout_category.delete()
        self.performance_category.delete()
        self.student_user.delete()
        
        print("✓ Advanced test data cleaned up")

def main():
    """Main function to run advanced tests"""
    suite = AdvancedTryoutTests()
    
    try:
        success = suite.run_all_advanced_tests()
        return success
    except Exception as e:
        print(f"Advanced test suite failed with error: {str(e)}")
        return False
    finally:
        suite.cleanup()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
