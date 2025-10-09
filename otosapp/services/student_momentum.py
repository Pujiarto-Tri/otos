from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json
from typing import Dict, Optional, Tuple

from django.db.models import Avg, Count, Max, QuerySet, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone

from ..models import StudentGoal, Test


@dataclass
class StreakStats:
    current: int
    longest: int
    last_activity: Optional[date]


@dataclass
class WeeklyActivity:
    current_week: int
    previous_week: int
    delta: int
    delta_abs: int


@dataclass
class GoalProgress:
    goal: StudentGoal
    current_value: float
    percent_complete: float
    remaining_to_target: float
    days_remaining: Optional[int]
    is_completed: bool


@dataclass
class PersonalBest:
    display_score: float
    unit: str
    label: str
    occurred_on: Optional[date]
    test_id: int


@dataclass
class GrowthSummary:
    recent_average: float
    previous_average: float
    delta: float
    delta_abs: float
    percent_change: Optional[float]
    unit: str
    direction: str
    recent_count: int
    previous_count: int


@dataclass
class TrendPayload:
    seven_day: str
    thirty_day: str
    ninety_day: str
    unit: str


@dataclass
class ReadinessSignal:
    title: str
    status: str
    message: str
    emphasis: Optional[str] = None


def _submitted_tests(user) -> QuerySet[Test]:
    return Test.objects.filter(student=user, is_submitted=True)


def _collect_unique_dates(tests_qs: QuerySet[Test]):
    return list(
        tests_qs.annotate(test_day=TruncDate("date_taken"))
        .values_list("test_day", flat=True)
        .distinct()
    )


def _calculate_streak(dates) -> Optional[StreakStats]:
    if not dates:
        return None

    today = timezone.localdate()
    unique_dates = sorted(set(dates))
    date_set = set(unique_dates)

    # current streak
    current_streak = 0
    cursor = today
    while cursor in date_set:
        current_streak += 1
        cursor -= timedelta(days=1)

    # longest streak
    longest = 0
    running = 0
    prev_day = None
    for day in unique_dates:
        if prev_day is None or (day - prev_day).days == 1:
            running = running + 1
        else:
            running = 1
        longest = max(longest, running)
        prev_day = day

    last_activity = unique_dates[-1]
    return StreakStats(current=current_streak, longest=longest, last_activity=last_activity)


def _calculate_weekly_activity(tests_qs: QuerySet[Test]) -> Optional[WeeklyActivity]:
    today = timezone.localdate()
    current_start = today - timedelta(days=6)
    previous_start = current_start - timedelta(days=7)
    previous_end = current_start - timedelta(days=1)

    current_week = tests_qs.filter(date_taken__date__gte=current_start).count()
    previous_week = tests_qs.filter(
        date_taken__date__gte=previous_start,
        date_taken__date__lte=previous_end,
    ).count()
    delta = current_week - previous_week

    if current_week == 0 and previous_week == 0:
        return None

    return WeeklyActivity(
        current_week=current_week,
        previous_week=previous_week,
        delta=delta,
        delta_abs=abs(delta),
    )


def _get_active_goal(user) -> Optional[StudentGoal]:
    return StudentGoal.objects.active().filter(user=user).order_by("timeframe_end", "-created_at").first()


def _score_scale(tests_qs: QuerySet[Test]) -> Tuple[str, float]:
    max_score = tests_qs.aggregate(mx=Max("score"))['mx'] or 0
    if max_score and max_score <= 1:
        return "%", 100.0
    return "pts", 1.0


def _format_label(test: Test) -> str:
    if test.tryout_package:
        return test.tryout_package.package_name
    categories = list(test.categories.values_list("category_name", flat=True))
    if not categories:
        return "Tryout Tanpa Kategori"
    if len(categories) == 1:
        return categories[0]
    return f"{categories[0]} +{len(categories) - 1}"


def _calculate_personal_best(tests_qs: QuerySet[Test]) -> Optional[PersonalBest]:
    if not tests_qs.exists():
        return None

    unit, scale = _score_scale(tests_qs)
    best_test = tests_qs.order_by("-score", "-date_taken").first()
    if not best_test:
        return None

    display_score = round((best_test.score or 0) * scale, 1)
    occurred_on = None
    if best_test.date_taken:
        occurred_on = timezone.localtime(best_test.date_taken).date()

    return PersonalBest(
        display_score=display_score,
        unit=unit,
        label=_format_label(best_test),
        occurred_on=occurred_on,
        test_id=best_test.id,
    )


def _calculate_growth(tests_qs: QuerySet[Test]) -> Optional[GrowthSummary]:
    tests = list(tests_qs.order_by("date_taken"))
    if len(tests) < 2:
        return None

    unit, scale = _score_scale(tests_qs)

    scores = [test.score or 0 for test in tests]
    recent_scores = scores[-3:]
    previous_scores = scores[:-3] or [scores[0]]

    def average(values):
        return sum(values) / len(values) if values else 0

    recent_avg_raw = average(recent_scores)
    previous_avg_raw = average(previous_scores)
    delta_raw = recent_avg_raw - previous_avg_raw

    percent_change = None
    if previous_avg_raw > 0:
        percent_change = round((delta_raw / previous_avg_raw) * 100, 1)

    direction = "flat"
    if delta_raw > 0:
        direction = "up"
    elif delta_raw < 0:
        direction = "down"

    delta_display = round(delta_raw * scale, 1)

    return GrowthSummary(
        recent_average=round(recent_avg_raw * scale, 1),
        previous_average=round(previous_avg_raw * scale, 1),
        delta=delta_display,
        delta_abs=abs(delta_display),
        percent_change=percent_change,
        unit=unit,
        direction=direction,
        recent_count=len(recent_scores),
        previous_count=len(previous_scores),
    )


def _calculate_goal_progress(goal: StudentGoal, tests_qs: QuerySet[Test]) -> GoalProgress:
    scoped_tests = tests_qs
    if goal.timeframe_start:
        scoped_tests = scoped_tests.filter(date_taken__date__gte=goal.timeframe_start)
    if goal.timeframe_end:
        scoped_tests = scoped_tests.filter(date_taken__date__lte=goal.timeframe_end)

    if goal.goal_type == StudentGoal.TEST_COUNT:
        current_value = float(scoped_tests.count())
    elif goal.goal_type == StudentGoal.AVERAGE_SCORE:
        current_value = scoped_tests.aggregate(avg=Avg("score"))['avg'] or 0.0
    elif goal.goal_type == StudentGoal.TOTAL_SCORE:
        current_value = scoped_tests.aggregate(total=Sum("score"))['total'] or 0.0
    else:
        current_value = 0.0

    target = goal.target_value if goal.target_value else 0
    percent = 0.0
    if target > 0:
        percent = max(0.0, min(100.0, (current_value / target) * 100))
    remaining = max(0.0, target - current_value)

    days_remaining: Optional[int] = None
    if goal.timeframe_end:
        days_remaining = (goal.timeframe_end - timezone.localdate()).days

    is_completed = target > 0 and current_value >= target

    return GoalProgress(
        goal=goal,
        current_value=float(round(current_value, 2)),
        percent_complete=round(percent, 2),
        remaining_to_target=float(round(remaining, 2)),
        days_remaining=days_remaining,
        is_completed=is_completed,
    )


def _build_trend_chart(tests_qs: QuerySet[Test], days: int, unit: str, scale: float) -> Dict[str, object]:
    if days <= 0:
        return {"categories": [], "series": []}

    end_date = timezone.localdate()
    start_date = end_date - timedelta(days=days - 1)

    # Aggregate average score per day
    aggregates = (
        tests_qs.filter(date_taken__date__gte=start_date)
        .annotate(day=TruncDate("date_taken"))
        .values("day")
        .annotate(avg_score=Avg("score"), count=Count("id"))
        .order_by("day")
    )

    score_map = {entry["day"]: (entry["avg_score"] or 0, entry["count"]) for entry in aggregates}

    categories = []
    data = []
    counts = []

    cursor = start_date
    while cursor <= end_date:
        categories.append(cursor.strftime("%d %b"))
        if cursor in score_map:
            avg, count = score_map[cursor]
            data.append(round((avg or 0) * scale, 2))
            counts.append(count)
        else:
            data.append(None)
            counts.append(0)
        cursor += timedelta(days=1)

    return {
        "categories": categories,
        "series": [
            {
                "name": "Skor Rata-rata",
                "data": data,
            }
        ],
        "sample_sizes": counts,
        "unit": unit,
    }


def _calculate_trend_payload(tests_qs: QuerySet[Test]) -> Optional[TrendPayload]:
    if not tests_qs.exists():
        return None

    unit, scale = _score_scale(tests_qs)
    payload_7 = _build_trend_chart(tests_qs, 7, unit, scale)
    payload_30 = _build_trend_chart(tests_qs, 30, unit, scale)
    payload_90 = _build_trend_chart(tests_qs, 90, unit, scale)

    return TrendPayload(
        seven_day=json.dumps(payload_7),
        thirty_day=json.dumps(payload_30),
        ninety_day=json.dumps(payload_90),
        unit=unit,
    )


def _format_status(level: str) -> str:
    mapping = {
        "strong": "strong",
        "steady": "steady",
        "focus": "focus",
    }
    return mapping.get(level, level)


def _calculate_readiness_signals(
    user,
    tests_qs: QuerySet[Test],
    streak: Optional[StreakStats],
    weekly: Optional[WeeklyActivity],
    goal: Optional[GoalProgress],
    growth: Optional[GrowthSummary],
) -> Optional[list[ReadinessSignal]]:
    if not user.is_student():
        return None

    signals: list[ReadinessSignal] = []

    # Practice frequency signal
    practice_count = weekly.current_week if weekly else 0
    if practice_count >= 3:
        status = "strong"
        message = f"Konsistensi latihan kamu sangat baik ({practice_count} sesi minggu ini)."
    elif practice_count >= 1:
        status = "steady"
        message = f"Pertahankan! Ada {practice_count} sesi minggu ini, jadwalkan 1-2 lagi untuk menjaga ritme."
    else:
        status = "focus"
        message = "Belum ada tryout minggu ini. Luangkan waktu untuk minimal satu sesi."
    signals.append(ReadinessSignal(title="Frekuensi Latihan", status=_format_status(status), message=message))

    # Streak / consistency signal
    current_streak = streak.current if streak else 0
    if current_streak >= 4:
        status = "strong"
        message = f"Streak {current_streak} hari! Ini modal bagus jelang ujian."
    elif current_streak >= 2:
        status = "steady"
        message = f"Kamu punya streak {current_streak} hari. Jaga agar tidak putus besok."
    else:
        status = "focus"
        message = "Mulai lagi streak latihan untuk membangun energi belajar."
    signals.append(ReadinessSignal(title="Konsistensi Harian", status=_format_status(status), message=message))

    # Goal progress
    if goal:
        percent = goal.percent_complete
        if percent >= 80:
            status = "strong"
            message = f"Target kamu hampir tuntas ({percent:.0f}% tercapai)."
        elif percent >= 40:
            status = "steady"
            message = f"Target berjalan ({percent:.0f}% tercapai). Tetapkan jadwal agar selesai tepat waktu."
        else:
            status = "focus"
            message = "Progress target masih rendah. Cek kembali angka target dan jadwalmu."
        signals.append(ReadinessSignal(title="Progress Target", status=_format_status(status), message=message))

    # Score momentum
    if growth:
        if growth.direction == "up":
            status = "strong"
            message = f"Nilai rata-rata naik {growth.delta_abs:.1f} {growth.unit} dari sesi sebelumnya."
        elif growth.direction == "flat":
            status = "steady"
            message = "Nilai stabil. Cari variasi latihan untuk memecah plateau."
        else:
            status = "focus"
            message = f"Nilai turun {growth.delta_abs:.1f} {growth.unit}. Evaluasi pembahasan tryout terakhir."
        signals.append(ReadinessSignal(title="Momentum Nilai", status=_format_status(status), message=message))

    # Coverage signal - variety of categories
    category_count = tests_qs.filter(date_taken__gte=timezone.now() - timedelta(days=60)).values("categories").distinct().count()
    if category_count >= 4:
        status = "strong"
        message = "Variasi materi luas. Terus latihan agar semua topik tercover."
    elif category_count >= 2:
        status = "steady"
        message = "Sudah mencoba beberapa kategori. Tambah variasi agar makin siap."
    else:
        status = "focus"
        message = "Latih lebih banyak kategori untuk menutup celah materi."
    signals.append(ReadinessSignal(title="Cakupan Materi", status=_format_status(status), message=message))

    return signals


def get_momentum_snapshot(user) -> Dict[str, Optional[object]]:
    tests_qs = _submitted_tests(user)
    dates = _collect_unique_dates(tests_qs)
    streak = _calculate_streak(dates)
    weekly = _calculate_weekly_activity(tests_qs)
    personal_best = _calculate_personal_best(tests_qs)
    growth = _calculate_growth(tests_qs)
    trend = _calculate_trend_payload(tests_qs)
    readiness = _calculate_readiness_signals(user, tests_qs, streak, weekly, goal=None, growth=growth)

    goal = None
    active_goal = _get_active_goal(user)
    if active_goal:
        goal = _calculate_goal_progress(active_goal, tests_qs)
        readiness = _calculate_readiness_signals(user, tests_qs, streak, weekly, goal, growth)

    return {
        "streak": streak,
        "weekly_activity": weekly,
        "goal": goal,
        "personal_best": personal_best,
        "growth": growth,
        "trend": trend,
        "readiness": readiness,
    }