#!/usr/bin/env python
import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import User

print("=== CHECKING USERS ===")

all_users = User.objects.all()
print(f"Total users: {all_users.count()}")

for user in all_users:
    role = getattr(user, 'role', None)
    role_name = role.role_name if role else "No Role"
    print(f"User: {user.username} - Email: {user.email} - Role: {role_name}")

# Check for any superusers
superusers = User.objects.filter(is_superuser=True)
print(f"\nSuperusers: {superusers.count()}")
for user in superusers:
    print(f"  Superuser: {user.username}")
