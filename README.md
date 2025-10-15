# Brainest Platform Enhancements

This repository contains the Brainest Django project. Recent changes introduce email verification for new accounts and align the password reset flow with verified addresses.

## Email Verification & Password Reset

- New users must activate their account via email before logging in.
- Login and password reset forms enforce verification via custom form classes.
- See [`docs/email_verification.md`](docs/email_verification.md) for configuration, flow details, and test commands.

## Running Tests

```powershell
py -3 manage.py test otosapp.tests.test_email_verification
```

Ensure dependencies are installed and the virtual environment is activated before running tests or migrations.

## Gmail SMTP Configuration

To send activation and reset emails from `noreply.brainest@gmail.com`, configure these environment variables in your deployment target (Vercel dashboard, VPS process manager, or local PowerShell session):

```powershell
$env:EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST = "smtp.gmail.com"
$env:EMAIL_PORT = "587"
$env:EMAIL_USE_TLS = "True"
$env:EMAIL_HOST_USER = "noreply.brainest@gmail.com"
$env:EMAIL_HOST_PASSWORD = "<your Gmail app password>"
$env:DEFAULT_FROM_EMAIL = "noreply.brainest@gmail.com"
```

Replace `<your Gmail app password>` with the 16-character app password you generated for the Brainest Gmail account. Restart the application after setting the variables so Django picks up the new credentials.
