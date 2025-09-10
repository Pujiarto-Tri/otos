#!/usr/bin/env python

import os
import requests

def test_vercel_blob_put():
    """Test Vercel Blob using PUT method (simpler approach)"""
    token = os.environ.get('VERCEL_BLOB_TOKEN')
    if not token:
        print("VERCEL_BLOB_TOKEN not found")
        return
    
    # Use PUT method directly to blob.vercel-storage.com
    filename = 'test_files/test_put.txt'
    url = f'https://blob.vercel-storage.com/{filename}'
    
    headers = {
        'Authorization': f'Bearer {token}',
        'x-content-type': 'text/plain'
    }
    
    data = b"Hello from PUT method test!"
    
    try:
        print(f"Uploading to: {url}")
        resp = requests.put(url, data=data, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        if resp.status_code in [200, 201]:
            try:
                response_data = resp.json()
                print(f"Upload successful: {response_data}")
                
                # Test the download URL
                download_url = response_data.get('url') or response_data.get('downloadUrl')
                if download_url:
                    print(f"Testing download URL: {download_url}")
                    test_resp = requests.get(download_url)
                    print(f"Download status: {test_resp.status_code}")
                    print(f"Download content: {test_resp.text}")
                
            except Exception as e:
                print(f"Could not parse JSON response: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vercel_blob_put()
