#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import PaymentMethod

# Buat data contoh payment methods
payment_methods = [
    {
        'name': 'Bank BCA',
        'payment_type': 'bank',
        'account_number': '1234567890',
        'account_name': 'Otos Education',
        'is_active': True
    },
    {
        'name': 'Bank Mandiri',
        'payment_type': 'bank',
        'account_number': '0987654321',
        'account_name': 'Otos Education',
        'is_active': True
    },
    {
        'name': 'Bank BNI',
        'payment_type': 'bank',
        'account_number': '1122334455',
        'account_name': 'Otos Education',
        'is_active': True
    },
    {
        'name': 'OVO',
        'payment_type': 'ewallet',
        'account_number': '081234567890',
        'account_name': 'Otos Education',
        'is_active': True
    },
    {
        'name': 'GoPay',
        'payment_type': 'ewallet',
        'account_number': '081234567890',
        'account_name': 'Otos Education',
        'is_active': True
    },
    {
        'name': 'DANA',
        'payment_type': 'ewallet',
        'account_number': '081234567890',
        'account_name': 'Otos Education',
        'is_active': True
    }
]

print("Creating payment methods...")

for method_data in payment_methods:
    method, created = PaymentMethod.objects.get_or_create(
        name=method_data['name'],
        defaults=method_data
    )
    if created:
        print(f"✓ Created: {method.name}")
    else:
        print(f"• Already exists: {method.name}")

print("\nAll payment methods created successfully!")
print(f"Total payment methods: {PaymentMethod.objects.count()}")
