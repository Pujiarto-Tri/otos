#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.forms import PaymentProofForm
from otosapp.models import SubscriptionPackage, PaymentMethod

def test_payment_form():
    print("=== Testing PaymentProofForm ===")
    
    # Get first package for testing
    package = SubscriptionPackage.objects.first()
    if not package:
        print("No packages found!")
        return
    
    print(f"Testing with package: {package.name}")
    
    # Initialize form
    form = PaymentProofForm(initial={'package': package, 'amount_paid': package.price})
    
    print(f"Form initialized successfully")
    print(f"Payment method field type: {type(form.fields['payment_method'])}")
    print(f"Payment method widget type: {type(form.fields['payment_method'].widget)}")
    print(f"Number of choices: {len(form.fields['payment_method'].choices)}")
    
    print("\nPayment method choices:")
    for i, choice in enumerate(form.fields['payment_method'].choices):
        print(f"  {i}: {choice}")
    
    # Test PaymentMethod model
    print(f"\n=== PaymentMethod Model ===")
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    print(f"Total active payment methods: {payment_methods.count()}")
    
    for method in payment_methods:
        print(f"  - {method.name} ({method.payment_type})")
        print(f"    Account: {method.account_number}")
        print(f"    Display text: {method.get_display_text()}")

if __name__ == "__main__":
    test_payment_form()
