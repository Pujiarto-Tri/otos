#!/usr/bin/env python

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

def test_image_upload():
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', '(not set)')}")
    
    # Create a test image file (simple content)
    test_image_content = b"fake-image-data-for-testing-vercel-blob"
    test_content = ContentFile(test_image_content, name="test_payment_proof.jpg")
    
    try:
        # Try to save a test payment proof image
        filename = default_storage.save("payment_proofs/test_payment_proof.jpg", test_content)
        print(f"File saved as: {filename}")
        
        # Try to get URL
        url = default_storage.url(filename)
        print(f"File URL: {url}")
        
        # Test if file exists
        exists = default_storage.exists(filename)
        print(f"File exists: {exists}")
        
        # If it's a Vercel Blob URL, test access
        if filename.startswith('http'):
            import requests
            try:
                response = requests.head(url, timeout=10)
                print(f"HTTP HEAD status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ File dapat diakses via HTTP!")
                else:
                    print("❌ File tidak dapat diakses via HTTP")
            except Exception as e:
                print(f"Error testing HTTP access: {e}")
        
    except Exception as e:
        print(f"Error during storage test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_image_upload()
