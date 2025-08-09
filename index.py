import os
from django.core.wsgi import get_wsgi_application

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Create WSGI application (this calls django.setup() internally)
app = get_wsgi_application()

# Backwards-compat name used by some platforms
application = app
