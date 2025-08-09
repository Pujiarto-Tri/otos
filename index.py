import os
from pathlib import Path

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.db import connections, DEFAULT_DB_ALIAS

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')

# Perform one-time migrations on cold start (serverless instance)
LOCK_FILE = Path('/tmp/.django_migrated')
try:
    if not LOCK_FILE.exists():
        print('[startup] initializing Django, running migrate & collectstatic')
        django.setup()

        # Acquire a DB advisory lock on Postgres to avoid concurrent migrations
        conn = connections[DEFAULT_DB_ALIAS]
        locked = False
        try:
            if conn.vendor == 'postgresql':
                with conn.cursor() as cur:
                    cur.execute('SELECT pg_advisory_lock(916031492)')
                    locked = True
                    print('[startup] acquired pg_advisory_lock')
        except Exception as e:
            print(f'[startup] could not acquire advisory lock: {e}')

        try:
            # Use --fake-initial to gracefully handle pre-existing tables
            call_command('migrate', interactive=False, fake_initial=True, verbosity=0)
        finally:
            # Release advisory lock if acquired
            try:
                if locked and conn.vendor == 'postgresql':
                    with conn.cursor() as cur:
                        cur.execute('SELECT pg_advisory_unlock(916031492)')
                        print('[startup] released pg_advisory_lock')
            except Exception:
                pass

        # Also collect static into a writable location when on Vercel
        try:
            call_command('collectstatic', interactive=False, verbosity=0)
        except Exception as e:
            print(f'[startup] collectstatic skipped/failed: {e}')

        # Seed roles and ensure a superuser exists (from env)
        try:
            from django.contrib.auth import get_user_model
            from otosapp.models import Role

            for role_name in ('Admin', 'Teacher', 'Student', 'Visitor'):
                Role.objects.get_or_create(role_name=role_name)

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
        except Exception as e:
            # Ignore seeding errors to not block startup
            print(f'[startup] seeding skipped/failed: {e}')

        try:
            LOCK_FILE.write_text('ok')
        except Exception:
            pass
except Exception as e:
    # Don't block app startup if migrations fail; errors will surface in logs
    print(f'[startup] migrate/collectstatic wrapper failed: {e}')

# Create WSGI application (calls django.setup() if not already called)
app = get_wsgi_application()

# Backwards-compat name used by some platforms
application = app
