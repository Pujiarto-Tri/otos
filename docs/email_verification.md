# Email Verification & Password Reset Workflow

This guide explains the account activation flow introduced for new registrations and the related password reset policy.

## Overview

- **Registration** now creates accounts in an inactive state and sends a verification link to the submitted email address.
- **Email verification** is required before a user can log in or receive password reset links.
- **Password reset** emails are only sent to verified addresses to protect against account enumeration.

## Configuration

Configure the following environment variables (defaults shown in parentheses):

- `ACCOUNT_ACTIVATION_TOKEN_VALID_HOURS` (`24`): validity window for activation tokens.
- `ACCOUNT_ACTIVATION_RESEND_COOLDOWN_MINUTES` (`5`): throttle window between resend attempts.
- Standard email settings (`EMAIL_HOST`, `EMAIL_HOST_USER`, etc.) must be set so activation and reset emails can be delivered.

### Existing Users

For legacy accounts you already trust, populate `email_verified_at` (and optionally keep `is_active=True`) via a data migration or management command so they can continue logging in without re-verifying. Accounts left with `email_verified_at=NULL` will be asked to confirm their address before logging in.

## Data Model

- `User.email_verified_at` stores when the address was confirmed. Helper properties:
  - `is_email_verified`
  - `mark_email_verified()`
- `EmailVerificationToken` holds activation tokens with expiry and resend metadata.

Run migrations after deploying the changes:

```powershell
py -3 manage.py makemigrations
py -3 manage.py migrate
```

## User Flows

### Registration

1. User submits the registration form.
2. Account is created as inactive; verification token is generated.
3. Activation email is sent after the transaction commits.
4. User clicks the link to activate the account.

### Resend Activation

- Accessible at `/register/resend-activation/`.
- Respects the resend cooldown.
- Sends a fresh token and email immediately.

### Login

- Uses `VerifiedEmailAuthenticationForm` to block access until the user confirms their email.
- UI offers quick links to resend activation or reset the password.

### Password Reset

1. Only verified accounts can request a reset link (`VerifiedEmailPasswordResetForm`).
2. Reset emails use templated subject/body under `templates/emails/`.
3. Standard Django reset views handle confirm/complete steps.

## Testing

Automated coverage lives in `otosapp/tests/test_email_verification.py` and covers:

- Login rejection for unverified accounts.
- Password reset filtering for unverified users.
- Token activation success and failure cases.
- Resend throttling.
- Registration email dispatch.
- Password reset email generation for verified users.

Run the suite locally:

```powershell
py -3 manage.py test otosapp.tests.test_email_verification
```
