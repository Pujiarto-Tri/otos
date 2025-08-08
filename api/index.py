import os
import sys
import traceback

# Set Django settings module  
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

def app(environ, start_response):
    try:
        # Import Django
        from django.core.wsgi import get_wsgi_application
        
        # Get the application
        application = get_wsgi_application()
        
        # Call the application
        return application(environ, start_response)
        
    except Exception as e:
        # Return detailed error information
        error_msg = f"""
        Django Error: {str(e)}
        
        Traceback:
        {traceback.format_exc()}
        
        Python Path:
        {sys.path}
        
        Environment:
        {dict(os.environ)}
        """
        
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/plain')]
        start_response(status, headers)
        return [error_msg.encode('utf-8')]
