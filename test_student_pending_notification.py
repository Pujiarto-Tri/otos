#!/usr/bin/env python
"""
Script untuk test notifikasi pending payment pada dashboard student
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import SubscriptionPackage, Role, PaymentProof

User = get_user_model()

def test_student_pending_payment_notification():
    """Test notifikasi pending payment di dashboard student"""
    print("🔍 Testing student pending payment notification...")
    
    try:
        # Get or create student role
        student_role, created = Role.objects.get_or_create(
            role_name='Student',
            defaults={'description': 'Student role for testing'}
        )
        
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
        
        # Get a subscription package
        package = SubscriptionPackage.objects.filter(is_active=True).first()
        if not package:
            print("❌ No active subscription packages found")
            return
        
        # Create pending payment for student
        from django.utils import timezone
        
        pending_payment, created = PaymentProof.objects.get_or_create(
            user=student_user,
            package=package,
            status='pending',
            defaults={
                'amount_paid': package.price,
                'payment_method': 'Bank Transfer',
                'payment_date': timezone.now(),
                'notes': 'Test payment for student dashboard'
            }
        )
        
        if created:
            print(f"✅ Created pending payment for package: {package.name}")
        else:
            print(f"✅ Pending payment already exists for package: {package.name}")
        
        # Test dashboard access
        from django.test.utils import override_settings
        
        with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
            client = Client()
            client.force_login(student_user)
            print("✅ Logged in as student")
            
            # Get dashboard page
            response = client.get('/')
            print(f"📋 Dashboard response status: {response.status_code}")
        
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check if pending payment notification is in the response
                if 'Pembayaran Sedang Diverifikasi' in content:
                    print("✅ SUCCESS: Pending payment notification found in dashboard!")
                    
                    # Check if package name is mentioned
                    if package.name in content:
                        print(f"✅ Package name '{package.name}' found in notification")
                    else:
                        print(f"⚠️  Package name '{package.name}' not found in notification")
                    
                    # Check if "Lihat Status" link exists
                    if 'Lihat Status' in content:
                        print("✅ 'Lihat Status' link found")
                    else:
                        print("⚠️  'Lihat Status' link not found")
                        
                else:
                    print("❌ FAILED: Pending payment notification NOT found in dashboard")
                    
                # Check subscription status
                sub_status = student_user.get_subscription_status()
                print(f"📊 Student subscription status: {sub_status}")
                
            else:
                print(f"❌ FAILED: Dashboard access failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    try:
        # Remove test payment
        PaymentProof.objects.filter(
            user__email='test@students.com',
            status='pending'
        ).delete()
        print("✅ Cleaned up test payment data")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == '__main__':
    test_student_pending_payment_notification()
    
    # Ask if user wants to cleanup
    print("\n" + "="*50)
    cleanup = input("🗑️  Do you want to cleanup test data? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_data()
    else:
        print("ℹ️  Test data left intact for manual verification")
