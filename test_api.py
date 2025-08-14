#!/usr/bin/env python
import os
import sys
import django
import json

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.test import RequestFactory
from otosapp.views import api_universities

# Test API endpoint
factory = RequestFactory()
request = factory.get('/api/universities/?q=institut')

# Call the view function
response = api_universities(request)
data = json.loads(response.content.decode('utf-8'))

print("=== API Response Test ===")
print(f"Status Code: {response.status_code}")
print("Results:")
for uni in data['results'][:3]:  # Show first 3 results
    print(f"  Name: {uni.get('name', 'MISSING')}")
    print(f"  Tier: {uni.get('tier', 'MISSING')}")
    print(f"  Tier Display: {uni.get('tier_display', 'MISSING')}")
    print(f"  Min Score: {uni.get('minimum_utbk_score', 'MISSING')}")
    print(f"  Location: {uni.get('location', 'MISSING')}")
    print("  ---")
