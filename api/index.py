import os
import sys
from pathlib import Path

# Add the parent directory to Python path to access the Django project
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))

# Set Django settings module  
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Initialize Django
import django
django.setup()

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application

# Create the Django WSGI application
application = get_wsgi_application()

# For Vercel compatibility
app = application
