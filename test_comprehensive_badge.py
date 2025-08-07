#!/usr/bin/env python
"""
Script untuk test komprehensif badge pending payments
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import SubscriptionPackage, Role, PaymentProof
import re

User = get_user_model()

def test_payment_badge_comprehensive():
    """Test komprehensif badge pending payments"""
    print("🔍 Comprehensive test of payment notification badge...")
    
    try:
        # Setup admin user
        admin_role = Role.objects.get(role_name='Admin')
        admin_user = User.objects.filter(role=admin_role, is_superuser=True).first()
        
        if not admin_user:
            print("❌ No admin user found")
            return
        
        # Clean up any existing test data first
        PaymentProof.objects.filter(user__email__startswith='badge_test').delete()
        User.objects.filter(email__startswith='badge_test').delete()
        
        print("✅ Cleaned up any existing test data")
        
        # Test 1: No pending payments
        print("\n📋 TEST 1: No pending payments")
        current_pending = PaymentProof.objects.filter(status='pending').count()
        print(f"   Current pending payments: {current_pending}")
        
        with_badge = test_badge_appearance(admin_user, expected_count=current_pending)
        print(f"   with_badge result: {with_badge}, type: {type(with_badge)}")
        
        if current_pending == 0:
            if with_badge == True:  # Explicitly check for True
                print("✅ TEST 1 PASSED: No badge when no pending payments")
            else:
                print("❌ TEST 1 FAILED: Badge appears when it shouldn't")
        else:
            if with_badge:
                print(f"✅ TEST 1 PASSED: Badge correctly shows {current_pending} pending payments")
            else:
                print(f"❌ TEST 1 FAILED: Badge should show {current_pending} but doesn't appear")
        
        # Test 2: Create some pending payments
        print("\n📋 TEST 2: With pending payments")
        
        # Create test users and payments
        visitor_role = Role.objects.get(role_name='Visitor')
        package = SubscriptionPackage.objects.filter(is_active=True).first()
        
        if not package:
            print("❌ No package found for test")
            return
        
        test_users = []
        for i in range(2):
            user = User.objects.create(
                email=f'badge_test_{i}@example.com',
                username=f'badge_test_{i}',
                first_name=f'Badge',
                last_name=f'Test{i}',
                role=visitor_role
            )
            test_users.append(user)
        
        # Create pending payments
        from django.utils import timezone
        
        for user in test_users:
            PaymentProof.objects.create(
                user=user,
                package=package,
                status='pending',
                amount_paid=package.price,
                payment_method='Bank Transfer',
                payment_date=timezone.now(),
                notes='Test payment for badge'
            )
        
        new_pending = PaymentProof.objects.filter(status='pending').count()
        print(f"   Created test payments. Total pending: {new_pending}")
        
        with_badge = test_badge_appearance(admin_user, expected_count=new_pending)
        
        if with_badge and new_pending > 0:
            print("✅ TEST 2 PASSED: Badge appears with correct count")
        else:
            print("❌ TEST 2 FAILED: Badge doesn't appear or count is wrong")
        
        # Test 3: Approve one payment
        print("\n📋 TEST 3: After approving one payment")
        
        # Approve one payment
        payment_to_approve = PaymentProof.objects.filter(user__in=test_users).first()
        payment_to_approve.status = 'approved'
        payment_to_approve.save()
        remaining_pending = PaymentProof.objects.filter(status='pending').count()
        print(f"   Approved one payment. Remaining pending: {remaining_pending}")
        
        with_badge = test_badge_appearance(admin_user, expected_count=remaining_pending)
        
        if remaining_pending > 0 and with_badge:
            print("✅ TEST 3 PASSED: Badge count updated correctly")
        elif remaining_pending == 0 and not with_badge:
            print("✅ TEST 3 PASSED: Badge hidden when no pending payments")
        else:
            print("❌ TEST 3 FAILED: Badge count not updated correctly")
        
        # Cleanup
        PaymentProof.objects.filter(user__in=test_users).delete()
        User.objects.filter(id__in=[u.id for u in test_users]).delete()
        print("\n🧹 Cleaned up test data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_badge_appearance(admin_user, expected_count):
    """Test apakah badge muncul dengan count yang benar"""
    from django.test.utils import override_settings
    
    with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
        client = Client()
        client.force_login(admin_user)
        
        response = client.get('/')
        
        if response.status_code != 200:
            print(f"   ❌ Failed to get dashboard: {response.status_code}")
            return False
        
        content = response.content.decode('utf-8')
        
        # Look for red badge
        badge_pattern = r'bg-red-500[^>]*>([^<]+)<'
        badge_match = re.search(badge_pattern, content)
        
        if badge_match:
            badge_text = badge_match.group(1).strip()
            try:
                badge_number = int(badge_text)
                print(f"   🔴 Badge found with number: {badge_number}")
                
                if badge_number == expected_count:
                    print(f"   ✅ Badge count matches expected: {expected_count}")
                    return True
                else:
                    print(f"   ❌ Badge count mismatch. Expected: {expected_count}, Got: {badge_number}")
                    return False
                    
            except ValueError:
                print(f"   ⚠️  Badge found but content is not a number: '{badge_text}'")
                return False
        else:
            print(f"   ⚪ No badge found (expected count: {expected_count})")
            if expected_count == 0:
                print(f"   ✅ Returning True (no badge needed)")
                return True
            else:
                print(f"   ❌ Returning False (badge should be there)")
                return False

if __name__ == '__main__':
    test_payment_badge_comprehensive()
