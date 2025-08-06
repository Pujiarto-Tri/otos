#!/usr/bin/env python
"""
Script untuk membuat role Visitor jika belum ada
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Role

def create_visitor_role():
    """Create Visitor role if it doesn't exist"""
    try:
        visitor_role, created = Role.objects.get_or_create(role_name='Visitor')
        if created:
            print("✅ Role 'Visitor' berhasil dibuat!")
        else:
            print("ℹ️ Role 'Visitor' sudah ada.")
        
        # Ensure other roles exist too
        student_role, created = Role.objects.get_or_create(role_name='Student')
        if created:
            print("✅ Role 'Student' berhasil dibuat!")
        
        admin_role, created = Role.objects.get_or_create(role_name='Admin')
        if created:
            print("✅ Role 'Admin' berhasil dibuat!")
        
        teacher_role, created = Role.objects.get_or_create(role_name='Teacher')
        if created:
            print("✅ Role 'Teacher' berhasil dibuat!")
            
        print("\n📋 Semua role yang tersedia:")
        for role in Role.objects.all():
            print(f"  - {role.role_name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    create_visitor_role()
