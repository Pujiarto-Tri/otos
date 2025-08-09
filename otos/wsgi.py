"""
WSGI config for otos project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Add the project directory to the sys.path
project_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

application = get_wsgi_application()

# Vercel expects an app callable for serverless functions
app = application
handler = application
