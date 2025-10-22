from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from unittest import skipIf

from django.db import connection
from django.db.utils import OperationalError
from django.test import Client, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from otosapp.models import (
    AccessLevel,
    Category,
    Choice,
    Question,
    Role,
    SubscriptionPackage,
    Test,
    User,
    UserSubscription,
)


@skipIf(
    connection.vendor == "sqlite",
    "SQLite locks on concurrent writes; run this test suite against Postgres/MySQL to exercise concurrency.",
)
class ConcurrentTryoutFlowTests(TransactionTestCase):
    """Exercise the take_test flow with parallel students to detect race issues."""

    password = "testpass123"

    def setUp(self):
        self.student_role, _ = Role.objects.get_or_create(role_name="Student")

        self.package = SubscriptionPackage.objects.create(
            name="Concurrency Package",
            description="Package used for concurrency testing.",
            features="Feature A\nFeature B",
            price=199000,
            duration_days=30,
            access_level=AccessLevel.SILVER,
        )

        self.category = Category.objects.create(
            category_name="Logika Dasar",
            time_limit=60,
            scoring_method="default",
            passing_score=60.0,
        )

        self.questions = []
        for index in range(3):
            question = Question.objects.create(
                question_text=f"Pertanyaan {index + 1}",
                pub_date=timezone.now(),
                category=self.category,
            )
            for choice_index in range(4):
                Choice.objects.create(
                    question=question,
                    choice_text=f"Opsi {choice_index + 1} untuk Q{index + 1}",
                    is_correct=choice_index == 0,
                )
            self.questions.append(question)

        self.primary_question = self.questions[0]
        self.correct_choice_id = (
            self.primary_question.choices.filter(is_correct=True).values_list("id", flat=True).first()
        )

        self.students = []
        for index in range(5):
            user = User.objects.create_user(
                email=f"student{index}@example.com",
                username=f"student{index}@example.com",
                password=self.password,
                role=self.student_role,
            )
            UserSubscription.objects.create(
                user=user,
                package=self.package,
                end_date=timezone.now() + timedelta(days=self.package.duration_days),
                is_active=True,
            )
            self.students.append(user)

    def _simulate_student_flow(self, student):
        client = Client()
        if not client.login(username=student.email, password=self.password):
            return {"student": student, "error": "login failed"}

        start_url = reverse("take_test", args=[self.category.id, 1])
        try:
            response = client.get(start_url)
        except OperationalError as exc:
            return {
                "student": student,
                "error": f"database error while starting test: {exc}",
            }
        if response.status_code != 200:
            return {"student": student, "error": f"initial GET returned {response.status_code}"}

        try:
            post_response = client.post(
                start_url,
                {"choice": str(self.correct_choice_id), "action": "submit"},
            )
        except OperationalError as exc:
            return {
                "student": student,
                "error": f"database error during submission: {exc}",
            }
        if post_response.status_code not in (200, 302):
            return {"student": student, "error": f"submit POST returned {post_response.status_code}"}

        latest_test = Test.objects.filter(student=student).order_by("-id").first()
        if latest_test is None:
            return {"student": student, "error": "test record missing"}

        latest_test.refresh_from_db()
        return {"student": student, "test": latest_test}

    def test_multiple_students_finish_same_category_concurrently(self):
        futures = []
        with ThreadPoolExecutor(max_workers=len(self.students)) as executor:
            for student in self.students:
                futures.append(executor.submit(self._simulate_student_flow, student))

        results = []
        for future in as_completed(futures):
            results.append(future.result())

        errors = [result for result in results if result.get("error")]
        self.assertFalse(errors, f"Concurrency errors detected: {errors}")

        for result in results:
            test = result["test"]
            self.assertTrue(test.is_submitted, f"Test {test.pk} for {result['student'].email} not submitted")
            self.assertEqual(test.answers.count(), 1, "Expected exactly one answer per test")
            self.assertEqual(
                test.answers.filter(question=self.primary_question).count(),
                1,
                "Answer missing for primary question",
            )
            answer = test.answers.first()
            self.assertTrue(answer.selected_choice.is_correct, "Recorded answer should be correct")

        submitted_tests = Test.objects.filter(categories=self.category, is_submitted=True)
        self.assertEqual(submitted_tests.count(), len(self.students), "Unexpected number of submitted tests")