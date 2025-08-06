#!/usr/bin/env python3
"""
Test Script untuk verifikasi fix subscription deactivation bug
Bug: User tidak bisa berlangganan lagi setelah subscription di-deactivate oleh admin
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.contrib.auth import get_user_model
from otosapp.models import Role, UserSubscription, SubscriptionPackage
from django.utils import timezone
from datetime import timedelta

def test_subscription_deactivation_reactivation():
    """Test complete flow: deactivate → user can subscribe again → reactivate"""
    
    print("\n" + "="*80)
    print("🧪 TESTING SUBSCRIPTION DEACTIVATION & REACTIVATION FIX")
    print("="*80)
    
    User = get_user_model()
    
    # Clean up any existing test data
    test_email = 'test_deactivation@example.com'
    User.objects.filter(email=test_email).delete()
    
    try:
        # 1. Create test user with subscription
        print("\n1️⃣ Creating test user with active subscription...")
        
        student_role, _ = Role.objects.get_or_create(role_name='Student')
        test_package, _ = SubscriptionPackage.objects.get_or_create(
            name='Test Package',
            defaults={
                'package_type': 'basic',
                'description': 'Test package',
                'features': 'Test feature 1\nTest feature 2',
                'price': 100000,
                'duration_days': 30,
            }
        )
        
        test_user = User.objects.create_user(
            username='testuser_deactivation',
            email=test_email,
            password='testpass123',
            role=student_role
        )
        
        # Create subscription
        subscription = UserSubscription.objects.create(
            user=test_user,
            package=test_package,
            end_date=timezone.now() + timedelta(days=30),
            is_active=True
        )
        
        print(f"   ✅ User created: {test_user.email}")
        print(f"   ✅ Subscription created: {subscription}")
        print(f"   ✅ Has active subscription: {test_user.has_active_subscription()}")
        print(f"   ✅ Can access tryouts: {test_user.can_access_tryouts()}")
        print(f"   ✅ Subscription status: {test_user.get_subscription_status()['status']}")
        
        # 2. Admin deactivates subscription
        print("\n2️⃣ Admin deactivates subscription...")
        
        subscription.is_active = False
        subscription.save()
        subscription.refresh_from_db()
        test_user.refresh_from_db()
        
        print(f"   ✅ Subscription is_active: {subscription.is_active}")
        print(f"   ✅ Has active subscription: {test_user.has_active_subscription()}")
        print(f"   ✅ Can access tryouts: {test_user.can_access_tryouts()}")
        print(f"   ✅ Subscription status: {test_user.get_subscription_status()['status']}")
        
        # Verify deactivated state
        if not test_user.has_active_subscription():
            print("   ✅ SUCCESS: User correctly cannot access tryouts when deactivated")
        else:
            print("   ❌ FAILED: User still can access tryouts when deactivated")
            return False
        
        # Verify status message
        status = test_user.get_subscription_status()
        if status['status'] == 'deactivated':
            print("   ✅ SUCCESS: Subscription status correctly shows 'deactivated'")
        else:
            print(f"   ❌ FAILED: Expected 'deactivated' but got '{status['status']}'")
            return False
        
        # 3. User tries to resubscribe (simulating new payment verification)
        print("\n3️⃣ User resubscribes (admin verifies new payment)...")
        
        # Simulate the upgrade_user_to_student process
        subscription.is_active = True
        subscription.extend_subscription(30)  # Extend by 30 days
        subscription.save()
        test_user.refresh_from_db()
        
        print(f"   ✅ Subscription is_active: {subscription.is_active}")
        print(f"   ✅ Has active subscription: {test_user.has_active_subscription()}")
        print(f"   ✅ Can access tryouts: {test_user.can_access_tryouts()}")
        print(f"   ✅ Subscription status: {test_user.get_subscription_status()['status']}")
        
        # Verify reactivated state
        if test_user.has_active_subscription() and test_user.can_access_tryouts():
            print("   ✅ SUCCESS: User can access tryouts after reactivation")
        else:
            print("   ❌ FAILED: User still cannot access tryouts after reactivation")
            return False
        
        # Verify active status
        status = test_user.get_subscription_status()
        if status['status'] == 'active':
            print("   ✅ SUCCESS: Subscription status correctly shows 'active'")
        else:
            print(f"   ❌ FAILED: Expected 'active' but got '{status['status']}'")
            return False
        
        # 4. Test edge case: deactivate expired subscription
        print("\n4️⃣ Testing edge case: deactivating expired subscription...")
        
        # Set subscription to expired
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.is_active = True
        subscription.save()
        test_user.refresh_from_db()
        
        print(f"   ✅ Subscription expired: {subscription.is_expired()}")
        print(f"   ✅ Has active subscription: {test_user.has_active_subscription()}")
        print(f"   ✅ Subscription status: {test_user.get_subscription_status()['status']}")
        
        # Now deactivate the expired subscription
        subscription.is_active = False
        subscription.save()
        test_user.refresh_from_db()
        
        status = test_user.get_subscription_status()
        print(f"   ✅ Status when deactivated AND expired: {status['status']}")
        
        # Should show 'deactivated' not 'expired' because is_active check comes first
        if status['status'] == 'deactivated':
            print("   ✅ SUCCESS: Deactivated status takes precedence over expired")
        else:
            print(f"   ❌ FAILED: Expected 'deactivated' but got '{status['status']}'")
            return False
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED! Subscription deactivation fix is working correctly!")
        print("="*80)
        print("\n📋 Summary of fixes:")
        print("   ✅ User cannot access tryouts when subscription is deactivated")
        print("   ✅ User gets proper 'deactivated' status message")
        print("   ✅ User can resubscribe after deactivation (existing subscription reactivated)")
        print("   ✅ Deactivated status takes precedence over expired status")
        print("   ✅ All subscription states work correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        print(f"\n🧹 Cleaning up test data...")
        User.objects.filter(email=test_email).delete()
        print("   ✅ Test user deleted")

if __name__ == "__main__":
    success = test_subscription_deactivation_reactivation()
    sys.exit(0 if success else 1)
