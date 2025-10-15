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
