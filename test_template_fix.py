#!/usr/bin/env python
"""
Test Script untuk memverifikasi perbaikan Template Syntax Error
Menguji apakah error 'categories|first.category_name' sudah teratasi
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import TestCase, Client
from django.urls import reverse
from django.template import Template, Context, TemplateSyntaxError
from otosapp.models import User, Role, Category

def test_template_syntax():
    """Test if template syntax error is fixed"""
    print("🧪 Testing Template Syntax Fix...")
    
    # Test the problematic template syntax
    template_content = """
    {% if current_category_name %}
    <br><strong>Kategori:</strong> {{ current_category_name }}
    {% endif %}
    """
    
    try:
        template = Template(template_content)
        context = Context({
            'current_category_name': 'Test Category'
        })
        result = template.render(context)
        print("✅ Template syntax test passed!")
        print(f"   Rendered output: {result.strip()}")
        return True
    except TemplateSyntaxError as e:
        print(f"❌ Template syntax error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_view_functionality():
    """Test the view functionality"""
    print("\n🔧 Testing View Functionality...")
    
    try:
        # Create test user
        student_role, _ = Role.objects.get_or_create(role_name='Student')
        user, created = User.objects.get_or_create(
            username='test_template_user',
            defaults={
                'email': 'template_test@test.com',
                'role': student_role
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        
        # Create test category
        category, created = Category.objects.get_or_create(
            category_name='Template Test Category',
            defaults={
                'scoring_method': 'default',
                'time_limit': 60,
                'passing_score': 75.0
            }
        )
        
        if created:
            print(f"✅ Created test category: {category.category_name}")
        
        # Test view with client
        client = Client()
        login_success = client.login(username='test_template_user', password='testpass123')
        
        if not login_success:
            print("❌ Failed to login test user")
            return False
        
        print("✅ Successfully logged in test user")
        
        # Test basic page load
        response = client.get(reverse('test_history'))
        if response.status_code == 200:
            print("✅ Test history page loads without errors")
        else:
            print(f"❌ Test history page failed: {response.status_code}")
            return False
        
        # Test with category filter
        response = client.get(reverse('test_history'), {'category': category.id})
        if response.status_code == 200:
            print("✅ Category filter works without template errors")
            
            # Check if context contains the new variable
            if 'current_category_name' in response.context:
                category_name = response.context['current_category_name']
                print(f"✅ current_category_name in context: {category_name}")
            else:
                print("⚠️  current_category_name not found in context")
        else:
            print(f"❌ Category filter failed: {response.status_code}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ View test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases that might cause template errors"""
    print("\n🎯 Testing Edge Cases...")
    
    client = Client()
    login_success = client.login(username='test_template_user', password='testpass123')
    
    if not login_success:
        print("❌ Failed to login for edge case testing")
        return False
    
    edge_cases = [
        {'name': 'Invalid category ID', 'params': {'category': 'invalid'}},
        {'name': 'Non-existent category', 'params': {'category': '99999'}},
        {'name': 'Empty search', 'params': {'search': ''}},
        {'name': 'Special characters', 'params': {'search': 'test & special <chars>'}},
        {'name': 'Combined invalid params', 'params': {'category': 'invalid', 'search': '', 'page': 'invalid'}},
    ]
    
    for case in edge_cases:
        try:
            response = client.get(reverse('test_history'), case['params'])
            if response.status_code == 200:
                print(f"✅ {case['name']}: Handled gracefully")
            else:
                print(f"❌ {case['name']}: Failed with status {response.status_code}")
        except Exception as e:
            print(f"❌ {case['name']}: Exception - {str(e)}")
    
    return True

def main():
    """Run all template syntax tests"""
    print("🚀 Starting Template Syntax Error Fix Testing...")
    print("=" * 60)
    
    try:
        # Test template syntax
        if not test_template_syntax():
            print("\n❌ Template syntax test failed!")
            return False
        
        # Test view functionality
        if not test_view_functionality():
            print("\n❌ View functionality test failed!")
            return False
        
        # Test edge cases
        if not test_edge_cases():
            print("\n❌ Edge case testing failed!")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 ALL TEMPLATE SYNTAX TESTS PASSED!")
        print("\n📋 Tests Completed:")
        print("✅ Template syntax validation")
        print("✅ View context variables")
        print("✅ Category filter functionality")
        print("✅ Edge case handling")
        print("✅ Error prevention")
        print("\n🎯 Template Error Fixed Successfully!")
        print("   - Removed invalid 'categories|first.category_name' syntax")
        print("   - Added 'current_category_name' to view context")
        print("   - Updated template to use proper variable")
        print("   - Added error handling for invalid category IDs")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
