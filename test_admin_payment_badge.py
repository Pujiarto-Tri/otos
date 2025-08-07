#!/usr/bin/env python
"""
Script untuk test notifikasi badge pending payments di sidebar admin
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

def test_admin_payment_notification_badge():
    """Test badge notifikasi pending payments di sidebar admin"""
    print("🔍 Testing admin payment notification badge...")
    
    try:
        # Get or create admin role
        admin_role, created = Role.objects.get_or_create(
            role_name='Admin',
            defaults={'description': 'Administrator role'}
        )
        
        if created:
            print("✅ Created Admin role")
        else:
            print("✅ Admin role already exists")
        
        # Get or create visitor role for test payment users
        visitor_role, created = Role.objects.get_or_create(
            role_name='Visitor',
            defaults={'description': 'Visitor role for testing'}
        )
        
        # Create or get admin user
        admin_user, created = User.objects.get_or_create(
            email='admin@test.com',
            defaults={
                'username': 'admin_test',
                'first_name': 'Admin',
                'last_name': 'Test',
                'role': admin_role,
                'is_superuser': True,
                'is_staff': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            print("✅ Created admin test user")
        else:
            print("✅ Admin test user already exists")
        
        # Create test users for payments
        test_users = []
        for i in range(3):
            user, created = User.objects.get_or_create(
                email=f'testuser{i+1}@example.com',
                defaults={
                    'username': f'testuser{i+1}',
                    'first_name': f'Test{i+1}',
                    'last_name': 'User',
                    'role': visitor_role
                }
            )
            test_users.append(user)
        
        print(f"✅ Created/found {len(test_users)} test users")
        
        # Get a subscription package
        package = SubscriptionPackage.objects.filter(is_active=True).first()
        if not package:
            print("❌ No active subscription packages found")
            return
        
        print(f"✅ Found package: {package.name}")
        
        # Create pending payments
        from django.utils import timezone
        
        pending_count = 0
        for i, user in enumerate(test_users[:2]):  # Create 2 pending payments
            payment, created = PaymentProof.objects.get_or_create(
                user=user,
                package=package,
                status='pending',
                defaults={
                    'amount_paid': package.price,
                    'payment_method': 'Bank Transfer',
                    'payment_date': timezone.now(),
                    'notes': f'Test payment {i+1} for badge notification'
                }
            )
            if created:
                pending_count += 1
        
        print(f"✅ Created {pending_count} pending payments")
        
        # Test admin dashboard access
        from django.test.utils import override_settings
        
        with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
            client = Client()
            client.force_login(admin_user)
            print("✅ Logged in as admin")
            
            # Get dashboard page
            response = client.get('/')
            print(f"📋 Dashboard response status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                # Check if pending_payments_count is in the response
                total_pending = PaymentProof.objects.filter(status='pending').count()
                print(f"📊 Total pending payments in database: {total_pending}")
                
                if f'pending_payments_count' in content:
                    print("✅ Variable 'pending_payments_count' found in template context")
                
                # Check if the badge number appears
                if f'>{total_pending}<' in content and total_pending > 0:
                    print(f"✅ SUCCESS: Badge number '{total_pending}' found in sidebar!")
                elif total_pending > 0:
                    print(f"⚠️  Badge number '{total_pending}' not found, but should be there")
                else:
                    print("ℹ️  No pending payments, so no badge should appear")
                
                # Check if Payment Verification link exists
                if 'Payment Verification' in content:
                    print("✅ 'Payment Verification' menu found")
                else:
                    print("⚠️  'Payment Verification' menu not found")
                
                # Check if the red badge styling is there
                if 'bg-red-500' in content and total_pending > 0:
                    print("✅ Red badge styling found")
                elif total_pending > 0:
                    print("⚠️  Red badge styling not found")
                    
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
        # Remove test payments
        PaymentProof.objects.filter(
            user__email__in=['testuser1@example.com', 'testuser2@example.com', 'testuser3@example.com']
        ).delete()
        
        # Remove test users
        User.objects.filter(
            email__in=['testuser1@example.com', 'testuser2@example.com', 'testuser3@example.com']
        ).delete()
        
        print("✅ Cleaned up test payment and user data")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

if __name__ == '__main__':
    test_admin_payment_notification_badge()
    
    # Ask if user wants to cleanup
    print("\n" + "="*50)
    cleanup = input("🗑️  Do you want to cleanup test data? (y/n): ").lower().strip()
    if cleanup == 'y':
        cleanup_test_data()
    else:
        print("ℹ️  Test data left intact for manual verification")
