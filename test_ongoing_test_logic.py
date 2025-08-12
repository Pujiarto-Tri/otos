#!/usr/bin/env python
"""
Script untuk test redirect logic dan ongoing test
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Test, TryoutPackage, Category
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

def test_ongoing_test_logic():
    """Test logic untuk ongoing test"""
    print("🔍 Testing ongoing test logic...")
    
    user = User.objects.first()
    if not user:
        print("❌ No user found for testing")
        return
    
    print(f"👤 Testing dengan user: {user.username}")
    
    # Find ongoing tests
    ongoing_tests = Test.objects.filter(
        student=user,
        is_submitted=False
    )
    
    print(f"📋 Found {ongoing_tests.count()} ongoing test(s)")
    
    for test in ongoing_tests:
        print(f"\n📝 Test ID: {test.id}")
        print(f"   Start time: {test.start_time}")
        print(f"   Time limit: {test.time_limit}")
        
        if test.tryout_package:
            print(f"   Type: Package Test")
            print(f"   Package: {test.tryout_package.package_name}")
            print(f"   Current question index: {test.get_current_question_index()}")
            
            # Test URL generation
            try:
                url = reverse('take_package_test_question', 
                             args=[test.tryout_package.id, test.get_current_question_index()])
                print(f"   ✅ Redirect URL: {url}")
            except Exception as e:
                print(f"   ❌ URL generation error: {e}")
        
        elif test.categories.exists():
            category = test.categories.first()
            print(f"   Type: Category Test")
            print(f"   Category: {category.category_name}")
            print(f"   Current question index: {test.get_current_question_index()}")
            
            # Test URL generation
            try:
                url = reverse('take_test', 
                             args=[category.id, test.get_current_question_index()])
                print(f"   ✅ Redirect URL: {url}")
            except Exception as e:
                print(f"   ❌ URL generation error: {e}")
        
        else:
            print(f"   ⚠️ No package or category found!")
        
        # Test time up check
        if test.is_time_up():
            print(f"   ⏰ Test is timed out!")
        else:
            print(f"   ⏱️ Test is still active")

def test_package_names():
    """Test package names"""
    print("\n🏷️ Testing package names...")
    
    packages = TryoutPackage.objects.all()[:5]
    
    for package in packages:
        print(f"📦 Package ID {package.id}: '{package.package_name}'")

def test_redirect_logic():
    """Simulate redirect logic"""
    print("\n🔄 Testing redirect logic...")
    
    user = User.objects.first()
    ongoing_test = Test.objects.filter(
        student=user, 
        is_submitted=False
    ).first()
    
    if ongoing_test:
        print(f"📝 Found ongoing test: {ongoing_test.id}")
        
        if ongoing_test.is_time_up():
            print("⏰ Test is timed out - would auto-submit")
        else:
            if ongoing_test.tryout_package:
                print("📦 Package test detected")
                current_question_index = ongoing_test.get_current_question_index()
                print(f"   Current question: {current_question_index}")
                print(f"   Would redirect to: package/{ongoing_test.tryout_package.id}/question/{current_question_index}/")
            else:
                category = ongoing_test.categories.first()
                if category:
                    print("📂 Category test detected")
                    current_question_index = ongoing_test.get_current_question_index()
                    print(f"   Category: {category.category_name}")
                    print(f"   Current question: {current_question_index}")
                    print(f"   Would redirect to: category/{category.id}/take/{current_question_index}/")
    else:
        print("✅ No ongoing test found")

if __name__ == "__main__":
    print("=== Ongoing Test Logic Test ===\n")
    test_ongoing_test_logic()
    test_package_names()
    test_redirect_logic()
    print("\n" + "="*40)
