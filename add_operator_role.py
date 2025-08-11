#!/usr/bin/env python
"""
Script untuk menambahkan role Operator ke database
Jalankan dengan: python manage.py shell < add_operator_role.py
atau: python add_operator_role.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Role

def add_operator_role():
    """Menambahkan role Operator jika belum ada"""
    try:
        # Cek apakah role Operator sudah ada
        operator_role, created = Role.objects.get_or_create(
            role_name='Operator'
        )
        
        if created:
            print("✅ Role 'Operator' berhasil ditambahkan ke database")
        else:
            print("ℹ️  Role 'Operator' sudah ada di database")
            
        # Tampilkan semua role yang ada
        print("\n📋 Daftar semua role:")
        for role in Role.objects.all():
            print(f"  - {role.role_name}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_operator_role()
