# verify_vercel_blob.py (template)
import os
import requests

token = os.environ.get("VERCEL_BLOB_TOKEN")
if not token:
    raise SystemExit("VERCEL_BLOB_TOKEN not set in env")

# TODO: ganti ENDPOINT dengan endpoint Vercel Blob yang sesuai
ENDPOINT = "https://api.vercel.com/v1/blob/uploads"  # <-- periksa dokumentasi Vercel dan ganti sesuai

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
}

print("Sending test request to Vercel API endpoint:", ENDPOINT)
resp = requests.post(ENDPOINT, headers=headers, json={"name": "test.txt"})
print("Status:", resp.status_code)
print("Response:", resp.text)