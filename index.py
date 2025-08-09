import os
import django
from django.core.wsgi import get_wsgi_application

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Initialize Django
django.setup()

# Create WSGI application
application = get_wsgi_application()

# Vercel compatibility
app = application
handler = application
