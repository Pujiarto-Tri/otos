#!/usr/bin/env python
"""
Script untuk debug nilai pending_payments_count
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from otosapp.models import PaymentProof, Role
from otosapp.context_processors import sidebar_context

User = get_user_model()

def debug_pending_payments():
    """Debug nilai pending_payments_count"""
    print("🔍 Debugging pending_payments_count value...")
    
    try:
        # Check database directly
        pending_count = PaymentProof.objects.filter(status='pending').count()
        print(f"📊 Direct database query - Pending payments: {pending_count}")
        
        # Get admin user
        admin_role = Role.objects.get(role_name='Admin')
        admin_user = User.objects.filter(role=admin_role, is_superuser=True).first()
        
        print(f"✅ Admin user: {admin_user.email}")
        print(f"   - is_authenticated: True (assumed)")
        print(f"   - is_superuser: {admin_user.is_superuser}")
        print(f"   - is_admin(): {admin_user.is_admin()}")
        
        # Test context processor directly
        from django.http import HttpRequest
        from django.contrib.auth.models import AnonymousUser
        
        request = HttpRequest()
        request.user = admin_user
        
        context = sidebar_context(request)
        print(f"📋 Context processor result: {context}")
        
        # Test with client
        from django.test.utils import override_settings
        
        with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
            client = Client()
            client.force_login(admin_user)
            
            # Get dashboard page with detailed debugging
            response = client.get('/')
            
            if response.status_code == 200:
                # Check specific content
                content = response.content.decode('utf-8')
                print(f"📄 Response content length: {len(content)} characters")
                
                # Look for the badge specifically
                import re
                badge_pattern = r'bg-red-500.*?>(\d+)<'
                badge_match = re.search(badge_pattern, content)
                
                if badge_match:
                    badge_number = badge_match.group(1)
                    print(f"🔴 Found red badge with number: {badge_number}")
                else:
                    print("✅ No red badge found (correct if no pending payments)")
                
                # Look for the if condition in rendered HTML
                if 'pending_payments_count' in content:
                    print("✅ Variable 'pending_payments_count' found in rendered HTML")
                    
                    # Look for specific patterns around the variable
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'pending_payments_count' in line:
                            print(f"📝 Line {i+1}: {line.strip()}")
                else:
                    print("⚠️  Variable 'pending_payments_count' not found in rendered HTML")
                    
            else:
                print(f"❌ Dashboard access failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    debug_pending_payments()
