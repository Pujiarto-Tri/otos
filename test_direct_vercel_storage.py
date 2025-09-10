#!/usr/bin/env python

import os
import django
from django.conf import settings

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Set environment variables explicitly
os.environ['VERCEL'] = '1'
os.environ['VERCEL_URL'] = 'otos-green.vercel.app'

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.storage import VercelBlobStorage
from django.core.files.base import ContentFile

def test_direct_vercel_storage():
    print("=== Direct Vercel Storage Test ===")
    
    # Create storage instance directly
    storage = VercelBlobStorage()
    
    print(f"Storage token: {storage.token[:20] if storage.token else '(not set)'}...")
    print(f"Storage use_vercel: {storage.use_vercel}")
    
    # Test upload directly
    test_content = ContentFile(b"Direct upload test to Vercel Blob", name="direct_test.txt")
    
    try:
        print("\n=== Testing Direct Upload ===")
        filename = storage.save("payment_proofs/direct_test.jpg", test_content)
        print(f"Returned filename: {filename}")
        
        url = storage.url(filename)
        print(f"Generated URL: {url}")
        
        # If it's a Vercel URL, test access
        if filename.startswith('http'):
            import requests
            try:
                response = requests.get(url)
                print(f"HTTP GET status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ File dapat diakses!")
                    print(f"Content: {response.text}")
                else:
                    print("❌ File tidak dapat diakses")
            except Exception as e:
                print(f"Error testing HTTP access: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_vercel_storage()
