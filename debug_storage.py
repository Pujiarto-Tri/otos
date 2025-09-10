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

from otosapp.storage import VercelBlobStorage

def debug_storage():
    print("=== Environment Variables ===")
    print(f"BLOB_READ_WRITE_TOKEN: {os.environ.get('BLOB_READ_WRITE_TOKEN', '(not set)')}")
    print(f"VERCEL_BLOB_TOKEN: {os.environ.get('VERCEL_BLOB_TOKEN', '(not set)')}")
    print(f"VERCEL: {os.environ.get('VERCEL', '(not set)')}")
    print(f"VERCEL_URL: {os.environ.get('VERCEL_URL', '(not set)')}")
    
    print("\n=== Django Settings ===")
    print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', '(not set)')}")
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', '(not set)')}")
    print(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', '(not set)')}")
    
    print("\n=== Storage Instance ===")
    try:
        storage = VercelBlobStorage()
        print(f"Storage token: {storage.token[:20] if storage.token else '(not set)'}...")
        print(f"Storage use_vercel: {storage.use_vercel}")
    except Exception as e:
        print(f"Error creating storage: {e}")

if __name__ == "__main__":
    debug_storage()
