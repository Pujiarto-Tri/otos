#!/usr/bin/env python
"""
Template validation script for admin dashboard components
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
    """Check all admin dashboard component templates"""
    templates_to_check = [
        'home.html',
        'dashboards/admin_dashboard.html',
        'components/welcome_header.html',
        'components/public_home.html',
        'components/modals_and_scripts.html',
        'components/admin/payment_status_overview.html',
        'components/admin/sales_trend_chart.html',
        'components/admin/popular_packages.html',
        'components/admin/recent_activities.html',
        'components/admin/management_menu.html',
        'components/admin/quick_actions.html',
        'components/quick_action.html'
    ]
    
    print("🔍 Checking admin dashboard template components...")
    print("=" * 60)
    
    all_ok = True
    for template_path in templates_to_check:
        exists, message = check_template_exists(template_path)
        print(message)
        if not exists:
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("🎉 All admin dashboard components are available!")
        print("✨ The modular template structure is working correctly.")
        print("🚀 Admin dashboard should render without TemplateDoesNotExist errors.")
    else:
        print("⚠️ Some templates are missing or have issues.")
        print("📝 Please create the missing components before testing.")
    
    return all_ok

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
