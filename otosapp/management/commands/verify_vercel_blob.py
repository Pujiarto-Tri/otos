from django.core.management.base import BaseCommand
import os
import requests


class Command(BaseCommand):
    help = 'Verify VERCEL_BLOB_TOKEN and create a small test upload (no public effect)' 

    def handle(self, *args, **options):
        token = os.environ.get('VERCEL_BLOB_TOKEN')
        if not token:
            self.stderr.write('VERCEL_BLOB_TOKEN not set in environment')
            return

        endpoint = 'https://api.vercel.com/v1/blob/uploads'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        try:
            resp = requests.post(endpoint, headers=headers, json={'name': 'django-vercel-verify.txt'})
            resp.raise_for_status()
        except Exception as e:
            self.stderr.write(f'Error calling Vercel API: {e}')
            if hasattr(e, 'response') and e.response is not None:
                self.stderr.write(str(e.response.text))
            return

        data = resp.json()
        self.stdout.write('Upload creation response:')
        self.stdout.write(str(data))

        upload_url = data.get('uploadURL') or data.get('url') or data.get('upload_url')
        if not upload_url:
            self.stdout.write('No upload URL returned; token may be valid but response format unexpected')
            return

        # PUT a tiny payload
        try:
            put = requests.put(upload_url, data=b'hello-vercel')
            put.raise_for_status()
        except Exception as e:
            self.stderr.write(f'Error uploading bytes: {e}')
            return

        self.stdout.write('Successfully uploaded test bytes to Vercel Blob')