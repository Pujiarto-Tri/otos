from datetime import timedelta
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse
from django.utils import timezone
from django.test import TransactionTestCase

from otosapp.forms import VerifiedEmailAuthenticationForm, VerifiedEmailPasswordResetForm
from otosapp.models import EmailVerificationToken, Role

User = get_user_model()


class EmailVerificationFlowTests(TransactionTestCase):
    def setUp(self):
        self.visitor_role = Role.objects.create(role_name='Visitor')
        self.password = 'StrongPass123!'
        mail.outbox = []
        self.user = User.objects.create_user(
            email='newuser@example.com',
            username='newuser@example.com',
            password=self.password,
            role=self.visitor_role,
            is_active=False,
        )
        self.token = EmailVerificationToken.objects.create(
            user=self.user,
            token='initial-token',
            purpose=EmailVerificationToken.PURPOSE_ACTIVATE,
            expires_at=timezone.now() + timedelta(hours=24),
        )

    def test_login_rejected_when_email_not_verified(self):
        form = VerifiedEmailAuthenticationForm(
            data={'username': self.user.email, 'password': self.password}
        )
        self.assertFalse(form.is_valid())
        non_field_errors = form.errors.as_data().get('__all__', [])
        self.assertTrue(any(error.code == 'email_not_verified' for error in non_field_errors))

    def test_password_reset_skips_unverified_users(self):
        form = VerifiedEmailPasswordResetForm(data={'email': self.user.email})
        self.assertTrue(form.is_valid())
        self.assertEqual(len(list(form.get_users(self.user.email))), 0)

    def test_activation_consumes_token_and_marks_user_verified(self):
        response = self.client.get(reverse('activate-account', args=[self.token.token]))
        self.assertRedirects(response, reverse('login'))

        self.user.refresh_from_db()
        self.token.refresh_from_db()

        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_active)
        self.assertIsNotNone(self.user.email_verified_at)
        self.assertIsNotNone(self.token.consumed_at)

    def test_activation_rejects_expired_token(self):
        self.token.expires_at = timezone.now() - timedelta(minutes=1)
        self.token.save(update_fields=['expires_at'])

        response = self.client.get(reverse('activate-account', args=[self.token.token]))
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'registration/activation_failed.html')

    def test_resend_activation_throttled(self):
        resend_url = reverse('resend-activation')
        post_data = {'email': self.user.email}

        response_first = self.client.post(resend_url, post_data, follow=True)
        self.assertEqual(response_first.status_code, 200)
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user).count() >= 1)

        response_second = self.client.post(resend_url, post_data)
        self.assertEqual(response_second.status_code, 429)

    def test_registration_flow_creates_inactive_user_and_sends_email(self):
        register_url = reverse('register')
        payload = {
            'email': 'fresh@example.com',
            'phone_number': '+628123456789',
            'password1': 'SuperSecret123',
            'password2': 'SuperSecret123',
        }

        response = self.client.post(register_url, payload, follow=True)
        self.assertRedirects(response, reverse('login'))

        newly_created = User.objects.get(email='fresh@example.com')
        self.assertFalse(newly_created.is_active)
        self.assertFalse(newly_created.is_email_verified)

        token = EmailVerificationToken.objects.filter(user=newly_created).latest('created_at')
        self.assertTrue(bool(token.token))
        self.assertGreater(token.expires_at, timezone.now())

        # Email sent via post-save hook captured in outbox
        self.assertGreaterEqual(len(mail.outbox), 1)
        activation_email = mail.outbox[-1]
        self.assertIn('Aktifkan Akun Brainest Anda', activation_email.subject)
        self.assertIn(token.token, activation_email.body)
        activation_link_match = re.search(r"https?://[\w\.-]+/register/activate/[\w\-_/]+", activation_email.body)
        self.assertIsNotNone(activation_link_match)

    def test_password_reset_email_contains_verified_link(self):
        self.user.mark_email_verified()
        reset_form = VerifiedEmailPasswordResetForm(data={'email': self.user.email})
        self.assertTrue(reset_form.is_valid())

        reset_form.save(domain_override='example.com', use_https=False, from_email='no-reply@example.com')

        self.assertEqual(len(mail.outbox), 1)
        reset_email = mail.outbox[0]
        self.assertIn('Reset Kata Sandi Brainest Anda', reset_email.subject)
        self.assertIn('/reset/', reset_email.body)
        self.assertIn('example.com', reset_email.body)
