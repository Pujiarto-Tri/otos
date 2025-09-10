#!/usr/bin/env python

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from otosapp.storage import VercelBlobStorage

def test_vercel_blob_directly():
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', '(not set)')}")
    
    # Test storage directly
    storage = VercelBlobStorage()
    test_content = ContentFile(b"Hello Vercel Blob Direct Test!", name="test_direct.txt")
    
    try:
        # Try to save a test file
        filename = storage.save("test_files/test_direct.txt", test_content)
        print(f"File saved as: {filename}")
        
        # Try to get URL
        url = storage.url(filename)
        print(f"File URL: {url}")
        
        # Test if file exists
        exists = storage.exists(filename)
        print(f"File exists: {exists}")
        
    except Exception as e:
        print(f"Error during storage test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vercel_blob_directly()
