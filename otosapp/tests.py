import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .forms import StudentGoalForm
from .models import (
	BroadcastMessage,
	Category,
	Role,
	StudentGoal,
	SubscriptionPackage,
	Test,
	User,
	UserSubscription,
	MessageThread,
	Message,
)
from .services.student_momentum import get_momentum_snapshot


class StudentGoalFormTests(TestCase):
	def setUp(self):
		self.role = Role.objects.create(role_name='Student')
		self.user = User.objects.create_user(
			email='student@example.com',
			username='student@example.com',
			password='testpass123',
			role=self.role,
		)

	def test_student_goal_form_accepts_valid_payload(self):
		today = timezone.localdate()
		data = {
			'goal_type': StudentGoal.TEST_COUNT,
			'title': 'Selesaikan lima tryout',
			'target_value': 5,
			'timeframe_start': today,
			'timeframe_end': today + timedelta(days=7),
		}

		form = StudentGoalForm(data=data)

		self.assertTrue(form.is_valid())

		goal = form.save(commit=False)
		goal.user = self.user
		goal.save()

		self.assertEqual(goal.goal_type, StudentGoal.TEST_COUNT)
		self.assertEqual(goal.target_value, 5)

	def test_student_goal_form_rejects_non_positive_targets(self):
		today = timezone.localdate()
		data = {
			'goal_type': StudentGoal.TEST_COUNT,
			'target_value': 0,
			'timeframe_start': today,
			'timeframe_end': today + timedelta(days=7),
		}

		form = StudentGoalForm(data=data)

		self.assertFalse(form.is_valid())
		self.assertIn('target_value', form.errors)
		self.assertIn('Target harus lebih besar dari 0.', form.errors['target_value'])

	def test_student_goal_form_requires_start_date(self):
		today = timezone.localdate()
		data = {
			'goal_type': StudentGoal.TEST_COUNT,
			'target_value': 3,
			'timeframe_start': '',
			'timeframe_end': today + timedelta(days=7),
		}

		form = StudentGoalForm(data=data)

		self.assertFalse(form.is_valid())
		self.assertIn('timeframe_start', form.errors)
		self.assertIn('Tanggal mulai wajib diisi untuk menghitung progres target.', form.errors['timeframe_start'])

	def test_student_goal_form_validates_timeframe_order(self):
		today = timezone.localdate()
		data = {
			'goal_type': StudentGoal.AVERAGE_SCORE,
			'target_value': 75,
			'timeframe_start': today,
			'timeframe_end': today - timedelta(days=1),
		}

		form = StudentGoalForm(data=data)

		self.assertFalse(form.is_valid())
		self.assertIn('timeframe_end', form.errors)
		self.assertIn('Tanggal selesai harus setelah tanggal mulai.', form.errors['timeframe_end'])


class StudentGoalModelTests(TestCase):
	def setUp(self):
		self.role = Role.objects.create(role_name='Student')
		self.user = User.objects.create_user(
			email='stud@example.com',
			username='stud@example.com',
			password='testpass123',
			role=self.role,
		)

	def test_get_active_goal_returns_current_goal(self):
		goal = StudentGoal.objects.create(
			user=self.user,
			goal_type=StudentGoal.TEST_COUNT,
			target_value=3,
			timeframe_start=timezone.localdate(),
			timeframe_end=timezone.localdate() + timedelta(days=3),
		)

		self.assertEqual(self.user.get_active_goal(), goal)

	def test_archived_goal_excluded_from_active(self):
		goal = StudentGoal.objects.create(
			user=self.user,
			goal_type=StudentGoal.TEST_COUNT,
			target_value=2,
		)

		goal.archive()

		self.assertIsNone(self.user.get_active_goal())
		self.assertIsNotNone(goal.archived_at)


class StudentMomentumServiceTests(TestCase):
	def setUp(self):
		self.role = Role.objects.create(role_name='Student')
		self.user = User.objects.create_user(
			email='momentum@example.com',
			username='momentum@example.com',
			password='testpass123',
			role=self.role,
		)
		self.category = Category.objects.create(
			category_name='Matematika',
			time_limit=60,
			scoring_method='default',
			passing_score=75.0,
		)

	def _create_test(self, score, days_ago=0, user=None, category=None):
		user = user or self.user
		category = category or self.category
		test = Test.objects.create(
			student=user,
			score=score,
			is_submitted=True,
		)
		test.categories.add(category)
		Test.objects.filter(pk=test.pk).update(date_taken=timezone.now() - timedelta(days=days_ago))
		return Test.objects.get(pk=test.pk)

	def test_personal_best_returns_highest_score(self):
		self._create_test(60, days_ago=10)
		self._create_test(72, days_ago=5)
		best = self._create_test(85, days_ago=1)

		snapshot = get_momentum_snapshot(self.user)
		personal_best = snapshot['personal_best']

		self.assertIsNotNone(personal_best)
		self.assertEqual(personal_best.unit, 'pts')
		self.assertAlmostEqual(personal_best.display_score, 85.0)
		self.assertEqual(personal_best.label, 'Matematika')
		self.assertEqual(personal_best.test_id, best.id)
		self.assertIsNotNone(snapshot['readiness'])
		self.assertGreaterEqual(len(snapshot['readiness']), 4)

	def test_growth_summary_uses_recent_and_previous_scores(self):
		self._create_test(50, days_ago=20)
		self._create_test(60, days_ago=14)
		self._create_test(65, days_ago=7)
		self._create_test(80, days_ago=2)

		snapshot = get_momentum_snapshot(self.user)
		growth = snapshot['growth']

		self.assertIsNotNone(growth)
		self.assertEqual(growth.unit, 'pts')
		self.assertEqual(growth.recent_count, 3)
		self.assertEqual(growth.previous_count, 1)
		self.assertEqual(growth.direction, 'up')
		self.assertAlmostEqual(growth.recent_average, 68.3, places=1)
		self.assertAlmostEqual(growth.previous_average, 50.0)
		self.assertAlmostEqual(growth.delta, 18.3, places=1)
		self.assertAlmostEqual(growth.delta_abs, 18.3, places=1)
		self.assertAlmostEqual(growth.percent_change, 36.7, places=1)

	def test_growth_requires_minimum_two_tests(self):
		self._create_test(70, days_ago=3)

		snapshot = get_momentum_snapshot(self.user)
		self.assertIsNone(snapshot['growth'])

	def test_fractional_scores_display_percentage(self):
		second_user = User.objects.create_user(
			email='fraction@example.com',
			username='fraction@example.com',
			password='testpass123',
			role=self.role,
		)
		second_category = Category.objects.create(
			category_name='Listening',
			time_limit=60,
			scoring_method='default',
			passing_score=75.0,
		)
		self._create_test(0.72, days_ago=5, user=second_user, category=second_category)
		self._create_test(0.88, days_ago=1, user=second_user, category=second_category)

		snapshot = get_momentum_snapshot(second_user)
		personal_best = snapshot['personal_best']
		self.assertIsNotNone(personal_best)
		self.assertEqual(personal_best.unit, '%')
		self.assertAlmostEqual(personal_best.display_score, 88.0)

	def test_trend_payload_serializes_chart_data(self):
		self._create_test(60, days_ago=6)
		self._create_test(70, days_ago=4)
		self._create_test(65, days_ago=2)

		snapshot = get_momentum_snapshot(self.user)
		trend = snapshot['trend']
		self.assertIsNotNone(trend)

		payload = json.loads(trend.seven_day)
		self.assertIn('categories', payload)
		self.assertIn('series', payload)
		self.assertEqual(len(payload['categories']), 7)
		self.assertEqual(payload['unit'], trend.unit)

	def test_readiness_signals_reflect_low_activity(self):
		snapshot = get_momentum_snapshot(self.user)
		signals = snapshot['readiness']
		self.assertIsNotNone(signals)
		frequency = next((s for s in signals if s.title == 'Frekuensi Latihan'), None)
		self.assertIsNotNone(frequency)
		self.assertEqual(frequency.status, 'focus')


class BroadcastMessageVisibilityTests(TestCase):
	def setUp(self):
		self.student_role = Role.objects.create(role_name='Student')
		self.teacher_role = Role.objects.create(role_name='Teacher')
		self.operator_role = Role.objects.create(role_name='Operator')

		self.package = SubscriptionPackage.objects.create(
			name='Paket Premium',
			description='Akses penuh selama 30 hari',
			features='Tryout lengkap\nAnalisis realtime',
			price=199000,
			duration_days=30,
		)

		self.student_active = User.objects.create_user(
			email='active@student.com',
			username='active@student.com',
			password='testpass123',
			role=self.student_role,
		)
		UserSubscription.objects.create(
			user=self.student_active,
			package=self.package,
			end_date=timezone.now() + timedelta(days=7),
		)

		self.student_inactive = User.objects.create_user(
			email='inactive@student.com',
			username='inactive@student.com',
			password='testpass123',
			role=self.student_role,
		)

		self.teacher = User.objects.create_user(
			email='teacher@example.com',
			username='teacher@example.com',
			password='testpass123',
			role=self.teacher_role,
		)

	def _create_broadcast(self, **kwargs):
		defaults = {
			'title': 'Pengumuman Penting',
			'content': 'Mohon diperhatikan.',
			'publish_at': timezone.now() - timedelta(minutes=5),
			'duration_minutes': 120,
		}
		defaults.update(kwargs)
		broadcast = BroadcastMessage.objects.create(**defaults)
		return broadcast

	def test_student_with_active_subscription_sees_restricted_message(self):
		broadcast = self._create_broadcast(students_require_active_subscription=True)
		broadcast.target_roles.add(self.student_role)

		visible = BroadcastMessage.objects.visible_for_user(self.student_active)
		self.assertIn(broadcast, visible)

	def test_student_without_subscription_hidden_when_restricted(self):
		broadcast = self._create_broadcast(students_require_active_subscription=True)
		broadcast.target_roles.add(self.student_role)

		visible = BroadcastMessage.objects.visible_for_user(self.student_inactive)
		self.assertNotIn(broadcast, visible)

	def test_general_student_message_visible_to_all_students(self):
		broadcast = self._create_broadcast(students_require_active_subscription=False)
		broadcast.target_roles.add(self.student_role)

		self.assertIn(broadcast, BroadcastMessage.objects.visible_for_user(self.student_active))
		self.assertIn(broadcast, BroadcastMessage.objects.visible_for_user(self.student_inactive))

	def test_teacher_specific_broadcast(self):
		broadcast = self._create_broadcast()
		broadcast.target_roles.add(self.teacher_role)

		self.assertIn(broadcast, BroadcastMessage.objects.visible_for_user(self.teacher))
		self.assertNotIn(broadcast, BroadcastMessage.objects.visible_for_user(self.student_active))

	def test_removed_broadcast_no_longer_visible(self):
		broadcast = self._create_broadcast()
		broadcast.target_roles.add(self.student_role)
		visible = BroadcastMessage.objects.visible_for_user(self.student_active)
		self.assertIn(broadcast, visible)

		broadcast.remove_now(user=self.teacher)
		visible_after = BroadcastMessage.objects.visible_for_user(self.student_active)
		self.assertNotIn(broadcast, visible_after)

	def test_upcoming_broadcast_not_visible_until_publish_time(self):
		broadcast = self._create_broadcast(publish_at=timezone.now() + timedelta(hours=1))
		broadcast.target_roles.add(self.student_role)

		self.assertNotIn(broadcast, BroadcastMessage.objects.visible_for_user(self.student_active))

		broadcast.publish_at = timezone.now() - timedelta(minutes=1)
		broadcast.save()
		self.assertIn(broadcast, BroadcastMessage.objects.visible_for_user(self.student_active))


class AdminBroadcastThreadTests(TestCase):
	def setUp(self):
		self.admin_role = Role.objects.create(role_name='Admin')
		self.student_role = Role.objects.create(role_name='Student')
		self.admin = User.objects.create_user(
			email='admin@example.com',
			username='admin@example.com',
			password='testpass123',
			role=self.admin_role,
		)
		self.student_one = User.objects.create_user(
			email='student1@example.com',
			username='student1@example.com',
			password='testpass123',
			role=self.student_role,
		)
		self.student_two = User.objects.create_user(
			email='student2@example.com',
			username='student2@example.com',
			password='testpass123',
			role=self.student_role,
		)

	def test_admin_can_create_threads_for_multiple_students(self):
		self.client.login(username='admin@example.com', password='testpass123')
		url = reverse('admin_broadcast_message_thread')
		payload = {
			'title': 'Pengumuman Penting',
			'thread_type': 'general',
			'priority': 'high',
			'content': 'Mohon diperhatikan jadwal tryout terbaru.',
			'students': [str(self.student_one.pk), str(self.student_two.pk)],
		}

		response = self.client.post(url, payload, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(MessageThread.objects.filter(title='Pengumuman Penting').count(), 2)
		self.assertEqual(Message.objects.filter(content__icontains='jadwal tryout terbaru').count(), 2)

	def test_non_admin_cannot_access_broadcast_form(self):
		self.client.login(username='student1@example.com', password='testpass123')
		url = reverse('admin_broadcast_message_thread')
		response = self.client.get(url)
		self.assertRedirects(response, reverse('message_inbox'))
