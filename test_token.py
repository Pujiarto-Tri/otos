#!/usr/bin/env python

import requests
import os

def test_token_format():
    """Test different token formats"""
    token = os.environ.get('VERCEL_BLOB_TOKEN')
    print(f"Token: {token}")
    print(f"Token length: {len(token) if token else 0}")
    
    # Test with different endpoint
    endpoints = [
        'https://blob.vercel-storage.com/test.txt',
        'https://api.vercel.com/v1/blob/uploads',
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'text/plain'
        }
        
        try:
            if 'blob.vercel-storage.com' in endpoint:
                # PUT request
                resp = requests.put(endpoint, data=b"test", headers=headers)
            else:
                # POST request
                resp = requests.post(endpoint, json={'name': 'test.txt'}, headers=headers)
            
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_token_format()
