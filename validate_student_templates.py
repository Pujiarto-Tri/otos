#!/usr/bin/env python
"""
Template validation script for student dashboard components
"""
import os
import sys

# Add the project directory to Python path
project_dir = r'c:\Users\ajied\Project\otos'
sys.path.insert(0, project_dir)

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

import django
django.setup()

from django.template.loader import get_template
from django.template import TemplateDoesNotExist

def check_template_exists(template_path):
    """Check if a template exists and can be loaded"""
    try:
        template = get_template(template_path)
        return True, f"✅ {template_path} - OK"
    except TemplateDoesNotExist as e:
        return False, f"❌ {template_path} - MISSING: {e}"
    except Exception as e:
        return False, f"⚠️ {template_path} - ERROR: {e}"

def main():
    """Check all student dashboard component templates"""
    templates_to_check = [
        'home.html',
        'dashboards/student_dashboard.html',
        'components/subscription_status_alert.html',
        'components/pending_payment_alert.html',
        'components/access_restriction_notice.html',
        'components/ongoing_test_alert.html',
        'components/stat_card.html',
        'components/motivational_message.html',
        'components/recent_tests.html',
        'components/popular_categories.html',
        'components/quick_action.html'
    ]
    
    print("🔍 Checking student dashboard template components...")
    print("=" * 60)
    
    all_ok = True
    for template_path in templates_to_check:
        exists, message = check_template_exists(template_path)
        print(message)
        if not exists:
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("🎉 All student dashboard components are available!")
        print("✨ The student dashboard should render without TemplateDoesNotExist errors.")
        print("🚀 Student dashboard is ready for use.")
    else:
        print("⚠️ Some templates are missing or have issues.")
        print("📝 Please create the missing components before testing.")
    
    return all_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
