from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from otosapp.models import Role, User


class UserStatusManagementTests(TestCase):
    def setUp(self):
        self.admin_role = Role.objects.create(role_name='Admin')
        self.operator_role = Role.objects.create(role_name='Operator')
        self.student_role = Role.objects.create(role_name='Student')

        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            username='admin@example.com',
            password='StrongPass123!',
            role=self.admin_role,
        )

        self.operator_user = User.objects.create_user(
            email='operator@example.com',
            username='operator@example.com',
            password='StrongPass123!',
            role=self.operator_role,
        )

        self.student_user = User.objects.create_user(
            email='student@example.com',
            username='student@example.com',
            password='StrongPass123!',
            role=self.student_role,
            is_active=False,
        )

    def test_admin_can_activate_user_and_mark_verified(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_update_status', args=[self.student_user.id]),
            {'action': 'activate'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.student_user.refresh_from_db()

        self.assertTrue(self.student_user.is_active)
        self.assertIsNotNone(self.student_user.email_verified_at)
        self.assertTrue(self.student_user.is_email_verified)

    def test_admin_can_deactivate_user(self):
        self.student_user.is_active = True
        self.student_user.email_verified_at = timezone.now()
        self.student_user.save(update_fields=['is_active', 'email_verified_at'])

        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_update_status', args=[self.student_user.id]),
            {'action': 'deactivate'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertFalse(self.student_user.is_active)
        # Email verification timestamp remains unchanged when deactivated only
        self.assertIsNotNone(self.student_user.email_verified_at)

    def test_admin_can_mark_email_verified_without_activation_email(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_update_status', args=[self.student_user.id]),
            {'action': 'mark_verified'},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.student_user.refresh_from_db()
        self.assertTrue(self.student_user.is_email_verified)
        self.assertTrue(self.student_user.is_active)

    def test_invalid_action_returns_bad_request(self):
        self.client.force_login(self.admin_user)

        response = self.client.post(
            reverse('user_update_status', args=[self.student_user.id]),
            {'action': 'invalid_action'},
        )

        self.assertEqual(response.status_code, 400)

    def test_operator_cannot_modify_admin_status(self):
        self.client.force_login(self.operator_user)

        response = self.client.post(
            reverse('user_update_status', args=[self.admin_user.id]),
            {'action': 'deactivate'},
        )

        self.assertEqual(response.status_code, 403)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)
        self.assertFalse(self.admin_user.is_email_verified)
