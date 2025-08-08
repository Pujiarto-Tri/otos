import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the sys.path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

application = get_wsgi_application()

# For Vercel
app = application
