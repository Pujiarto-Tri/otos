#!/usr/bin/env python

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def test_vercel_blob():
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', '(not set)')}")
    print(f"VERCEL_BLOB_TOKEN present: {'VERCEL_BLOB_TOKEN' in os.environ}")
    print(f"VERCEL present: {'VERCEL' in os.environ}")
    print(f"VERCEL_URL present: {'VERCEL_URL' in os.environ}")
    
    # Test storage
    test_content = ContentFile(b"Hello Vercel Blob Test!", name="test.txt")
    
    try:
        # Try to save a test file
        filename = default_storage.save("test_files/test.txt", test_content)
        print(f"File saved as: {filename}")
        
        # Try to get URL
        url = default_storage.url(filename)
        print(f"File URL: {url}")
        
        # Test if file exists
        exists = default_storage.exists(filename)
        print(f"File exists: {exists}")
        
    except Exception as e:
        print(f"Error during storage test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vercel_blob()
