import os
import sys
import django
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Initialize Django
django.setup()

# Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# For Vercel compatibility - expose both handler and app
handler = application
app = application
