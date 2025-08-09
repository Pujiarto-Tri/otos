#!/usr/bin/env python
"""
Test script to verify Vercel setup works correctly
"""
import os
import sys
from pathlib import Path

def test_django_setup():
    """Test if Django can be imported and configured"""
    try:
        # Add project to path
        project_dir = Path(__file__).resolve().parent
        sys.path.insert(0, str(project_dir))
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
        
        # Import Django
        import django
        from django.core.wsgi import get_wsgi_application
        
        # Setup Django
        django.setup()
        
        # Get WSGI application
        app = get_wsgi_application()
        
        print("✅ Django setup successful!")
        print(f"✅ WSGI application created: {app}")
        print(f"✅ Django version: {django.get_version()}")
        
        # Test settings
        from django.conf import settings
        print(f"✅ Settings module: {settings.SETTINGS_MODULE}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        print(f"✅ Static root: {settings.STATIC_ROOT}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_imports():
    """Test if API files can be imported"""
    try:
        # Test api/index.py
        from api.index import app, handler
        print("✅ api/index.py imports successful!")
        print(f"✅ app: {app}")
        print(f"✅ handler: {handler}")
        
        return True
        
    except Exception as e:
        print(f"❌ API import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Testing Vercel setup...")
    print("-" * 50)
    
    django_ok = test_django_setup()
    print("-" * 50)
    
    api_ok = test_api_imports()
    print("-" * 50)
    
    if django_ok and api_ok:
        print("🎉 All tests passed! Vercel setup should work.")
    else:
        print("💥 Some tests failed. Please check the errors above.")
