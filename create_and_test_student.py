#!/usr/bin/env python
"""
Script untuk membuat user student test dan test akses
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import SubscriptionPackage, Role

User = get_user_model()

def create_test_student():
    """Create test student user"""
    print("👤 Creating test student user...")
    
    try:
        # Get or create student role
        student_role, created = Role.objects.get_or_create(
            role_name='Student',
            defaults={'description': 'Student role for testing'}
        )
        
        if created:
            print("✅ Created Student role")
        else:
            print("✅ Student role already exists")
        
        # Create or get student user
        student_user, created = User.objects.get_or_create(
            email='test@students.com',
            defaults={
                'username': 'test_student',
                'first_name': 'Test',
                'last_name': 'Student',
                'role': student_role
            }
        )
        
        if created:
            student_user.set_password('testpassword123')
            student_user.save()
            print("✅ Created test student user")
        else:
            print("✅ Test student user already exists")
            
        print(f"   Email: {student_user.email}")
        print(f"   Role: {student_user.role.role_name}")
        
        return student_user
        
    except Exception as e:
        print(f"❌ Error creating student: {e}")
        return None

def test_student_payment_access():
    """Test apakah student bisa mengakses halaman upload payment"""
    print("\n🔍 Testing student access to upload payment...")
    
    # Create test client
    client = Client()
    
    try:
        # Get or create student user
        student_user = create_test_student()
        if not student_user:
            return
        
        # Login as student
        client.force_login(student_user)
        print("✅ Logged in as student")
        
        # Get a subscription package
        package = SubscriptionPackage.objects.filter(is_active=True).first()
        if not package:
            print("❌ No active subscription packages found")
            return
        
        print(f"✅ Found package: {package.name} (ID: {package.id})")
        
        # Test access to upload payment page
        url = f'/subscription/upload-payment/{package.id}/'
        print(f"🔗 Testing URL: {url}")
        
        response = client.get(url)
        print(f"📋 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Student can access upload payment page!")
        elif response.status_code == 403:
            print("❌ FAILED: Permission denied (403)")
        elif response.status_code == 404:
            print("❌ FAILED: Page not found (404)")
        else:
            print(f"❌ FAILED: Unexpected status code: {response.status_code}")
            
        # Check subscription status
        sub_status = student_user.get_subscription_status()
        print(f"📊 Subscription status: {sub_status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_student_payment_access()
