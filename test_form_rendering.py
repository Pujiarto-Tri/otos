#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.forms import UniversityTargetForm
from otosapp.models import UniversityTarget

# Test form rendering
print("Testing UniversityTargetForm rendering...")

# Test empty form
form = UniversityTargetForm()
print("\n1. Empty form primary_university field:")
print(form['primary_university'])

# Test if the select element has proper structure
primary_field_html = str(form['primary_university'])
print(f"\nHTML structure: {primary_field_html}")

# Check if it has select tag and options
if '<select' in primary_field_html and 'id="id_primary_university"' in primary_field_html:
    print("✅ Select element with correct ID found")
else:
    print("❌ Select element structure is incorrect")

# Check queryset
print(f"\nPrimary university queryset: {form.fields['primary_university'].queryset}")
print(f"Primary university queryset count: {form.fields['primary_university'].queryset.count()}")

print("\nForm rendering test completed!")
