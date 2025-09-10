from django.core.management.base import BaseCommand
from django.conf import settings
from otosapp.models import PaymentProof
import requests
import os


class Command(BaseCommand):
    help = 'Debug PaymentProof entries: show proof_image.name and proof_image.url and test HTTP HEAD on URL to detect 404s'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10, help='Number of recent proofs to inspect')

    def handle(self, *args, **options):
        limit = options.get('limit')
        self.stdout.write(f'DEFAULT_FILE_STORAGE: {getattr(settings, "DEFAULT_FILE_STORAGE", "(not set)")}')
        self.stdout.write(f'MEDIA_URL: {getattr(settings, "MEDIA_URL", "(not set)")}')
        self.stdout.write(f'MEDIA_ROOT: {getattr(settings, "MEDIA_ROOT", "(not set)")}')

        qs = PaymentProof.objects.order_by('-created_at')[:limit]
        if not qs:
            self.stdout.write('No PaymentProof objects found')
            return

        for p in qs:
            try:
                name = p.proof_image.name
            except Exception:
                name = '(no name)'
            try:
                url = p.proof_image.url
            except Exception as e:
                url = f'(could not get url: {e})'

            self.stdout.write('\n---')
            self.stdout.write(f'PaymentProof id={p.id} status={p.status} created_at={p.created_at}')
            self.stdout.write(f'  name: {name}')
            self.stdout.write(f'  url: {url}')

            # If url looks like an HTTP URL, try a HEAD request to check reachability
            if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://')):
                try:
                    resp = requests.head(url, allow_redirects=True, timeout=10)
                    self.stdout.write(f'  HEAD status: {resp.status_code}')
                except Exception as e:
                    self.stdout.write(f'  HEAD request failed: {e}')
            else:
                # If not an HTTP URL, check local file existence
                path = os.path.join(getattr(settings, 'MEDIA_ROOT', ''), name) if name and not name.startswith('http') else name
                exists = os.path.exists(path) if path else False
                self.stdout.write(f'  local path: {path} exists={exists}')

        self.stdout.write('\nDone')