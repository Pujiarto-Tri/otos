#!/usr/bin/env python

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

import requests
from django.core.files.base import ContentFile

def test_vercel_api_directly():
    """Test Vercel Blob API directly"""
    token = os.environ.get('VERCEL_BLOB_TOKEN')
    if not token:
        print("VERCEL_BLOB_TOKEN not found")
        return
    
    # Create upload session
    endpoint = 'https://api.vercel.com/v1/blob/uploads'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Step 1: Create upload session
        print("Creating upload session...")
        resp = requests.post(endpoint, headers=headers, json={'name': 'test_direct.txt'})
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"Upload info: {data}")
            
            # Step 2: Upload file
            upload_url = data.get('uploadURL') or data.get('url') or data.get('upload_url')
            if upload_url:
                print(f"Uploading to: {upload_url}")
                put_resp = requests.put(upload_url, data=b"Hello from direct API test!")
                print(f"Upload status: {put_resp.status_code}")
                print(f"Upload response: {put_resp.text}")
                
                # Get the public URL
                public_url = data.get('url') or data.get('fileUrl') or data.get('cdnUrl')
                if public_url:
                    print(f"Public URL: {public_url}")
                    
                    # Test the public URL
                    print("Testing public URL...")
                    test_resp = requests.get(public_url)
                    print(f"Public URL status: {test_resp.status_code}")
                    print(f"Public URL content: {test_resp.text}")
                else:
                    print("No public URL found in response")
            else:
                print("No upload URL found in response")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vercel_api_directly()
