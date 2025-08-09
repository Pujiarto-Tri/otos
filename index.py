import os
from pathlib import Path

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Perform one-time migrations on cold start (serverless instance)
LOCK_FILE = Path('/tmp/.django_migrated')
try:
    if not LOCK_FILE.exists():
        django.setup()
        # Run migrations quietly; run_syncdb ensures initial tables if no migrations
        call_command('migrate', interactive=False, run_syncdb=True, verbosity=0)

        # Seed roles and ensure a superuser exists (from env)
        try:
            from django.contrib.auth import get_user_model
            from otosapp.models import Role

            # Ensure basic roles exist
            for role_name in ('Admin', 'Teacher', 'Student', 'Visitor'):
                Role.objects.get_or_create(role_name=role_name)

            # Create/update superuser from env vars if provided
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')

            if admin_email and admin_password:
                User = get_user_model()
                user, created = User.objects.get_or_create(
                    email=admin_email,
                    defaults={
                        'username': admin_username,
                        'is_superuser': True,
                        'is_staff': True,
                    },
                )
                if created:
                    user.set_password(admin_password)
                    user.save()
                else:
                    updated = False
                    if not user.is_superuser or not user.is_staff:
                        user.is_superuser = True
                        user.is_staff = True
                        updated = True
                    # Reset password if provided to ensure access
                    user.set_password(admin_password)
                    updated = True
                    if updated:
                        user.save()
                role_admin, _ = Role.objects.get_or_create(role_name='Admin')
                if getattr(user, 'role_id', None) != role_admin.id:
                    user.role = role_admin
                    user.save()
        except Exception:
            # Ignore seeding errors to not block startup
            pass

        try:
            LOCK_FILE.write_text('ok')
        except Exception:
            pass
except Exception:
    # Don't block app startup if migrations fail; errors will surface in logs
    pass

# Create WSGI application (calls django.setup() if not already called)
app = get_wsgi_application()

# Backwards-compat name used by some platforms
application = app
