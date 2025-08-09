#!/usr/bin/env python
import os
import sys
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_dir = current_dir.parent
sys.path.insert(0, str(project_dir))

# Set environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Import and setup Django
import django
django.setup()

# Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# For Vercel compatibility
app = application
handler = application
