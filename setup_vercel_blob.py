#!/usr/bin/env python

"""
Script untuk membantu setup Vercel Blob Storage

Instruksi untuk mendapatkan token Vercel Blob yang benar:

1. Buka https://vercel.com/dashboard
2. Pilih project Anda (otos)
3. Buka tab "Storage" 
4. Klik "Connect Database"
5. Pilih "Blob" dan klik "Continue"
6. Beri nama blob store (misalnya "otos-media")
7. Pilih region yang dekat dengan users Anda
8. Setelah dibuat, Anda akan mendapat environment variable:
   BLOB_READ_WRITE_TOKEN=vercel_blob_rw_XXXXXXXXXXXXXXXXXXXXXXXXXX

9. Copy token tersebut dan set sebagai environment variable:
   - Untuk development lokal: tambahkan ke .env file
   - Untuk production: sudah otomatis tersedia di Vercel

10. Token yang benar biasanya dimulai dengan "vercel_blob_rw_" dan panjang 60+ karakter

Current token analysis:
"""

import os

def analyze_token():
    tokens = {
        'BLOB_READ_WRITE_TOKEN': os.environ.get('BLOB_READ_WRITE_TOKEN'),
        'VERCEL_BLOB_TOKEN': os.environ.get('VERCEL_BLOB_TOKEN'),
    }
    
    print("Current environment variables:")
    for name, value in tokens.items():
        if value:
            print(f"  {name}: {value[:10]}...{value[-10:]} (length: {len(value)})")
            if name == 'BLOB_READ_WRITE_TOKEN' and value.startswith('vercel_blob_rw_'):
                print(f"    ✓ {name} looks valid!")
            elif name == 'VERCEL_BLOB_TOKEN' and len(value) > 50:
                print(f"    ? {name} might be valid")
            else:
                print(f"    ✗ {name} looks invalid")
        else:
            print(f"  {name}: Not set")
    
    print("\nNext steps:")
    print("1. If you don't have a valid token, follow the instructions above")
    print("2. Set the token as BLOB_READ_WRITE_TOKEN environment variable")
    print("3. Re-deploy your application to Vercel")
    print("4. Test the image upload functionality")

if __name__ == "__main__":
    analyze_token()
