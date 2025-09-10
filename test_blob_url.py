#!/usr/bin/env python

import requests

def test_vercel_blob_url():
    # URL dari test sebelumnya
    url = "https://gjf1jr5lh1wkxear.public.blob.vercel-storage.com/test_files%5Ctest_direct_hBHXMgK-Gpcp9Uvk1k6vKgeVGodK4dcYNXRRBG.txt"
    
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Vercel Blob URL dapat diakses dengan sukses!")
        else:
            print("❌ Vercel Blob URL tidak dapat diakses")
            
    except Exception as e:
        print(f"Error accessing URL: {e}")

if __name__ == "__main__":
    test_vercel_blob_url()
