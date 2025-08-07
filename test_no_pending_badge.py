#!/usr/bin/env python
"""
Script untuk test bahwa badge tidak muncul ketika tidak ada pending payments
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import PaymentProof, Role

User = get_user_model()

def test_no_pending_payments():
    """Test bahwa badge tidak muncul ketika tidak ada pending payments"""
    print("🔍 Testing admin sidebar when no pending payments...")
    
    try:
        # Ensure no pending payments exist
        pending_count = PaymentProof.objects.filter(status='pending').count()
        print(f"📊 Current pending payments: {pending_count}")
        
        # Get admin user
        admin_role = Role.objects.get(role_name='Admin')
        admin_user = User.objects.filter(role=admin_role, is_superuser=True).first()
        
        if not admin_user:
            print("❌ No admin user found")
            return
        
        print(f"✅ Found admin user: {admin_user.email}")
        
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
                
                if pending_count == 0:
                    # Check that badge does NOT appear when no pending payments
                    if 'bg-red-500' not in content:
                        print("✅ SUCCESS: Red badge correctly hidden when no pending payments")
                    else:
                        print("⚠️  Red badge still appears when it shouldn't")
                        
                    if 'Payment Verification' in content:
                        print("✅ Payment Verification menu still visible (as expected)")
                    else:
                        print("⚠️  Payment Verification menu missing")
                else:
                    print(f"ℹ️  There are {pending_count} pending payments, so badge should appear")
                    
            else:
                print(f"❌ FAILED: Dashboard access failed with status {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_no_pending_payments()
