#!/usr/bin/env python
import os
import sys

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(root_dir)
sys.path.insert(0, parent_dir)

# Set environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Simple handler function for debugging
def handler(request):
    try:
        # Import Django components
        import django
        from django.core.wsgi import get_wsgi_application
        from django.http import HttpResponse
        
        # Setup Django
        if not django.conf.settings.configured:
            django.setup()
        
        # Get WSGI app
        app = get_wsgi_application()
        return app
        
    except Exception as e:
        # Return error for debugging
        from django.http import HttpResponse
        return HttpResponse(f"Error: {str(e)}", status=500)

# For Vercel
app = handler
