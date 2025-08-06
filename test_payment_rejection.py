#!/usr/bin/env python
"""
Test script to verify payment rejection functionality
This script tests that when an approved payment is rejected, 
the user's subscription is properly deactivated.
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import TestCase
from django.contrib.auth import get_user_model
from otosapp.models import Role, SubscriptionPackage, PaymentProof, UserSubscription
from otosapp.views import deactivate_user_subscription
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def cleanup_test_data():
    """Clean up any leftover test data"""
    print("🧹 Cleaning up any existing test data...")
    
    # Delete test users
    User.objects.filter(email__contains='@example.com').delete()
    
    # Delete test packages
    SubscriptionPackage.objects.filter(name__contains='Test').delete()
    SubscriptionPackage.objects.filter(name__contains='Package').delete()
    
    print("✅ Test data cleanup completed.")

def test_payment_rejection_deactivates_subscription():
    """Test that rejecting an approved payment deactivates subscription"""
    print("🧪 Testing Payment Rejection Functionality...")
    
    # Create roles
    visitor_role, _ = Role.objects.get_or_create(role_name='Visitor')
    student_role, _ = Role.objects.get_or_create(role_name='Student')
    
    # Generate unique email to avoid conflicts
    import time
    unique_id = str(int(time.time() * 1000))
    email = f'testuser_{unique_id}@example.com'
    
    # Create test user
    test_user = User.objects.create_user(
        username=email,
        email=email,
        first_name='Test',
        last_name='User',
        role=student_role  # Start as student
    )
    
    # Create test package
    test_package = SubscriptionPackage.objects.create(
        name=f'Test Package {unique_id}',
        description='Test package for testing',
        price=Decimal('100000'),
        duration_days=30,
        is_active=True
    )
    
    # Create approved payment
    payment = PaymentProof.objects.create(
        user=test_user,
        package=test_package,
        amount_paid=Decimal('100000'),
        payment_method='Bank Transfer',
        payment_date=timezone.now(),
        status='approved'
    )
    
    # Create active subscription
    subscription = UserSubscription.objects.create(
        user=test_user,
        package=test_package,
        end_date=timezone.now() + timezone.timedelta(days=30),
        payment_proof=payment,
        is_active=True
    )
    
    print(f"✅ Created test user: {test_user.email}")
    print(f"✅ User role: {test_user.role.role_name}")
    print(f"✅ Created subscription: {subscription.id} (Active: {subscription.is_active})")
    print(f"✅ Payment status: {payment.status}")
    
    # Test: Deactivate subscription when payment is rejected
    print("\n🔄 Testing deactivation...")
    deactivate_user_subscription(test_user, payment)
    
    # Refresh objects from database
    test_user.refresh_from_db()
    subscription.refresh_from_db()
    
    print(f"📊 Results after deactivation:")
    print(f"   - User role: {test_user.role.role_name}")
    print(f"   - Subscription active: {subscription.is_active}")
    
    # Assertions
    assert test_user.role.role_name == 'Visitor', f"Expected Visitor, got {test_user.role.role_name}"
    assert not subscription.is_active, f"Expected inactive subscription, got active={subscription.is_active}"
    
    print("✅ Test passed! Payment rejection properly deactivates subscription and downgrades user.")
    
    # Cleanup
    subscription.delete()
    payment.delete()
    test_package.delete()
    test_user.delete()
    print("🧹 Cleanup completed.")

def test_payment_rejection_with_subscription_update():
    """Test that rejecting payment when user has updated subscription"""
    print("\n🧪 Testing Payment Rejection with Updated Subscription...")
    
    # Create roles
    visitor_role, _ = Role.objects.get_or_create(role_name='Visitor')
    student_role, _ = Role.objects.get_or_create(role_name='Student')
    
    # Generate unique email to avoid conflicts
    import time
    unique_id = str(int(time.time() * 1000))
    email = f'testuser2_{unique_id}@example.com'
    
    # Create test user
    test_user = User.objects.create_user(
        username=email,
        email=email,
        first_name='Test',
        last_name='User2',
        role=student_role
    )
    
    # Create test packages
    package1 = SubscriptionPackage.objects.create(
        name=f'Package 1 {unique_id}',
        description='First package',
        price=Decimal('100000'),
        duration_days=30,
        is_active=True
    )
    
    package2 = SubscriptionPackage.objects.create(
        name=f'Package 2 {unique_id}', 
        description='Second package',
        price=Decimal('150000'),
        duration_days=60,
        is_active=True
    )
    
    # Create first approved payment
    payment1 = PaymentProof.objects.create(
        user=test_user,
        package=package1,
        amount_paid=Decimal('100000'),
        payment_method='Bank Transfer',
        payment_date=timezone.now(),
        status='approved'
    )
    
    # Create subscription with first payment
    subscription = UserSubscription.objects.create(
        user=test_user,
        package=package1,
        end_date=timezone.now() + timezone.timedelta(days=30),
        payment_proof=payment1,
        is_active=True
    )
    
    # Create second approved payment (upgrade)
    payment2 = PaymentProof.objects.create(
        user=test_user,
        package=package2,
        amount_paid=Decimal('150000'),
        payment_method='E-Wallet',
        payment_date=timezone.now(),
        status='approved'
    )
    
    # Update subscription to new package (simulate upgrade)
    subscription.package = package2
    subscription.payment_proof = payment2
    subscription.end_date = timezone.now() + timezone.timedelta(days=60)
    subscription.save()
    
    print(f"✅ Created user with updated subscription")
    print(f"   - Original payment: {payment1.package.name}")
    print(f"   - Current subscription: {subscription.package.name}")
    print(f"   - Current payment proof: {subscription.payment_proof.package.name}")
    
    # Test: Reject the original payment (should not affect current subscription)
    print("\n🔄 Rejecting original payment...")
    deactivate_user_subscription(test_user, payment1)
    
    # Refresh objects
    test_user.refresh_from_db()
    subscription.refresh_from_db()
    
    print(f"📊 Results after rejecting original payment:")
    print(f"   - User role: {test_user.role.role_name}")
    print(f"   - Subscription active: {subscription.is_active}")
    print(f"   - Subscription package: {subscription.package.name}")
    
    # Assertions - subscription should remain active since it's linked to different payment
    assert test_user.role.role_name == 'Student', f"Expected Student, got {test_user.role.role_name}"
    assert subscription.is_active, f"Expected active subscription, got inactive"
    
    print("✅ Test passed! Rejecting old payment doesn't affect current subscription.")
    
    # Test: Now reject the current payment
    print("\n🔄 Rejecting current payment...")
    deactivate_user_subscription(test_user, payment2)
    
    # Refresh objects
    test_user.refresh_from_db()
    subscription.refresh_from_db()
    
    print(f"📊 Results after rejecting current payment:")
    print(f"   - User role: {test_user.role.role_name}")
    print(f"   - Subscription active: {subscription.is_active}")
    
    # Assertions - subscription should be deactivated and user downgraded
    assert test_user.role.role_name == 'Visitor', f"Expected Visitor, got {test_user.role.role_name}"
    assert not subscription.is_active, f"Expected inactive subscription, got active"
    
    print("✅ Test passed! Rejecting current payment deactivates subscription.")
    
    # Cleanup
    subscription.delete()
    payment1.delete()
    payment2.delete()
    package1.delete()
    package2.delete()
    test_user.delete()
    print("🧹 Cleanup completed.")

if __name__ == "__main__":
    try:
        # Clean up any existing test data first
        cleanup_test_data()
        
        # Run tests
        test_payment_rejection_deactivates_subscription()
        test_payment_rejection_with_subscription_update()
        print("\n🎉 All tests passed! Payment rejection functionality is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Final cleanup
        cleanup_test_data()
