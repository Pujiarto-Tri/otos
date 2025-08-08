import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Initialize Django
django.setup()

# Get WSGI application
application = get_wsgi_application()

# For Vercel
app = application
