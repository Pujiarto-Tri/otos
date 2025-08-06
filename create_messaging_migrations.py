#!/usr/bin/env python
"""
Script untuk membuat migration file untuk messaging system
"""
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("🔧 Membuat migrations untuk messaging system...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations', 'otosapp'])
        print("✅ Migrations berhasil dibuat!")
        
        print("\n🔧 Menjalankan migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations berhasil dijalankan!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
