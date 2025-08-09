import os
from pathlib import Path

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Perform one-time migrations on cold start (serverless instance)
LOCK_FILE = Path('/tmp/.django_migrated')
try:
    if not LOCK_FILE.exists():
        django.setup()
        # Run migrations quietly; run_syncdb ensures initial tables if no migrations
        call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)
        try:
            LOCK_FILE.write_text('ok')
        except Exception:
            pass
except Exception:
    # Don't block app startup if migrations fail; errors will surface in logs
    pass

# Create WSGI application (calls django.setup() if not already called)
app = get_wsgi_application()

# Backwards-compat name used by some platforms
application = app
