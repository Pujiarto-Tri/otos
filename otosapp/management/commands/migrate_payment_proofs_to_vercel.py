from django.core.management.base import BaseCommand
from django.conf import settings
from otosapp.models import PaymentProof
import os
import requests


class Command(BaseCommand):
    help = 'Upload local payment_proofs files to Vercel Blob and update PaymentProof.proof_image to public URL'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Limit number of files to migrate (0 = all)')
        parser.add_argument('--dry-run', action='store_true', help='Show actions without performing upload')

    def handle(self, *args, **options):
        token = os.environ.get('VERCEL_BLOB_TOKEN')
        if not token:
            self.stderr.write('VERCEL_BLOB_TOKEN not set in environment. Set it before running this command.')
            return

        limit = options.get('limit') or None
        dry_run = options.get('dry_run')

        qs = PaymentProof.objects.order_by('id')
        if limit:
            qs = qs[:limit]

        migrated = 0
        for p in qs:
            name = None
            try:
                name = p.proof_image.name
            except Exception:
                continue

            # Skip if already a URL
            if not name or name.startswith('http'):
                continue

            local_path = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), name)
            if not os.path.exists(local_path):
                self.stdout.write(f'SKIP id={p.id} local file not found: {local_path}')
                continue

            self.stdout.write(f'Processing id={p.id} file={local_path}')
            if dry_run:
                continue

            # Create upload session
            endpoint = 'https://api.vercel.com/v1/blob/uploads'
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            try:
                resp = requests.post(endpoint, headers=headers, json={'name': os.path.basename(name)})
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Print response body for debugging (403/401 details)
                body = ''
                try:
                    body = e.response.text
                except Exception:
                    pass
                self.stderr.write(f'Error creating upload for id={p.id}: {e} - response: {body}')
                continue
            except Exception as e:
                self.stderr.write(f'Error creating upload for id={p.id}: {e}')
                continue

            info = resp.json()
            upload_url = info.get('uploadURL') or info.get('upload_url') or info.get('url')
            if not upload_url:
                self.stderr.write(f'No upload URL returned for id={p.id}: {info}')
                continue

            # PUT file bytes
            try:
                with open(local_path, 'rb') as fh:
                    put = requests.put(upload_url, data=fh)
                    put.raise_for_status()
            except requests.exceptions.HTTPError as e:
                body = ''
                try:
                    body = e.response.text
                except Exception:
                    pass
                self.stderr.write(f'Error uploading bytes for id={p.id}: {e} - response: {body}')
                continue
            except Exception as e:
                self.stderr.write(f'Error uploading bytes for id={p.id}: {e}')
                continue

            public_url = info.get('url') or info.get('fileUrl') or info.get('cdnUrl')
            if not public_url:
                # Use a fallback pattern
                public_url = info.get('id') and f'https://vercel.storage/{info.get("id")}'

            if not public_url:
                self.stderr.write(f'Could not determine public URL for id={p.id} after upload: {info}')
                continue

            # Update DB: set proof_image.name to public_url string and save
            p.proof_image.name = public_url
            p.save(update_fields=['proof_image'])
            migrated += 1
            self.stdout.write(f'Migrated id={p.id} -> {public_url}')

        self.stdout.write(f'Done. Migrated {migrated} files.')