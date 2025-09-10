#!/usr/bin/env python

import os
import django
from django.conf import settings

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

def debug_default_storage():
    print("=== Default Storage Debug ===")
    print(f"default_storage type: {type(default_storage)}")
    print(f"default_storage class: {default_storage.__class__}")
    print(f"DEFAULT_FILE_STORAGE setting: {getattr(settings, 'DEFAULT_FILE_STORAGE', '(not set)')}")
    
    # Check if storage has our custom attributes
    if hasattr(default_storage, 'token'):
        print(f"Storage token: {default_storage.token[:20] if default_storage.token else '(not set)'}...")
    if hasattr(default_storage, 'use_vercel'):
        print(f"Storage use_vercel: {default_storage.use_vercel}")
    
    # Test upload with explicit debugging
    test_content = ContentFile(b"debug-test-content", name="debug_test.txt")
    
    try:
        print("\n=== Testing Upload ===")
        filename = default_storage.save("test_debug/debug_test.txt", test_content)
        print(f"Returned filename: {filename}")
        
        url = default_storage.url(filename)
        print(f"Generated URL: {url}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_default_storage()
