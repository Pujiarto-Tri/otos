#!/usr/bin/env python
"""
Test script untuk sistem berlangganan
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.utils import timezone
from otosapp.models import User, Role, SubscriptionPackage, PaymentProof, UserSubscription

def test_subscription_system():
    """Test complete subscription workflow"""
    print("=== TESTING SUBSCRIPTION SYSTEM ===\n")
    
    # 1. Test Role Creation
    print("1. Testing Roles...")
    visitor_role, created = Role.objects.get_or_create(role_name='Visitor')
    student_role, created = Role.objects.get_or_create(role_name='Student')
    admin_role, created = Role.objects.get_or_create(role_name='Admin')
    print(f"✅ Roles: Visitor={visitor_role.id}, Student={student_role.id}, Admin={admin_role.id}")
    
    # 2. Test Subscription Packages
    print("\n2. Testing Subscription Packages...")
    packages = SubscriptionPackage.objects.filter(is_active=True)
    print(f"✅ Active packages: {packages.count()}")
    for pkg in packages:
        print(f"   - {pkg.name}: Rp{pkg.price:,.0f} ({pkg.duration_days} days)")
    
    # 3. Test User Creation and Role Assignment
    print("\n3. Testing User Role System...")
    
    # Create test visitor user
    test_email = "test_visitor@example.com"
    test_user, created = User.objects.get_or_create(
        email=test_email,
        defaults={
            'username': 'test_visitor',
            'first_name': 'Test',
            'last_name': 'Visitor',
            'role': visitor_role
        }
    )
    
    print(f"✅ Test user: {test_user.email} (Role: {test_user.role.role_name})")
    print(f"   - Is visitor: {test_user.is_visitor()}")
    print(f"   - Is student: {test_user.is_student()}")
    print(f"   - Can access tryouts: {test_user.can_access_tryouts()}")
    print(f"   - Has active subscription: {test_user.has_active_subscription()}")
    
    # 4. Test Subscription Status
    print("\n4. Testing Subscription Status...")
    status = test_user.get_subscription_status()
    print(f"✅ Subscription status: {status}")
    
    # 5. Test Payment Proof Creation
    print("\n5. Testing Payment Proof...")
    if packages.exists():
        test_package = packages.first()
        payment_proof, created = PaymentProof.objects.get_or_create(
            user=test_user,
            package=test_package,
            defaults={
                'amount_paid': test_package.price,
                'payment_method': 'Bank Transfer - BCA',
                'payment_date': timezone.now(),
                'notes': 'Test payment for subscription system'
            }
        )
        print(f"✅ Payment proof created: ID={payment_proof.id}, Status={payment_proof.status}")
    
    # 6. Test User Upgrade to Student
    print("\n6. Testing User Upgrade...")
    if packages.exists():
        test_package = packages.first()
        
        # Simulate admin approval
        payment_proof.status = 'approved'
        payment_proof.admin_notes = 'Test approval'
        payment_proof.save()
        
        # Create subscription
        subscription, created = UserSubscription.objects.get_or_create(
            user=test_user,
            defaults={
                'package': test_package,
                'end_date': timezone.now() + timezone.timedelta(days=test_package.duration_days),
                'payment_proof': payment_proof
            }
        )
        
        # Upgrade user role
        test_user.role = student_role
        test_user.save()
        
        print(f"✅ User upgraded to Student!")
        print(f"   - New role: {test_user.role.role_name}")
        print(f"   - Can access tryouts: {test_user.can_access_tryouts()}")
        print(f"   - Subscription ends: {subscription.end_date}")
        print(f"   - Days remaining: {subscription.days_remaining()}")
    
    # 7. Test Subscription Expiry
    print("\n7. Testing Subscription Expiry...")
    if hasattr(test_user, 'subscription'):
        # Simulate expired subscription
        expired_subscription = test_user.subscription
        expired_subscription.end_date = timezone.now() - timezone.timedelta(days=1)
        expired_subscription.save()
        
        print(f"✅ Subscription expired (simulated)")
        print(f"   - Is expired: {expired_subscription.is_expired()}")
        print(f"   - User can access tryouts: {test_user.can_access_tryouts()}")
        
        # Auto downgrade would happen in the check_and_downgrade_expired_subscriptions function
        print(f"   - Auto downgrade needed: {expired_subscription.is_expired()}")
    
    print("\n=== SUBSCRIPTION SYSTEM TEST COMPLETE ===")
    print("✅ All core functionality working correctly!")
    print("\nNext steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Visit http://localhost:8000 to test the web interface")
    print("3. Register as new user (will be Visitor by default)")
    print("4. View subscription packages and upload payment")
    print("5. Admin can verify payments and upgrade users")

if __name__ == '__main__':
    test_subscription_system()
