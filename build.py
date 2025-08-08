#!/usr/bin/env python3
"""
Build script for Vercel deployment
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

# Run collectstatic
if __name__ == '__main__':
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("Static files collected successfully")
    except Exception as e:
        print(f"Error collecting static files: {e}")
        sys.exit(1)
