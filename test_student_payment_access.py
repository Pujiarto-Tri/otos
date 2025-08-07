#!/usr/bin/env python
"""
Script untuk test akses student ke halaman upload payment
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import SubscriptionPackage

User = get_user_model()

def test_student_payment_access():
    """Test apakah student bisa mengakses halaman upload payment"""
    print("🔍 Testing student access to upload payment...")
    
    # Create test client
    client = Client()
    
    try:
        # Get student user
        student_user = User.objects.get(email='test@students.com')
        print(f"✅ Found student user: {student_user.email}")
        print(f"   Role: {student_user.role.role_name}")
        
        # Login as student
        login_success = client.force_login(student_user)
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
        
    except User.DoesNotExist:
        print("❌ Student user test@students.com not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_student_payment_access()
