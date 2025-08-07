#!/usr/bin/env python
"""
Test script for Student Rankings functionality
Tests the ranking system with various filters and scenarios
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

class StudentRankingsTest:
    def __init__(self):
        self.client = Client()
        self.test_users = []
        self.test_categories = []
        self.test_questions = []
        
    def setup_test_data(self):
        """Setup comprehensive test data for ranking system"""
        print("Setting up test data for ranking system...")
        
        # Create roles
        self.student_role, _ = Role.objects.get_or_create(role_name='Student')
        
        # Create multiple test students
        for i in range(10):
            user = User.objects.create_user(
                username=f'ranking_student_{i+1}@example.com',
                email=f'ranking_student_{i+1}@example.com',
                password='testpass123',
                role=self.student_role
            )
            self.test_users.append(user)
        
        # Create test categories with different scoring methods
        categories_data = [
            {'name': 'Mathematics', 'method': 'default', 'time': 60, 'pass': 70.0},
            {'name': 'Physics', 'method': 'custom', 'time': 90, 'pass': 75.0},
            {'name': 'Chemistry', 'method': 'utbk', 'time': 120, 'pass': 80.0},
        ]
        
        for cat_data in categories_data:
            category = Category.objects.create(
                category_name=cat_data['name'],
                time_limit=cat_data['time'],
                scoring_method=cat_data['method'],
                passing_score=cat_data['pass']
            )
            self.test_categories.append(category)
            
            # Create questions for each category
            for q in range(5):  # 5 questions per category
                question = Question.objects.create(
                    category=category,
                    question_text=f'{cat_data["name"]} Question {q+1}: Sample question for testing',
                    pub_date=timezone.now(),
                    custom_weight=20 if cat_data['method'] == 'custom' else 1,
                    difficulty_coefficient=1.2 if cat_data['method'] == 'utbk' else 1.0
                )
                
                # Create choices
                for c in range(4):
                    Choice.objects.create(
                        question=question,
                        choice_text=f'Choice {c+1}',
                        is_correct=(c == 0)  # First choice is correct
                    )
                
                self.test_questions.append(question)
        
        print(f"✓ Created {len(self.test_users)} students, {len(self.test_categories)} categories, {len(self.test_questions)} questions")
    
    def create_test_results(self):
        """Create diverse test results for different ranking scenarios"""
        print("Creating diverse test results...")
        
        # Scenario 1: Student with high overall average
        self.create_student_tests(self.test_users[0], [85, 90, 88])  # Good in all categories
        
        # Scenario 2: Student with one excellent score but lower average  
        self.create_student_tests(self.test_users[1], [95, 65, 70])  # Excellent in math, average others
        
        # Scenario 3: Consistent but average student
        self.create_student_tests(self.test_users[2], [75, 75, 75])  # Consistent average
        
        # Scenario 4: Improving student (recent tests better)
        self.create_student_tests(self.test_users[3], [60, 70, 80])  # Getting better
        
        # Scenario 5: High performer in one category only
        self.create_student_tests(self.test_users[4], [98])  # Only math, but excellent
        
        # Scenario 6-10: Various performance levels
        for i, user in enumerate(self.test_users[5:]):
            scores = [70 + (i * 3), 68 + (i * 2), 72 + (i * 4)]  # Varied performance
            self.create_student_tests(user, scores[:min(len(scores), len(self.test_categories))])
        
        print("✓ Created diverse test results for ranking analysis")
    
    def create_student_tests(self, student, scores):
        """Create tests for a student with specified scores"""
        for i, score in enumerate(scores):
            if i >= len(self.test_categories):
                break
                
            category = self.test_categories[i]
            questions = Question.objects.filter(category=category)
            
            # Create test
            test = Test.objects.create(
                student=student,
                start_time=timezone.now() - timedelta(days=i*7),  # Spread over weeks
                time_limit=category.time_limit,
                is_submitted=True
            )
            test.categories.add(category)
            
            # Calculate how many questions to answer correctly for target score
            total_questions = questions.count()
            if category.scoring_method == 'default':
                correct_needed = int((score / 100) * total_questions)
            elif category.scoring_method == 'custom':
                # For custom scoring, we need to be more careful
                correct_needed = min(int((score / 100) * total_questions), total_questions)
            else:  # utbk
                correct_needed = int((score / 100) * total_questions)
            
            # Answer questions
            for j, question in enumerate(questions):
                correct_choice = question.choices.filter(is_correct=True).first()
                wrong_choice = question.choices.filter(is_correct=False).first()
                
                selected_choice = correct_choice if j < correct_needed else wrong_choice
                
                Answer.objects.create(
                    test=test,
                    question=question,
                    selected_choice=selected_choice
                )
            
            # Calculate score
            test.calculate_score()
            test.save()
    
    def test_ranking_access(self):
        """Test access to ranking page"""
        print("\n1. Testing Ranking Page Access...")
        
        # Login as student
        login_success = self.client.login(
            username=self.test_users[0].username,
            password='testpass123'
        )
        
        if not login_success:
            print("✗ Student login failed")
            return False
        
        # Test access to ranking page
        response = self.client.get(reverse('student_rankings'))
        if response.status_code == 200:
            print("✓ Ranking page accessible")
        else:
            print(f"✗ Ranking page not accessible (Status: {response.status_code})")
            return False
        
        return True
    
    def test_overall_average_ranking(self):
        """Test overall average ranking functionality"""
        print("\n2. Testing Overall Average Ranking...")
        
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'min_tests': 2
        })
        
        if response.status_code == 200:
            rankings = response.context['rankings']
            if rankings:
                print(f"✓ Overall average ranking generated with {len(rankings)} students")
                
                # Check if rankings are properly sorted (highest average first)
                for i in range(len(rankings) - 1):
                    if rankings[i]['score'] < rankings[i+1]['score']:
                        print("✗ Rankings not properly sorted by average score")
                        return False
                
                print("✓ Rankings properly sorted by average score")
                
                # Display top 3 for verification
                print("Top 3 students:")
                for i, ranking in enumerate(rankings[:3]):
                    print(f"  {i+1}. {ranking['username']}: {ranking['score']}% avg, {ranking['total_tests']} tests")
                
            else:
                print("✗ No rankings generated")
                return False
        else:
            print(f"✗ Failed to get overall average ranking (Status: {response.status_code})")
            return False
        
        return True
    
    def test_category_best_ranking(self):
        """Test category best score ranking"""
        print("\n3. Testing Category Best Score Ranking...")
        
        math_category = self.test_categories[0]  # Mathematics
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'category_best',
            'category_id': math_category.id,
            'min_tests': 1
        })
        
        if response.status_code == 200:
            rankings = response.context['rankings']
            if rankings:
                print(f"✓ Category best score ranking generated with {len(rankings)} students")
                
                # Check sorting (highest score first)
                for i in range(len(rankings) - 1):
                    if rankings[i]['score'] < rankings[i+1]['score']:
                        print("✗ Rankings not properly sorted by best score")
                        return False
                
                print("✓ Rankings properly sorted by best score")
                
                # Display top 3
                print(f"Top 3 in {math_category.category_name}:")
                for i, ranking in enumerate(rankings[:3]):
                    print(f"  {i+1}. {ranking['username']}: {ranking['score']}% best")
                
            else:
                print("✗ No category rankings generated")
                return False
        else:
            print(f"✗ Failed to get category ranking (Status: {response.status_code})")
            return False
        
        return True
    
    def test_category_average_ranking(self):
        """Test category average ranking"""
        print("\n4. Testing Category Average Ranking...")
        
        physics_category = self.test_categories[1]  # Physics
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'category_average',
            'category_id': physics_category.id,
            'min_tests': 1
        })
        
        if response.status_code == 200:
            rankings = response.context['rankings']
            if rankings:
                print(f"✓ Category average ranking generated with {len(rankings)} students")
                print(f"Top student in {physics_category.category_name}: {rankings[0]['username']} with {rankings[0]['score']}% average")
            else:
                print("✗ No category average rankings generated")
                return False
        else:
            print(f"✗ Failed to get category average ranking (Status: {response.status_code})")
            return False
        
        return True
    
    def test_time_period_filter(self):
        """Test time period filtering"""
        print("\n5. Testing Time Period Filters...")
        
        # Test week filter
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'time_period': 'week',
            'min_tests': 1
        })
        
        if response.status_code == 200:
            week_rankings = len(response.context['rankings'])
            print(f"✓ Week filter: {week_rankings} students")
        else:
            print("✗ Week filter failed")
            return False
        
        # Test all time filter
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'time_period': 'all',
            'min_tests': 1
        })
        
        if response.status_code == 200:
            all_rankings = len(response.context['rankings'])
            print(f"✓ All time filter: {all_rankings} students")
            
            # All time should have more or equal results than week
            if all_rankings >= week_rankings:
                print("✓ Time period filtering working correctly")
            else:
                print("✗ Time period filtering issue detected")
                return False
        else:
            print("✗ All time filter failed")
            return False
        
        return True
    
    def test_scoring_method_filter(self):
        """Test scoring method filtering"""
        print("\n6. Testing Scoring Method Filters...")
        
        # Test default scoring filter
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'scoring_method': 'default',
            'min_tests': 1
        })
        
        if response.status_code == 200:
            print("✓ Default scoring method filter working")
        else:
            print("✗ Default scoring method filter failed")
            return False
        
        # Test custom scoring filter
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'scoring_method': 'custom',
            'min_tests': 1
        })
        
        if response.status_code == 200:
            print("✓ Custom scoring method filter working")
        else:
            print("✗ Custom scoring method filter failed")
            return False
        
        return True
    
    def test_minimum_tests_filter(self):
        """Test minimum tests requirement"""
        print("\n7. Testing Minimum Tests Filter...")
        
        # Test with high minimum (should reduce results)
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'min_tests': 10,  # High requirement
        })
        
        if response.status_code == 200:
            high_min_results = len(response.context['rankings'])
            print(f"✓ High minimum tests (10): {high_min_results} students")
        else:
            print("✗ High minimum tests filter failed")
            return False
        
        # Test with low minimum (should have more results)
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'min_tests': 1,  # Low requirement
        })
        
        if response.status_code == 200:
            low_min_results = len(response.context['rankings'])
            print(f"✓ Low minimum tests (1): {low_min_results} students")
            
            # Low minimum should have more or equal results
            if low_min_results >= high_min_results:
                print("✓ Minimum tests filtering working correctly")
            else:
                print("✗ Minimum tests filtering issue detected")
                return False
        else:
            print("✗ Low minimum tests filter failed")
            return False
        
        return True
    
    def test_current_user_ranking(self):
        """Test current user ranking detection"""
        print("\n8. Testing Current User Ranking Detection...")
        
        response = self.client.get(reverse('student_rankings'), {
            'ranking_type': 'overall_average',
            'min_tests': 1
        })
        
        if response.status_code == 200:
            rankings = response.context['rankings']
            current_user_rank = response.context['current_user_rank']
            
            # Check if current user is in top rankings or separate rank is shown
            user_in_top = any(r['is_current_user'] for r in rankings)
            
            if user_in_top:
                print("✓ Current user found in top rankings")
            elif current_user_rank:
                print(f"✓ Current user rank shown separately: #{current_user_rank['rank']}")
            else:
                print("✗ Current user ranking not detected")
                return False
            
        else:
            print("✗ Failed to test current user ranking")
            return False
        
        return True
    
    def cleanup(self):
        """Clean up test data"""
        print("\nCleaning up test data...")
        
        # Delete answers first (foreign key constraint)
        Answer.objects.filter(test__student__in=self.test_users).delete()
        
        # Delete tests
        Test.objects.filter(student__in=self.test_users).delete()
        
        # Delete choices and questions
        for category in self.test_categories:
            Choice.objects.filter(question__category=category).delete()
            Question.objects.filter(category=category).delete()
            category.delete()
        
        # Delete test users
        for user in self.test_users:
            user.delete()
        
        print("✓ Test data cleaned up")
    
    def run_all_tests(self):
        """Run all ranking tests"""
        try:
            self.setup_test_data()
            self.create_test_results()
            
            tests = [
                self.test_ranking_access,
                self.test_overall_average_ranking,
                self.test_category_best_ranking,
                self.test_category_average_ranking,
                self.test_time_period_filter,
                self.test_scoring_method_filter,
                self.test_minimum_tests_filter,
                self.test_current_user_ranking,
            ]
            
            passed_tests = 0
            total_tests = len(tests)
            
            print("="*70)
            print("🏆 STUDENT RANKINGS SYSTEM TESTING")
            print("="*70)
            
            for test in tests:
                try:
                    if test():
                        passed_tests += 1
                except Exception as e:
                    print(f"✗ Test {test.__name__} failed with error: {str(e)}")
            
            print("\n" + "="*70)
            print(f"📊 TEST RESULTS: {passed_tests}/{total_tests} PASSED")
            
            if passed_tests == total_tests:
                print("🎉 ALL RANKING TESTS PASSED!")
                print("\n✅ Student Rankings System is working correctly!")
                print("\nFeatures Tested:")
                print("  • Overall average rankings")
                print("  • Category-specific best scores")
                print("  • Category-specific averages")
                print("  • Time period filtering")
                print("  • Scoring method filtering")
                print("  • Minimum tests requirements")
                print("  • Current user ranking detection")
                return True
            else:
                print(f"❌ {total_tests - passed_tests} test(s) failed!")
                return False
                
        except Exception as e:
            print(f"✗ Test suite failed with error: {str(e)}")
            return False
        finally:
            self.cleanup()

def main():
    """Main function to run the ranking tests"""
    test_suite = StudentRankingsTest()
    success = test_suite.run_all_tests()
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
