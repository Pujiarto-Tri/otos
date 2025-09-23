from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404, HttpResponseNotFound
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.forms import inlineformset_factory
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from otosapp.models import Choice, User, Role, Category, Question, Test, Answer, MessageThread, Message, SubscriptionPackage, PaymentMethod, PaymentProof, UserSubscription, University, UniversityTarget, TryoutPackage, TryoutPackageCategory
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Avg, Max, Q, Sum, Case, When, IntegerField
from datetime import timedelta, datetime
from .forms import CustomUserCreationForm, UserUpdateForm, CategoryUpdateForm, CategoryCreationForm, QuestionForm, ChoiceFormSet, QuestionUpdateForm, SubscriptionPackageForm, PaymentMethodForm, PaymentProofForm, PaymentVerificationForm, UserRoleChangeForm, UserSubscriptionEditForm, UniversityForm, UniversityTargetForm, TryoutPackageForm, TryoutPackageCategoryFormSet
from .decorators import admin_required, admin_or_operator_required, admin_or_teacher_required, admin_or_teacher_or_operator_required, operator_required, students_required, visitor_required, visitor_or_student_required, active_subscription_required

from django.db.models.functions import TruncDay, TruncMonth
from django.core.exceptions import PermissionDenied
import json


def check_and_downgrade_expired_subscriptions():
    """Check and automatically downgrade expired subscriptions"""
    expired_subscriptions = UserSubscription.objects.filter(
        is_active=True,
        end_date__lt=timezone.now(),
        auto_downgrade_processed=False
    )
    
    visitor_role, created = Role.objects.get_or_create(role_name='Visitor')
    
    for subscription in expired_subscriptions:
        # Change user role back to Visitor
        subscription.user.role = visitor_role
        subscription.user.save()
        
        # Mark subscription as processed
        subscription.is_active = False
        subscription.auto_downgrade_processed = True
        subscription.save()
        
        # You could also send notification here
        print(f"Downgraded user {subscription.user.email} to Visitor due to expired subscription")


def home(request):
    context = {}
    
    if request.user.is_authenticated:
        # Auto downgrade expired subscriptions
        check_and_downgrade_expired_subscriptions()
        
        if request.user.is_visitor():
            # Visitor dashboard - show subscription packages
            packages = SubscriptionPackage.objects.filter(is_active=True).order_by('price')
            
            # Check if user has pending payment
            pending_payment = PaymentProof.objects.filter(
                user=request.user, 
                status='pending'
            ).first()
            
            context.update({
                'is_visitor': True,
                'packages': packages,
                'pending_payment': pending_payment,
                'subscription_status': request.user.get_subscription_status()
            })
            
        elif request.user.is_student():
            # Student dashboard - show only tryout (UTBK) results in stat cards

            # Only use tryout/UTBK tests for dashboard stats and recent tests (sama persis dengan test_history)
            user_tests = Test.objects.filter(
                student=request.user,
                is_submitted=True
            ).select_related().prefetch_related('categories').order_by('-date_taken')
            # If no tryout/UTBK tests, show empty stats/cards
            if not user_tests.exists():
                user_tests = Test.objects.none()

            # Check for ongoing test (not submitted and not timed out)
            ongoing_test = Test.objects.filter(
                student=request.user,
                is_submitted=False
            ).first()

            # If ongoing test exists, check if it's still valid (not timed out)
            if ongoing_test:
                if ongoing_test.is_time_up():
                    # Auto-submit expired test
                    ongoing_test.is_submitted = True
                    ongoing_test.end_time = timezone.now()
                    ongoing_test.calculate_score()
                    ongoing_test.save()
                    ongoing_test = None  # Clear ongoing test
                elif not ongoing_test.start_time:
                    # If no start_time, this test is invalid, remove it
                    ongoing_test = None

            # Statistik untuk student (hanya dari tryout/UTBK)
            total_tests = user_tests.count()
            completed_tests = user_tests.filter(score__gt=0).count()

            # Rata-rata skor - deteksi format berdasarkan nilai maksimum
            avg_score_raw = user_tests.aggregate(avg_score=Avg('score'))['avg_score'] or 0
            max_score_in_data = user_tests.aggregate(max_score=Max('score'))['max_score'] or 0

            # Jika skor maksimum <= 1, maka format adalah 0-1, konversi ke persen
            # Jika skor maksimum > 1, maka sudah dalam format persen
            if max_score_in_data <= 1:
                avg_score = avg_score_raw * 100
                highest_score = max_score_in_data * 100
            else:
                avg_score = avg_score_raw
                highest_score = max_score_in_data

            # Test terbaru (maksimal 5)
            recent_tests = user_tests[:5]

            # Kategori yang paling sering dikerjakan - berdasarkan test tryout yang sudah submitted
            popular_categories = []
            if user_tests.exists():
                categories_data = {}
                for test in user_tests:
                    for category in test.categories.all():
                        category_name = category.category_name
                        if category_name in categories_data:
                            categories_data[category_name] += 1
                        else:
                            categories_data[category_name] = 1
                popular_categories = [
                    {'category_name': name, 'count': count}
                    for name, count in sorted(categories_data.items(), key=lambda x: x[1], reverse=True)[:3]
                ]

            # Check if student has pending payment
            pending_payment = PaymentProof.objects.filter(
                user=request.user,
                status='pending'
            ).first()
            # Include student's saved university target (if any) so templates/components can check it
            try:
                student_university_target = request.user.university_target
            except UniversityTarget.DoesNotExist:
                student_university_target = None

            context.update({
                'is_student': True,
                'user_tests': recent_tests,
                'total_tests': total_tests,
                'completed_tests': completed_tests,
                'avg_score': round(avg_score, 1),
                'highest_score': round(highest_score, 1),
                'popular_categories': popular_categories,
                'ongoing_test': ongoing_test,
                'pending_payment': pending_payment,
                'subscription_status': request.user.get_subscription_status(),
                'can_access_tryouts': request.user.can_access_tryouts()
                ,
                'student_university_target': student_university_target
            })
        
        # Data untuk teacher dashboard (statistik siswa & tren skor)
        elif request.user.is_teacher():
            # Categories the teacher is responsible for
            teacher_categories = Category.objects.filter(Q(created_by=request.user) | Q(teachers=request.user)).distinct()

            # Tests related to these categories (submitted)
            tests_qs = Test.objects.filter(is_submitted=True, categories__in=teacher_categories).select_related('student').distinct()

            # Number of distinct students who have submitted tests in teacher categories
            tested_count = tests_qs.values('student').distinct().count()

            # Determine passed/failed based on each student's latest submitted test for these categories
            passed_count = 0
            # Iterate students (could be optimized if needed)
            student_ids = tests_qs.values_list('student', flat=True).distinct()
            for sid in student_ids:
                latest = Test.objects.filter(student_id=sid, is_submitted=True, categories__in=teacher_categories).order_by('-date_taken').first()
                if latest and latest.is_passed():
                    passed_count += 1

            failed_count = max(0, tested_count - passed_count)
            pass_rate = round((passed_count / tested_count) * 100, 1) if tested_count else 0

            # Build teacher_stats for charts: aggregate per-category scores into series
            now = timezone.now()

            def build_per_category_chart(days, by_month=False):
                # Returns {'categories': [labels], 'series': [{'name': cat_name, 'data': [vals]}]}
                categories_labels = []
                series = []

                if not by_month:
                    # daily labels oldest->newest
                    days_list = [(now.date() - timedelta(days=i)) for i in range(days-1, -1, -1)]
                    categories_labels = [d.strftime('%d %b') for d in days_list]

                    for cat in teacher_categories:
                        data = []
                        for d in days_list:
                            day_start = timezone.make_aware(datetime.combine(d, datetime.min.time())) if timezone.is_naive(datetime.now()) else datetime.combine(d, datetime.min.time()).replace(tzinfo=now.tzinfo)
                            day_end = day_start + timedelta(days=1)
                            tests = Test.objects.filter(is_submitted=True, date_taken__gte=day_start, date_taken__lt=day_end).distinct()
                            tests = tests.filter(categories=cat)
                            total = 0.0
                            count = 0
                            for test in tests:
                                # compute this test's contribution for this category
                                if test.tryout_package:
                                    pkg_cat = test.tryout_package.tryoutpackagecategory_set.filter(category=cat).first()
                                    if pkg_cat:
                                        category_answers = test.answers.filter(question__category=cat)
                                        if category_answers.exists():
                                            correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
                                            total_questions = category_answers.count()
                                            category_score_percentage = (correct_answers / total_questions) if total_questions else 0
                                            contrib = category_score_percentage * pkg_cat.max_score
                                            total += contrib
                                            count += 1
                                else:
                                    # Non-package test: use test.score (already per-category)
                                    total += test.score
                                    count += 1
                            avg = (total / count) if count else 0
                            data.append(round(avg, 1))
                        series.append({'name': cat.category_name, 'data': data})

                    return {'categories': categories_labels, 'series': series}
                else:
                    # monthly aggregation (group by month)
                    months = []
                    # approximate months by 30-day steps
                    for i in range(max(1, int(days/30))-1, -1, -1):
                        dt = (now - timedelta(days=i*30)).date().replace(day=1)
                        months.append(dt)
                    categories_labels = [m.strftime('%b %Y') for m in months]

                    for cat in teacher_categories:
                        data = []
                        for m in months:
                            month_start = timezone.make_aware(datetime.combine(m, datetime.min.time())) if timezone.is_naive(datetime.now()) else datetime.combine(m, datetime.min.time()).replace(tzinfo=now.tzinfo)
                            month_end = month_start + timedelta(days=30)
                            tests = Test.objects.filter(is_submitted=True, date_taken__gte=month_start, date_taken__lt=month_end).distinct()
                            tests = tests.filter(categories=cat)
                            total = 0.0
                            count = 0
                            for test in tests:
                                if test.tryout_package:
                                    pkg_cat = test.tryout_package.tryoutpackagecategory_set.filter(category=cat).first()
                                    if pkg_cat:
                                        category_answers = test.answers.filter(question__category=cat)
                                        if category_answers.exists():
                                            correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
                                            total_questions = category_answers.count()
                                            category_score_percentage = (correct_answers / total_questions) if total_questions else 0
                                            contrib = category_score_percentage * pkg_cat.max_score
                                            total += contrib
                                            count += 1
                                else:
                                    total += test.score
                                    count += 1
                            avg = (total / count) if count else 0
                            data.append(round(avg, 1))
                        series.append({'name': cat.category_name, 'data': data})

                    return {'categories': categories_labels, 'series': series}

            scores_7d_chart = build_per_category_chart(7)
            scores_30d_chart = build_per_category_chart(30)
            scores_90d_chart = build_per_category_chart(90, by_month=True)
            scores_180d_chart = build_per_category_chart(180, by_month=True)

            # daily_summary: sum of per-category averages for each day (last 7 days)
            daily_summary = []
            chart7 = scores_7d_chart
            if chart7 and chart7.get('categories') and chart7.get('series'):
                # for each day index, sum series[i]
                for idx, label in enumerate(chart7['categories']):
                    total_score = 0
                    for s in chart7['series']:
                        vals = s.get('data', [])
                        total_score += vals[idx] if idx < len(vals) else 0
                    daily_summary.append({'date': label, 'total_score': round(total_score, 1)})

            # Ensure at least two points for growth calculation
            if len(daily_summary) >= 2:
                last_total = daily_summary[-1]['total_score']
                prev_total = daily_summary[-2]['total_score']
                growth_percent = round(((last_total - prev_total) / prev_total * 100), 1) if prev_total else 0
            else:
                growth_percent = 0

            teacher_stats = {
                'scores_7d_chart': scores_7d_chart,
                'scores_30d_chart': scores_30d_chart,
                'scores_90d_chart': scores_90d_chart,
                'scores_180d_chart': scores_180d_chart,
                'daily_summary': daily_summary,
                'growth_percent': growth_percent,
            }

            context.update({
                'tested_count': tested_count,
                'passed_count': passed_count,
                'failed_count': failed_count,
                'pass_rate': pass_rate,
                'teacher_stats': teacher_stats,
            })

        # Data untuk admin dashboard dengan statistik lengkap
        if request.user.is_superuser or request.user.is_admin():
            # from django.utils import timezone  # Sudah di-import di atas
            # from django.db.models import Count, Sum, Q  # Sudah di-import di atas
            # from datetime import datetime, timedelta  # Sudah di-import di atas
            
            # Basic user stats
            total_users = User.objects.count()
            new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
            new_users_this_month = User.objects.filter(date_joined__month=timezone.now().month, 
                                                     date_joined__year=timezone.now().year).count()
            
            # Payment statistics
            total_payments = PaymentProof.objects.count()
            pending_payments = PaymentProof.objects.filter(status='pending').count()
            approved_payments = PaymentProof.objects.filter(status='approved').count()
            rejected_payments = PaymentProof.objects.filter(status='rejected').count()
            
            # Revenue calculation (from approved payments)
            total_revenue = PaymentProof.objects.filter(status='approved').aggregate(
                total=Sum('amount_paid')
            )['total'] or 0
            
            # Monthly revenue (current month)
            current_month_revenue = PaymentProof.objects.filter(
                status='approved',
                verified_at__month=timezone.now().month,
                verified_at__year=timezone.now().year
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            # Subscription statistics
            total_subscriptions = UserSubscription.objects.count()
            active_subscriptions = UserSubscription.objects.filter(is_active=True, end_date__gt=timezone.now()).count()
            expired_subscriptions = UserSubscription.objects.filter(
                Q(is_active=False) | Q(end_date__lt=timezone.now())
            ).count()
            
            # Package popularity
            popular_packages = SubscriptionPackage.objects.annotate(
                subscription_count=Count('usersubscription')
            ).order_by('-subscription_count')[:5]
            
            # Recent activities
            recent_payments = PaymentProof.objects.order_by('-created_at')[:5]
            recent_subscriptions = UserSubscription.objects.order_by('-created_at')[:5]
            
            # Monthly trends (last 6 months, 3 months, 30 days, 7 days)
            from collections import OrderedDict
            monthly_data = []
            for i in range(6):
                month_date = timezone.now() - timedelta(days=30*i)
                month_revenue = PaymentProof.objects.filter(
                    status='approved',
                    verified_at__month=month_date.month,
                    verified_at__year=month_date.year
                ).aggregate(total=Sum('amount_paid'))['total'] or 0
                month_sales = PaymentProof.objects.filter(
                    status='approved',
                    verified_at__month=month_date.month,
                    verified_at__year=month_date.year
                ).count()
                month_subscriptions = UserSubscription.objects.filter(
                    created_at__month=month_date.month,
                    created_at__year=month_date.year
                ).count()
                monthly_data.append({
                    'month': month_date.strftime('%B %Y'),
                    'month_short': month_date.strftime('%b'),
                    'revenue': float(month_revenue),
                    'subscriptions': month_subscriptions,
                    'sales_count': month_sales
                })
            monthly_data.reverse()  # Oldest to newest

            # Growth percent (last vs previous month)
            growth_percent = 0
            if len(monthly_data) >= 2:
                last = monthly_data[-1]['sales_count']
                prev = monthly_data[-2]['sales_count']
                if prev:
                    growth_percent = round((last - prev) / prev * 100, 1)
                else:
                    growth_percent = 0

            # Filtered data for 7, 30, 90, 180 days
            now = timezone.now()
            def filter_by_days(days):
                start = now - timedelta(days=days)
                sales = PaymentProof.objects.filter(status='approved', verified_at__gte=start)
                return sales.count()
            sales_7d = filter_by_days(7)
            sales_30d = filter_by_days(30)
            sales_90d = filter_by_days(90)
            sales_180d = filter_by_days(180)

            # Data harian/bulanan untuk chart filter
            
            # 7 days chart data
            sales_7d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=7))
            sales_7d_chart = sales_7d_qs.annotate(day=TruncDay('verified_at')).values('day').annotate(count=Count('id')).order_by('day')
            sales_7d_chart_data = [{'label': d['day'].strftime('%d %b'), 'value': d['count']} for d in sales_7d_chart]
            
            # Fallback untuk 7 hari jika kosong
            if not sales_7d_chart_data:
                today = timezone.now().date()
                sales_7d_chart_data = [
                    {'label': (today - timedelta(days=i)).strftime('%d %b'), 'value': 0} 
                    for i in range(6, -1, -1)
                ]

            # 30 days chart data
            sales_30d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=30))
            sales_30d_chart = sales_30d_qs.annotate(day=TruncDay('verified_at')).values('day').annotate(count=Count('id')).order_by('day')
            sales_30d_chart_data = [{'label': d['day'].strftime('%d %b'), 'value': d['count']} for d in sales_30d_chart]
            
            # Fallback untuk 30 hari jika kosong
            if not sales_30d_chart_data:
                today = timezone.now().date()
                sales_30d_chart_data = [
                    {'label': (today - timedelta(days=i)).strftime('%d %b'), 'value': 0} 
                    for i in range(29, -1, -7)  # Sample setiap 7 hari
                ]

            # 90 days chart data
            sales_90d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=90))
            sales_90d_chart = sales_90d_qs.annotate(month=TruncMonth('verified_at')).values('month').annotate(count=Count('id')).order_by('month')
            sales_90d_chart_data = [{'label': d['month'].strftime('%b %Y'), 'value': d['count']} for d in sales_90d_chart]
            
            # Fallback untuk 90 hari jika kosong
            if not sales_90d_chart_data:
                today = timezone.now().date()
                sales_90d_chart_data = [
                    {'label': (today.replace(day=1) - timedelta(days=i*30)).strftime('%b %Y'), 'value': 0} 
                    for i in range(2, -1, -1)  # 3 bulan terakhir
                ]

            # 180 days chart data
            sales_180d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=180))
            sales_180d_chart = sales_180d_qs.annotate(month=TruncMonth('verified_at')).values('month').annotate(count=Count('id')).order_by('month')
            sales_180d_chart_data = [{'label': d['month'].strftime('%b %Y'), 'value': d['count']} for d in sales_180d_chart]
            
            # Fallback untuk 180 hari jika kosong
            if not sales_180d_chart_data:
                today = timezone.now().date()
                sales_180d_chart_data = [
                    {'label': (today.replace(day=1) - timedelta(days=i*30)).strftime('%b %Y'), 'value': 0} 
                    for i in range(5, -1, -1)  # 6 bulan terakhir
                ]

            context.update({
                'admin_stats': {
                    'total_users': total_users,
                    'new_users_today': new_users_today,
                    'new_users_this_month': new_users_this_month,
                    'total_payments': total_payments,
                    'pending_payments': pending_payments,
                    'approved_payments': approved_payments,
                    'rejected_payments': rejected_payments,
                    'total_revenue': float(total_revenue),
                    'current_month_revenue': float(current_month_revenue),
                    'total_subscriptions': total_subscriptions,
                    'active_subscriptions': active_subscriptions,
                    'expired_subscriptions': expired_subscriptions,
                    'popular_packages': popular_packages,
                    'recent_payments': recent_payments,
                    'recent_subscriptions': recent_subscriptions,
                    'monthly_data': monthly_data,
                    'growth_percent': growth_percent,
                    'sales_7d': sales_7d,
                    'sales_30d': sales_30d,
                    'sales_90d': sales_90d,
                    'sales_180d': sales_180d,
                    'sales_7d_chart': sales_7d_chart_data,
                    'sales_30d_chart': sales_30d_chart_data,
                    'sales_90d_chart': sales_90d_chart_data,
                    'sales_180d_chart': sales_180d_chart_data,
                },
                'pending_payments_count': pending_payments  # For sidebar notification
            })
        
        # Data untuk operator dashboard (tanpa data finansial sensitif)
        elif request.user.is_operator():
            # Basic user stats
            total_users = User.objects.count()
            new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
            new_users_this_month = User.objects.filter(date_joined__month=timezone.now().month, 
                                                     date_joined__year=timezone.now().year).count()
            
            # Payment statistics (counts only, no revenue)
            total_payments = PaymentProof.objects.count()
            pending_payments = PaymentProof.objects.filter(status='pending').count()
            approved_payments = PaymentProof.objects.filter(status='approved').count()
            rejected_payments = PaymentProof.objects.filter(status='rejected').count()
            
            # Subscription statistics
            total_subscriptions = UserSubscription.objects.count()
            active_subscriptions = UserSubscription.objects.filter(is_active=True, end_date__gt=timezone.now()).count()
            expired_subscriptions = UserSubscription.objects.filter(
                Q(is_active=False) | Q(end_date__lt=timezone.now())
            ).count()
            
            # Recent activities (tanpa amounts)
            recent_payments = PaymentProof.objects.order_by('-created_at')[:5]
            recent_subscriptions = UserSubscription.objects.order_by('-created_at')[:5]
            
            # Monthly trends (subscriber counts only, no revenue)
            monthly_data = []
            for i in range(6):
                month_date = timezone.now() - timedelta(days=30*i)
                month_sales = PaymentProof.objects.filter(
                    status='approved',
                    verified_at__month=month_date.month,
                    verified_at__year=month_date.year
                ).count()
                month_subscriptions = UserSubscription.objects.filter(
                    created_at__month=month_date.month,
                    created_at__year=month_date.year
                ).count()
                monthly_data.append({
                    'month': month_date.strftime('%B %Y'),
                    'month_short': month_date.strftime('%b'),
                    'subscriptions': month_subscriptions,
                    'sales_count': month_sales
                })
            monthly_data.reverse()  # Oldest to newest

            # Growth percent (last vs previous month)
            growth_percent = 0
            if len(monthly_data) >= 2:
                last = monthly_data[-1]['sales_count']
                prev = monthly_data[-2]['sales_count']
                if prev:
                    growth_percent = round((last - prev) / prev * 100, 1)
                else:
                    growth_percent = 0

            # Filtered data for 7, 30, 90, 180 days (counts only)
            now = timezone.now()
            def filter_by_days(days):
                start = now - timedelta(days=days)
                sales = PaymentProof.objects.filter(status='approved', verified_at__gte=start)
                return sales.count()
            sales_7d = filter_by_days(7)
            sales_30d = filter_by_days(30)
            sales_90d = filter_by_days(90)
            sales_180d = filter_by_days(180)

            # Data harian/bulanan untuk chart filter
            
            # 7 days chart data
            sales_7d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=7))
            sales_7d_chart = sales_7d_qs.annotate(day=TruncDay('verified_at')).values('day').annotate(count=Count('id')).order_by('day')
            sales_7d_chart_data = [{'label': d['day'].strftime('%d %b'), 'value': d['count']} for d in sales_7d_chart]
            
            # Fallback untuk 7 hari jika kosong
            if not sales_7d_chart_data:
                today = timezone.now().date()
                sales_7d_chart_data = [
                    {'label': (today - timedelta(days=i)).strftime('%d %b'), 'value': 0} 
                    for i in range(6, -1, -1)
                ]

            # 30 days chart data
            sales_30d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=30))
            sales_30d_chart = sales_30d_qs.annotate(day=TruncDay('verified_at')).values('day').annotate(count=Count('id')).order_by('day')
            sales_30d_chart_data = [{'label': d['day'].strftime('%d %b'), 'value': d['count']} for d in sales_30d_chart]
            
            # Fallback untuk 30 hari jika kosong
            if not sales_30d_chart_data:
                today = timezone.now().date()
                sales_30d_chart_data = [
                    {'label': (today - timedelta(days=i)).strftime('%d %b'), 'value': 0} 
                    for i in range(29, -1, -7)  # Sample setiap 7 hari
                ]

            # 90 days chart data
            sales_90d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=90))
            sales_90d_chart = sales_90d_qs.annotate(month=TruncMonth('verified_at')).values('month').annotate(count=Count('id')).order_by('month')
            sales_90d_chart_data = [{'label': d['month'].strftime('%b %Y'), 'value': d['count']} for d in sales_90d_chart]
            
            # Fallback untuk 90 hari jika kosong
            if not sales_90d_chart_data:
                today = timezone.now().date()
                sales_90d_chart_data = [
                    {'label': (today.replace(day=1) - timedelta(days=i*30)).strftime('%b %Y'), 'value': 0} 
                    for i in range(2, -1, -1)  # 3 bulan terakhir
                ]

            # 180 days chart data
            sales_180d_qs = PaymentProof.objects.filter(status='approved', verified_at__gte=timezone.now() - timedelta(days=180))
            sales_180d_chart = sales_180d_qs.annotate(month=TruncMonth('verified_at')).values('month').annotate(count=Count('id')).order_by('month')
            sales_180d_chart_data = [{'label': d['month'].strftime('%b %Y'), 'value': d['count']} for d in sales_180d_chart]
            
            # Fallback untuk 180 hari jika kosong
            if not sales_180d_chart_data:
                today = timezone.now().date()
                sales_180d_chart_data = [
                    {'label': (today.replace(day=1) - timedelta(days=i*30)).strftime('%b %Y'), 'value': 0} 
                    for i in range(5, -1, -1)  # 6 bulan terakhir
                ]

            context.update({
                'operator_stats': {
                    'total_users': total_users,
                    'new_users_today': new_users_today,
                    'new_users_this_month': new_users_this_month,
                    'total_payments': total_payments,
                    'pending_payments': pending_payments,
                    'approved_payments': approved_payments,
                    'rejected_payments': rejected_payments,
                    'total_subscriptions': total_subscriptions,
                    'active_subscriptions': active_subscriptions,
                    'expired_subscriptions': expired_subscriptions,
                    'recent_payments': recent_payments,
                    'recent_subscriptions': recent_subscriptions,
                    'monthly_data': monthly_data,
                    'growth_percent': growth_percent,
                    'sales_7d': sales_7d,
                    'sales_30d': sales_30d,
                    'sales_90d': sales_90d,
                    'sales_180d': sales_180d,
                    'sales_7d_chart': sales_7d_chart_data,
                    'sales_30d_chart': sales_30d_chart_data,
                    'sales_90d_chart': sales_90d_chart_data,
                    'sales_180d_chart': sales_180d_chart_data,
                },
                'pending_payments_count': pending_payments  # For sidebar notification
            })
    else:
        # Not logged in - show public home with packages preview
        featured_packages = SubscriptionPackage.objects.filter(
            is_active=True, 
            is_featured=True
        ).order_by('price')[:3]
        
        context.update({
            'featured_packages': featured_packages
        })
    
    return render(request, 'home.html', context)


# ------------------------- TEACHER VIEWS -------------------------


@login_required
@admin_or_teacher_required
def teacher_category_list(request):
    """List categories owned by the teacher (or all for admin)."""
    if request.user.is_admin():
        categories = Category.objects.all().order_by('-id')
    else:
        categories = Category.objects.filter(
            Q(created_by=request.user) | Q(teachers=request.user)
        ).distinct().order_by('-id')

    paginator = Paginator(categories, 10)
    page = request.GET.get('page')
    try:
        categories_page = paginator.page(page)
    except PageNotAnInteger:
        categories_page = paginator.page(1)
    except EmptyPage:
        categories_page = paginator.page(paginator.num_pages)

    return render(request, 'teacher/category_list.html', {'categories': categories_page, 'paginator': paginator})


@login_required
@admin_or_teacher_required
def teacher_category_create(request):
    if request.method == 'POST':
        form = CategoryCreationForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            # Save M2M teachers and auto-assign the creator as a teacher
            try:
                form.save_m2m()
            except Exception:
                pass
            try:
                # Ensure the creator is assigned as a teacher for their own category
                category.teachers.add(request.user)
            except Exception:
                pass
            messages.success(request, 'Kategori berhasil dibuat.')
            return redirect('teacher_category_list')
        else:
            # Log form errors for debugging
            try:
                from django.utils.log import getLogger
                logger = getLogger(__name__)
            except Exception:
                logger = None
            if logger:
                logger.error('Category creation form invalid: %s', form.errors.as_json())
            # Also print and show message for immediate feedback during debugging
            try:
                print('Category creation form invalid:', form.errors.as_json())
            except Exception:
                try:
                    print('Category creation form invalid:', form.errors)
                except Exception:
                    pass
            try:
                messages.error(request, 'Form validation failed: ' + form.errors.as_text())
            except Exception:
                pass
    else:
        form = CategoryCreationForm()

    return render(request, 'teacher/category_form.html', {'form': form, 'title': 'Buat Kategori'})


@login_required
@admin_or_teacher_required
def teacher_category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    # only allow owner or admin
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    if request.method == 'POST':
        form = CategoryUpdateForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            try:
                form.save_m2m()
            except Exception:
                pass
            messages.success(request, 'Kategori berhasil diperbarui.')
            return redirect('teacher_category_list')
    else:
        form = CategoryUpdateForm(instance=category)

    return render(request, 'teacher/category_form.html', {'form': form, 'title': 'Edit Kategori'})


@login_required
@admin_or_teacher_required
def teacher_category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Kategori dihapus.')
        return redirect('teacher_category_list')

    return render(request, 'teacher/category_confirm_delete.html', {'category': category})


@login_required
@admin_or_teacher_required
def teacher_question_list(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    questions = Question.objects.filter(category=category).order_by('-pub_date')
    paginator = Paginator(questions, 10)
    page = request.GET.get('page')
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)

    return render(request, 'teacher/question_list.html', {'questions': questions_page, 'category': category})


@login_required
@admin_or_teacher_required
def teacher_question_create(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    if request.method == 'POST':
        # Ensure the bound form includes the category id so the required
        # `category` field validates. Teachers shouldn't change category, so
        # inject it into the POST data before binding.
        post_data = request.POST.copy()
        post_data['category'] = str(category.id)
        form = QuestionForm(post_data)
        formset = ChoiceFormSet(post_data)

        # DEBUG: show incoming POST data for choices
        try:
            print('\n[DEBUG] teacher_question_create POST data:')
            for i in range(5):
                choice_text = request.POST.get(f'choices-{i}-choice_text', '')
                is_correct = request.POST.get(f'choices-{i}-is_correct', '')
                choice_letter = chr(65 + i)  # A, B, C, D, E
                print(f'  Choice {choice_letter}: text="{choice_text[:30]}..." is_correct="{is_correct}"')
        except Exception:
            pass

        if form.is_valid():
            question = form.save(commit=False)
            question.pub_date = timezone.now()
            question.category = category
            
            # For essay questions, choices are not required
            if question.question_type == 'essay':
                question.save()
                messages.success(request, 'Soal isian berhasil dibuat!')
                return redirect('teacher_question_list', category_id=category.id)
            
            # For multiple choice questions, use custom choice saving logic
            elif question.question_type == 'multiple_choice':
                print(f'[DEBUG] Formset is_valid: {formset.is_valid()}')
                
                # CUSTOM VALIDATION: Check if formset errors are only from optional choices (C, D, E)
                can_proceed = False
                if formset.is_valid():
                    can_proceed = True
                    print('[DEBUG] Formset is valid')
                else:
                    print('[DEBUG] Formset errors - checking if only optional choices have errors')
                    
                    # Check if errors are only from optional choices (index 2, 3, 4 = C, D, E)
                    critical_errors = False
                    for i, form in enumerate(formset.forms):
                        if form.errors:
                            print(f'  Form {i} ({chr(65+i)}) errors:', form.errors)
                            # Only consider errors from A & B (index 0, 1) as critical
                            if i <= 1:
                                critical_errors = True
                                print(f'    -> CRITICAL ERROR in required choice {chr(65+i)}')
                    
                    # Check for critical non-form errors
                    if formset.non_form_errors():
                        non_form_errors = formset.non_form_errors()
                        print('[DEBUG] Non-form errors detected:', non_form_errors)
                        error_text = str(non_form_errors).lower()
                        if 'choice a' in error_text or 'choice b' in error_text:
                            critical_errors = True
                    
                    if not critical_errors:
                        can_proceed = True
                        print('[DEBUG] Only optional choice errors - proceeding anyway')
                
                if can_proceed:
                    # Check if at least one choice is marked as correct
                    correct_choices = 0
                    for i in range(5):
                        checkbox_name = f'choices-{i}-is_correct'
                        checkbox_value = request.POST.get(checkbox_name, None)
                        if checkbox_value == 'on' or checkbox_value == 'true' or checkbox_value is True:
                            correct_choices += 1
                    
                    if correct_choices == 0:
                        messages.error(request, 'Minimal satu pilihan harus ditandai sebagai jawaban yang benar.')
                        return render(request, 'admin/manage_questions/question_form.html', {
                            'form': form,
                            'formset': formset,
                            'category': category
                        })
                    
                    question.save()
                    
                    # CRITICAL FIX: Force save ALL choices (A through E) even if some are empty
                    print('[DEBUG] Saving all 5 choices manually...')
                    
                    saved_choice_count = 0
                    for i in range(5):  # Always process choices 0-4 (A-E)
                        choice_letter = chr(65 + i)  # A, B, C, D, E
                        
                        # Get data from POST directly
                        choice_text = request.POST.get(f'choices-{i}-choice_text', '').strip()
                        is_correct_raw = request.POST.get(f'choices-{i}-is_correct', '')
                        is_correct = is_correct_raw in ['on', 'true', True]
                        
                        print(f'[DEBUG] Creating Choice {choice_letter}: text="{choice_text[:30]}..." is_correct={is_correct}')
                        
                        # ALWAYS create choice object, even if empty (to maintain A-E structure)
                        from .models import Choice
                        choice_obj = Choice()
                        choice_obj.question = question
                        choice_obj.choice_text = choice_text
                        choice_obj.is_correct = is_correct
                        
                        # Handle choice image
                        choice_image_url = request.POST.get(f'choice_image_{i+1}')
                        if choice_image_url and choice_image_url.strip():
                            import urllib.parse
                            from django.core.files.storage import default_storage
                            
                            parsed_url = urllib.parse.urlparse(choice_image_url)
                            if choice_image_url.startswith('https://') and 'blob.vercel-storage.com' in choice_image_url:
                                choice_obj.choice_image = choice_image_url
                            elif parsed_url.path.startswith('/media/'):
                                file_path = parsed_url.path[7:]
                                if default_storage.exists(file_path):
                                    choice_obj.choice_image = file_path
                        
                        choice_obj.save()
                        saved_choice_count += 1
                        print(f'[DEBUG] Saved Choice {choice_letter} with ID: {choice_obj.id}')
                    
                    print(f'[DEBUG] Total choices saved: {saved_choice_count}')
                    messages.success(request, 'Soal berhasil dibuat.')
                    return redirect('teacher_question_list', category_id=category.id)
                else:
                    messages.error(request, 'Terjadi kesalahan validasi pada pilihan jawaban.')
            else:
                messages.error(request, 'Tipe soal tidak valid.')
        else:
            # Debug: expose validation errors
            try:
                form_json = form.errors.as_json()
            except Exception:
                form_json = str(form.errors)
            try:
                formset_errors = formset.errors
                formset_non = formset.non_form_errors()
            except Exception:
                formset_errors = str(formset.errors)
                formset_non = str(formset.non_form_errors())
            print('\n[DEBUG] teacher_question_create validation failed')
            print('Form errors (json):', form_json)
            print('Formset errors:', formset_errors)
            print('Formset non-field errors:', formset_non)
            messages.error(request, 'Form validation failed: ' + (form.errors.as_text() or str(formset_errors)))
    else:
        form = QuestionForm(initial={'category': category})
        formset = ChoiceFormSet()

    return render(request, 'admin/manage_questions/question_form.html', {'form': form, 'formset': formset, 'category': category})


@login_required
@admin_or_teacher_required
def teacher_question_update(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    category = question.category
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    if request.method == 'POST':
        form = QuestionUpdateForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, instance=question)

        # DEBUG: show incoming POST data for choices
        try:
            print('\n[DEBUG] teacher_question_update POST data:')
            for i in range(5):
                choice_text = request.POST.get(f'choices-{i}-choice_text', '')
                is_correct = request.POST.get(f'choices-{i}-is_correct', '')
                choice_letter = chr(65 + i)  # A, B, C, D, E
                print(f'  Choice {choice_letter}: text="{choice_text[:30]}..." is_correct="{is_correct}"')
        except Exception:
            pass

        if form.is_valid():
            updated_question = form.save()
            
            # For essay questions, choices are not required
            if updated_question.question_type == 'essay':
                # Delete existing choices for essay questions
                from .models import Choice
                Choice.objects.filter(question=updated_question).delete()
                messages.success(request, 'Soal isian berhasil diperbarui!')
                return redirect('teacher_question_list', category_id=category.id)
            
            # For multiple choice questions, use custom choice saving logic
            elif updated_question.question_type == 'multiple_choice':
                print(f'[DEBUG] Formset is_valid: {formset.is_valid()}')
                
                # CUSTOM VALIDATION: Check if formset errors are only from optional choices (C, D, E)
                can_proceed = False
                if formset.is_valid():
                    can_proceed = True
                    print('[DEBUG] Formset is valid')
                else:
                    print('[DEBUG] Formset errors - checking if only optional choices have errors')
                    
                    # Check if errors are only from optional choices (index 2, 3, 4 = C, D, E)
                    critical_errors = False
                    for i, form in enumerate(formset.forms):
                        if form.errors:
                            print(f'  Form {i} ({chr(65+i)}) errors:', form.errors)
                            # Only consider errors from A & B (index 0, 1) as critical
                            if i <= 1:
                                critical_errors = True
                                print(f'    -> CRITICAL ERROR in required choice {chr(65+i)}')
                    
                    # Check for critical non-form errors
                    if formset.non_form_errors():
                        non_form_errors = formset.non_form_errors()
                        print('[DEBUG] Non-form errors detected:', non_form_errors)
                        error_text = str(non_form_errors).lower()
                        if 'choice a' in error_text or 'choice b' in error_text:
                            critical_errors = True
                    
                    if not critical_errors:
                        can_proceed = True
                        print('[DEBUG] Only optional choice errors - proceeding anyway')
                
                if can_proceed:
                    # Check if at least one choice is marked as correct
                    correct_choices = 0
                    for i in range(5):
                        checkbox_name = f'choices-{i}-is_correct'
                        checkbox_value = request.POST.get(checkbox_name, None)
                        if checkbox_value == 'on' or checkbox_value == 'true' or checkbox_value is True:
                            correct_choices += 1
                    
                    if correct_choices == 0:
                        messages.error(request, 'Minimal satu pilihan harus ditandai sebagai jawaban yang benar.')
                        return render(request, 'admin/manage_questions/question_form.html', {
                            'form': form,
                            'formset': formset,
                            'category': category,
                            'question': question
                        })
                    
                    # CRITICAL FIX: Delete existing choices and create new ones
                    print('[DEBUG] Deleting existing choices and creating new ones...')
                    from .models import Choice
                    Choice.objects.filter(question=updated_question).delete()
                    
                    saved_choice_count = 0
                    for i in range(5):  # Always process choices 0-4 (A-E)
                        choice_letter = chr(65 + i)  # A, B, C, D, E
                        
                        # Get data from POST directly
                        choice_text = request.POST.get(f'choices-{i}-choice_text', '').strip()
                        is_correct_raw = request.POST.get(f'choices-{i}-is_correct', '')
                        is_correct = is_correct_raw in ['on', 'true', True]
                        
                        print(f'[DEBUG] Creating Choice {choice_letter}: text="{choice_text[:30]}..." is_correct={is_correct}')
                        
                        # ALWAYS create choice object, even if empty (to maintain A-E structure)
                        choice_obj = Choice()
                        choice_obj.question = updated_question
                        choice_obj.choice_text = choice_text
                        choice_obj.is_correct = is_correct
                        
                        # Handle choice image
                        choice_image_url = request.POST.get(f'choice_image_{i+1}')
                        if choice_image_url and choice_image_url.strip():
                            import urllib.parse
                            from django.core.files.storage import default_storage
                            
                            parsed_url = urllib.parse.urlparse(choice_image_url)
                            if choice_image_url.startswith('https://') and 'blob.vercel-storage.com' in choice_image_url:
                                choice_obj.choice_image = choice_image_url
                            elif parsed_url.path.startswith('/media/'):
                                file_path = parsed_url.path[7:]
                                if default_storage.exists(file_path):
                                    choice_obj.choice_image = file_path
                        
                        choice_obj.save()
                        saved_choice_count += 1
                        print(f'[DEBUG] Saved Choice {choice_letter} with ID: {choice_obj.id}')
                    
                    print(f'[DEBUG] Total choices saved: {saved_choice_count}')
                    messages.success(request, 'Soal berhasil diperbarui.')
                    return redirect('teacher_question_list', category_id=category.id)
                else:
                    messages.error(request, 'Terjadi kesalahan validasi pada pilihan jawaban.')
            else:
                messages.error(request, 'Tipe soal tidak valid.')
        else:
            # Debug: show why update failed
            try:
                form_json = form.errors.as_json()
            except Exception:
                form_json = str(form.errors)
            try:
                formset_errors = formset.errors
                formset_non = formset.non_form_errors()
            except Exception:
                formset_errors = str(formset.errors)
                formset_non = str(formset.non_form_errors())
            print('\n[DEBUG] teacher_question_update validation failed')
            print('Form errors (json):', form_json)
            print('Formset errors:', formset_errors)
            print('Formset non-field errors:', formset_non)
            messages.error(request, 'Form validation failed: ' + (form.errors.as_text() or str(formset_errors)))
    else:
        form = QuestionUpdateForm(instance=question)
        formset = ChoiceFormSet(instance=question)
        
        # Prepare initial data for choice images (for edit)
        choices = question.choices.all()
        initial_data = {}
        for i, choice in enumerate(choices, 1):
            if choice.choice_image:
                # Handle both Vercel Blob URLs and legacy media URLs
                image_name = choice.choice_image.name
                if image_name.startswith('https://'):
                    # Already a full URL (Vercel Blob)
                    initial_data[f'choice_image_{i}'] = image_name
                else:
                    # Legacy media file - construct full URL
                    try:
                        initial_data[f'choice_image_{i}'] = choice.choice_image.url
                    except Exception:
                        # Fallback if URL generation fails
                        initial_data[f'choice_image_{i}'] = f'/media/{image_name}'
        
        # DEBUG: Print initial data for debugging
        print(f'\n[DEBUG] teacher_question_update GET - Question ID: {question.id}')
        print(f'[DEBUG] Initial choice images data: {initial_data}')

    return render(request, 'admin/manage_questions/question_form.html', {
        'form': form, 
        'formset': formset, 
        'category': category, 
        'question': question,
        'initial_choice_images': initial_data if 'initial_data' in locals() else {}
    })


@login_required
@admin_or_teacher_required
def teacher_question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    category = question.category
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Soal dihapus.')
        return redirect('teacher_question_list', category_id=category.id)

    return render(request, 'teacher/question_confirm_delete.html', {'question': question})


@login_required
@admin_or_teacher_required
def teacher_view_student_scores(request, category_id):
    """Show students' tests and scores for a given teacher-owned category."""
    category = get_object_or_404(Category, id=category_id)
    if not (request.user.is_admin() or category.created_by == request.user or category.teachers.filter(pk=request.user.pk).exists()):
        raise PermissionDenied

    # Get all submitted tests that include this category (show every attempt)
    tests_qs = Test.objects.filter(
        categories=category,
        is_submitted=True
    ).select_related('student').distinct()

    # Annotate correct and wrong counts per test for this category so we can sort by them
    tests_qs = tests_qs.annotate(
        correct_count_ann=Count(
            'answers', 
            filter=Q(answers__question__category=category) & (
                Q(answers__selected_choice__is_correct=True) | 
                Q(answers__question__question_type='essay', answers__text_answer__isnull=False)
            ), 
            distinct=True
        ),
        wrong_count_ann=Count(
            'answers', 
            filter=Q(answers__question__category=category) & (
                Q(answers__selected_choice__is_correct=False) |
                Q(answers__question__question_type='essay', answers__text_answer__isnull=True)
            ), 
            distinct=True
        ),
    )

    # Sorting support via query params: ?sort=score|correct&order=asc|desc
    sort = request.GET.get('sort', 'date')
    order = request.GET.get('order', 'desc')
    if sort == 'score':
        sort_field = 'score'
    elif sort == 'correct':
        sort_field = 'correct_count_ann'
    else:
        sort_field = 'date_taken'

    if order == 'asc':
        tests_qs = tests_qs.order_by(sort_field)
    else:
        tests_qs = tests_qs.order_by('-' + sort_field)

    paginator = Paginator(tests_qs, 15)
    page = request.GET.get('page')
    try:
        tests_page = paginator.page(page)
    except PageNotAnInteger:
        tests_page = paginator.page(1)
    except EmptyPage:
        tests_page = paginator.page(paginator.num_pages)

    # For each test on the current page, compute number of correct and wrong answers
    # but only counting answers that belong to this category (a test can include multiple categories)
    for test in tests_page:
        # Prefer annotated counts when available (on the queryset), otherwise compute fallback
        test.correct_count = getattr(test, 'correct_count_ann', None)
        test.wrong_count = getattr(test, 'wrong_count_ann', None)
        if test.correct_count is None:
            # Count multiple choice correct answers
            mc_correct = Answer.objects.filter(
                test=test, 
                question__category=category, 
                selected_choice__is_correct=True
            ).count()
            
            # Count essay correct answers (case-insensitive exact match)
            essay_correct = 0
            essay_answers = Answer.objects.filter(
                test=test,
                question__category=category,
                question__question_type='essay',
                text_answer__isnull=False
            ).exclude(text_answer='')
            
            for answer in essay_answers:
                if (answer.question.correct_answer_text and 
                    answer.text_answer.strip().lower() == answer.question.correct_answer_text.strip().lower()):
                    essay_correct += 1
            
            test.correct_count = mc_correct + essay_correct
            
        if test.wrong_count is None:
            # Count multiple choice wrong answers
            mc_wrong = Answer.objects.filter(
                test=test, 
                question__category=category, 
                selected_choice__is_correct=False
            ).count()
            
            # Count essay wrong answers (including empty answers)
            essay_wrong = 0
            essay_questions = test.answers.filter(
                question__category=category,
                question__question_type='essay'
            ).count()
            
            essay_wrong = essay_questions - (test.correct_count - Answer.objects.filter(
                test=test, 
                question__category=category, 
                selected_choice__is_correct=True
            ).count())
            
            test.wrong_count = mc_wrong + max(0, essay_wrong)
        # Percentage correct for this category (based on answered questions in this category)
        total_answered = (test.correct_count or 0) + (test.wrong_count or 0)
        if total_answered > 0:
            try:
                test.percent_correct = round((test.correct_count / total_answered) * 100, 1)
            except Exception:
                test.percent_correct = 0.0
        else:
            test.percent_correct = 0.0

    return render(request, 'teacher/student_scores.html', {'tests': tests_page, 'category': category})


@login_required
@admin_or_teacher_required
def teacher_test_review(request, category_id, test_id):
    """Dedicated teacher review page showing only the questions/answers for a specific
    category (subtest) within a student's test. Accessible only to admins or teachers
    assigned to the category (created_by or in category.teachers).
    """
    category = get_object_or_404(Category, id=category_id)
    test = get_object_or_404(Test, id=test_id)

    # Guard: ensure the category is actually part of this test (either linked directly
    # via test.categories or included in the tryout_package composition). If not, return 404.
    category_in_test = False
    if test.categories.filter(pk=category.pk).exists():
        category_in_test = True
    elif test.tryout_package and test.tryout_package.categories.filter(pk=category.pk).exists():
        category_in_test = True

    if not category_in_test:
        raise Http404('Category not found in this test')

    # Permission: allow admins or teachers assigned to this category
    is_owner_teacher = False
    if category.created_by and category.created_by == request.user:
        is_owner_teacher = True
    if category.teachers.filter(pk=request.user.pk).exists():
        is_owner_teacher = True

    if not (request.user.is_superuser or request.user.is_admin() or is_owner_teacher):
        raise PermissionDenied

    # Collect questions that belong to this category and assemble answer data
    question_list = []

    if test.tryout_package:
        # package: limit to questions from this category within the package ordering
        questions_qs = Question.objects.filter(category=category).order_by('id')
    else:
        # non-package: test.categories should include category; still filter
        questions_qs = Question.objects.filter(category=category).order_by('id')

    total_questions = questions_qs.count()
    correct_count = 0

    for q in questions_qs:
        ans = test.answers.filter(question=q).select_related('selected_choice').first()
        
        if q.question_type == 'essay':
            # Handle essay questions
            is_correct = False
            your_answer = None
            if ans and ans.text_answer:
                your_answer = ans.text_answer.strip()
                # Check if essay answer is correct (case-insensitive exact match)
                if q.correct_answer_text and your_answer.lower() == q.correct_answer_text.lower():
                    is_correct = True
            
            if is_correct:
                correct_count += 1

            question_list.append({
                'question_text': q.question_text,
                'question_type': q.question_type,
                'your_answer': your_answer,
                'is_correct': is_correct,
                'correct_answer_text': q.correct_answer_text,
                'question_obj': q,
                'all_choices': [],  # Empty for essay questions
                'your_choice_label': None,
                'correct_choice_label': None,
            })
        else:
            # Handle multiple choice questions
            selected_choice = ans.selected_choice if ans else None
            correct_choice = q.choices.filter(is_correct=True).first()
            is_correct = (selected_choice.is_correct) if selected_choice else False
            if is_correct:
                correct_count += 1

            # Build labeled choices (A, B, C...)
            all_choices = []
            choices_qs = list(q.choices.all().order_by('id'))
            for idx, ch in enumerate(choices_qs):
                label = chr(65 + idx)
                all_choices.append({'label': label, 'id': ch.id, 'text': ch.choice_text, 'is_correct': ch.is_correct})

            your_answer_label = None
            correct_answer_label = None
            if selected_choice:
                for c in all_choices:
                    if c['id'] == selected_choice.id:
                        your_answer_label = c['label']
                        break
            if correct_choice:
                for c in all_choices:
                    if c['id'] == correct_choice.id:
                        correct_answer_label = c['label']
                        break

            question_list.append({
                'question_text': q.question_text,
                'question_type': q.question_type,
                'your_answer': selected_choice.choice_text if selected_choice else None,
                'is_correct': is_correct,
                'correct_answer': correct_choice.choice_text if correct_choice else None,
                'correct_answer_text': getattr(q, 'correct_answer_text', None),
                'question_obj': q,
                'all_choices': all_choices,
                'your_choice_label': your_answer_label,
                'correct_choice_label': correct_answer_label,
            })

    percent_correct = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0

    context = {
        'test': test,
        'category': category,
        'questions': question_list,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'percent_correct': percent_correct,
    }

    return render(request, 'teacher/test_review_detail.html', context)


@login_required
@admin_or_teacher_required
def teacher_student_list(request):
    """Show a card-style list of subtests (categories) that the teacher created."""
    # Admins see all categories, teachers only their own
    if request.user.is_admin():
        categories = Category.objects.all().order_by('-id')
    else:
        categories = Category.objects.filter(
            Q(created_by=request.user) | Q(teachers=request.user)
        ).distinct().order_by('-id')

    # Add quick stats
    for cat in categories:
        stats = cat.get_test_statistics()
        cat.total_students = stats['total_students']
        cat.total_tests = stats['total_tests']
        cat.avg_score = stats['average_score']
        # Attach average completion time (minutes) if available
        cat.avg_completion_minutes = stats.get('average_completion_minutes')
        # Flag to indicate an average score exists (could be 0)
        cat.has_avg_score = stats.get('average_score') is not None

    return render(request, 'teacher/student_performance.html', {'categories': categories})


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after successful registration
            return redirect('home')  # Redirect to home or another page
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

##User View##

@login_required
@admin_or_operator_required
def user_list(request):
    users_list = User.objects.all().order_by('-date_joined')
    
    # If the current user is an operator, exclude admin users
    if request.user.is_operator():
        users_list = users_list.exclude(role__role_name='Admin')
    
    q = request.GET.get('q', '').strip()
    role = request.GET.get('role', '').strip()
    if q:
        users_list = users_list.filter(
            Q(email__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(phone_number__icontains=q)
        )
    if role:
        users_list = users_list.filter(role__role_name=role)

    paginator = Paginator(users_list, 10)  # Show 10 users per page
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)

    # Stat cards for roles
    from otosapp.models import Role
    student_count = User.objects.filter(role__role_name='Student').count()
    teacher_count = User.objects.filter(role__role_name='Teacher').count()
    operator_count = User.objects.filter(role__role_name='Operator').count()

    return render(request, 'admin/manage_user/user_list.html', {
        'users': users,
        'paginator': paginator,
        'student_count': student_count,
        'teacher_count': teacher_count,
        'operator_count': operator_count,
    })
    

@login_required
@admin_or_operator_required
def user_create(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, current_user=request.user)
        if form.is_valid():
            form.save()
            return redirect('user_list')
    else:
        form = CustomUserCreationForm(current_user=request.user)
    return render(request, 'admin/manage_user/user_form.html', {'form': form, 'title': 'Add New User'})

@login_required
@admin_or_operator_required
def user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Prevent operators from editing admin users
    if request.user.is_operator() and user.is_admin():
        raise PermissionDenied("Operators cannot edit admin users.")
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user, current_user=request.user)
        if form.is_valid():
            # Prevent Operator from assigning Admin role
            try:
                if request.user.role.role_name == 'Operator' and form.cleaned_data.get('role') and form.cleaned_data.get('role').role_name == 'Admin':
                    form.add_error('role', 'Operator tidak memiliki izin untuk memberikan role Admin.')
                else:
                    form.save()
                    return redirect('user_list')
            except Exception:
                # If any unexpected error during role check, avoid silent failure and proceed to save as fallback
                form.save()
                return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user, current_user=request.user)
    return render(request, 'admin/manage_user/user_form.html', {'form': form, 'title': 'Edit User'})

@login_required
@admin_or_operator_required
def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Prevent operators from deleting admin users
    if request.user.is_operator() and user.is_admin():
        raise PermissionDenied("Operators cannot delete admin users.")
    
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'admin/manage_user/user_confirm_delete.html', {'user': user})


##Category View##

@login_required
@admin_or_operator_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryCreationForm(request.POST)
        if form.is_valid():
            # Save instance, set creator, and ensure M2M saved
            category = form.save(commit=False)
            try:
                category.created_by = request.user
            except Exception:
                pass
            category.save()
            try:
                form.save_m2m()
            except Exception:
                pass
            messages.success(request, 'Kategori berhasil dibuat.')
            return redirect('category_list')
    else:
        form = CategoryCreationForm()
    return render(request, {'form': form, 'title': 'Add New Category'})

@login_required
@admin_or_operator_required
def category_list(request):
    categories_list = Category.objects.all()
    q = request.GET.get('q', '').strip()
    scoring_method = request.GET.get('scoring_method', '').strip()
    if q:
        categories_list = categories_list.filter(category_name__icontains=q)
    if scoring_method:
        categories_list = categories_list.filter(scoring_method=scoring_method)

    paginator = Paginator(categories_list, 10)  # Show 10 categories per page
    page = request.GET.get('page')
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)

    # Add scoring status info for each category
    for category in categories:
        if category.scoring_method == 'custom':
            total_points = category.get_total_custom_points()
            category.scoring_status = {
                'complete': category.is_custom_scoring_complete(),
                'total_points': total_points
            }
        else:
            category.scoring_status = {'complete': True, 'total_points': 100}

    form = CategoryCreationForm()

    # Stat cards data
    custom_scoring_count = Category.objects.filter(scoring_method='custom').count()
    utbk_scoring_count = Category.objects.filter(scoring_method='utbk').count()
    total_questions = 0
    for cat in Category.objects.all():
        total_questions += cat.question_set.count()

    return render(request, 'admin/manage_categories/category_list.html', {
        'categories': categories,
        'form': form,
        'paginator': paginator,
        'custom_scoring_count': custom_scoring_count,
        'utbk_scoring_count': utbk_scoring_count,
        'total_questions': total_questions,
        'total_categories': Category.objects.count(),
    })

@login_required
@admin_or_operator_required
def category_update(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        form = CategoryUpdateForm(request.POST, instance=category)
        if form.is_valid():
            old_scoring_method = Category.objects.get(id=category_id).scoring_method
            new_category = form.save()
            try:
                form.save_m2m()
            except Exception:
                pass
            
            # Check custom scoring validation
            if new_category.scoring_method == 'custom':
                if not new_category.is_custom_scoring_complete():
                    total_points = new_category.get_total_custom_points()
                    messages.warning(
                        request, 
                        f'Warning: Custom scoring incomplete! Total points: {total_points}/100. Please update question weights.'
                    )
            
            # Update UTBK coefficients if switching to UTBK method
            if new_category.scoring_method == 'utbk' and old_scoring_method != 'utbk':
                Test.update_utbk_difficulty_coefficients(category_id)
                messages.info(request, 'UTBK difficulty coefficients have been calculated based on existing data.')
            
            return redirect('category_list')
    else:
        form = CategoryUpdateForm(instance=category)
    
    # Add warnings for current category
    warnings = []
    if category.scoring_method == 'custom' and not category.is_custom_scoring_complete():
        total_points = category.get_total_custom_points()
        warnings.append(f'Custom scoring incomplete! Total points: {total_points}/100')
    
    context = {
        'form': form, 
        'category_id': category_id,
        'category': category,
        'warnings': warnings
    }
    return render(request, 'admin/manage_categories/category_form.html', context)

@login_required
@admin_or_operator_required
def category_delete(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, {'category': category})

@login_required
@admin_required
def update_utbk_coefficients(request, category_id):
    """Manually update UTBK difficulty coefficients for a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if category.scoring_method != 'utbk':
        messages.error(request, f'Category "{category.category_name}" is not using UTBK scoring method.')
    else:
        Test.update_utbk_difficulty_coefficients(category_id)
        messages.success(request, f'UTBK difficulty coefficients updated for "{category.category_name}".')
    
    return redirect('category_list')

# Update all UTBK coefficients for all categories with scoring_method='utbk'
@login_required
@admin_required
@require_POST
def update_all_utbk_coefficients(request):
    utbk_categories = Category.objects.filter(scoring_method='utbk')
    updated_count = 0
    for category in utbk_categories:
        Test.update_utbk_difficulty_coefficients(category.id)
        updated_count += 1
    if updated_count:
        messages.success(request, f'UTBK coefficients updated for {updated_count} categories.')
    else:
        messages.info(request, 'No UTBK categories found to update.')
    return redirect('category_list')

##Question View##

@login_required
@admin_or_teacher_or_operator_required
def question_list(request):
    """Display category selection page for questions"""
    categories_list = Category.objects.all().order_by('category_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        categories_list = categories_list.filter(
            Q(category_name__icontains=search_query)
        )
    
    # Filter by scoring method
    scoring_method_filter = request.GET.get('scoring_method', '')
    if scoring_method_filter:
        categories_list = categories_list.filter(scoring_method=scoring_method_filter)
    
    # Filter by completion status (for custom scoring)
    completion_filter = request.GET.get('completion', '')
    
    # Sort options
    sort_by = request.GET.get('sort', 'category_name')
    valid_sorts = ['category_name', '-category_name', 'time_limit', '-time_limit', 'passing_score', '-passing_score']
    if sort_by in valid_sorts:
        categories_list = categories_list.order_by(sort_by)
    
    # Add question count and scoring status for each category
    for category in categories_list:
        category.question_count = category.question_set.count()
        if category.scoring_method == 'custom':
            total_points = category.get_total_custom_points()
            category.scoring_status = {
                'complete': category.is_custom_scoring_complete(),
                'total_points': total_points
            }
        else:
            category.scoring_status = {'complete': True, 'total_points': 100}
    
    # Filter by completion status after calculating scoring status
    if completion_filter:
        if completion_filter == 'complete':
            categories_list = [cat for cat in categories_list if cat.scoring_status['complete']]
        elif completion_filter == 'incomplete':
            categories_list = [cat for cat in categories_list if not cat.scoring_status['complete']]
    
    # Pagination
    paginator = Paginator(categories_list, 10)  # Show 10 categories per page
    page = request.GET.get('page')
    
    try:
        categories = paginator.page(page)
    except PageNotAnInteger:
        categories = paginator.page(1)
    except EmptyPage:
        categories = paginator.page(paginator.num_pages)
    
    # Stats for dashboard
    total_categories = Category.objects.count()
    custom_scoring_count = Category.objects.filter(scoring_method='custom').count()
    utbk_scoring_count = Category.objects.filter(scoring_method='utbk').count()
    
    context = {
        'categories': categories,
        'paginator': paginator,
        'search_query': search_query,
        'scoring_method_filter': scoring_method_filter,
        'completion_filter': completion_filter,
        'sort_by': sort_by,
        'total_categories': total_categories,
        'custom_scoring_count': custom_scoring_count,
        'utbk_scoring_count': utbk_scoring_count,
        'total_questions': sum(cat.question_count for cat in categories_list if hasattr(cat, 'question_count')),
    }
    
    return render(request, 'admin/manage_questions/category_selection.html', context)

@login_required
@admin_or_teacher_or_operator_required
def question_list_by_category(request, category_id):
    """Display questions filtered by category"""
    category = get_object_or_404(Category, id=category_id)
    questions_list = Question.objects.filter(category=category).order_by('-pub_date')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        questions_list = questions_list.filter(
            Q(question_text__icontains=search_query) |
            Q(choices__choice_text__icontains=search_query)
        ).distinct()
    
    # Filter by scoring status (for custom scoring)
    scoring_filter = request.GET.get('scoring_filter', '')
    if scoring_filter and category.scoring_method == 'custom':
        if scoring_filter == 'with_weight':
            questions_list = questions_list.filter(custom_weight__gt=0)
        elif scoring_filter == 'no_weight':
            questions_list = questions_list.filter(custom_weight=0)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            questions_list = questions_list.filter(pub_date__date__gte=date_from_obj)
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            questions_list = questions_list.filter(pub_date__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Sort options
    sort_by = request.GET.get('sort', '-pub_date')
    valid_sorts = ['-pub_date', 'pub_date', 'question_text', '-question_text']
    if category.scoring_method == 'custom':
        valid_sorts.extend(['-custom_weight', 'custom_weight'])
    elif category.scoring_method == 'utbk':
        valid_sorts.extend(['-difficulty_coefficient', 'difficulty_coefficient'])
    
    if sort_by in valid_sorts:
        questions_list = questions_list.order_by(sort_by)
    
    # Add scoring status for category
    if category.scoring_method == 'custom':
        total_points = category.get_total_custom_points()
        category.scoring_status = {
            'complete': category.is_custom_scoring_complete(),
            'total_points': total_points
        }
    else:
        category.scoring_status = {'complete': True, 'total_points': 100}
    
    paginator = Paginator(questions_list, 15)  # Show 15 questions per page
    
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)
        
    context = {
        'questions': questions,
        'category': category,
        'paginator': paginator,
        'search_query': search_query,
        'scoring_filter': scoring_filter,
        'date_from': date_from,
        'date_to': date_to,
        'sort_by': sort_by,
        'total_questions': questions_list.count(),
    }
    
    return render(request, 'admin/manage_questions/question_list.html', context)

@login_required
@admin_or_teacher_or_operator_required
def question_create(request):
    # Pre-select category from URL parameter
    category_id = request.GET.get('category')
    initial_category = None
    if category_id:
        try:
            initial_category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST)

        # DEBUG: show incoming POST and FILES keys to diagnose validation issues
        try:
            print('\n[DEBUG] question_create POST keys:', list(request.POST.keys()))
            print('[DEBUG] question_create FILES keys:', list(request.FILES.keys()))
            
            # Debug checkbox values specifically
            print('\n[DEBUG] Checkbox values:')
            for key in request.POST.keys():
                if 'is_correct' in key:
                    print(f'  {key}: {request.POST.get(key)}')
            
            # Debug formset structure
            print('\n[DEBUG] Formset info:')
            print(f'  TOTAL_FORMS: {request.POST.get("choices-TOTAL_FORMS")}')
            print(f'  INITIAL_FORMS: {request.POST.get("choices-INITIAL_FORMS")}')
            
            # Debug each choice data
            print('\n[DEBUG] Choice data from POST:')
            for i in range(5):
                choice_text = request.POST.get(f'choices-{i}-choice_text', '')
                is_correct = request.POST.get(f'choices-{i}-is_correct', '')
                # Handle both checkbox "on" values and hidden field "true"/"false" values
                is_correct_bool = is_correct in ['on', 'true', True]
                print(f'  Choice {i+1}: text="{choice_text[:30]}..." is_correct="{is_correct}" -> {is_correct_bool}')
            
        except Exception as _:
            pass
        
        if form.is_valid():
            question = form.save(commit=False)
            if hasattr(request.user, 'created_by'):
                question.created_by = request.user
            
            # For essay questions, choices are not required
            if question.question_type == 'essay':
                question.save()
                messages.success(request, 'Soal isian berhasil dibuat!')
                
                # Redirect to category-specific question list if came from there
                if question.category:
                    return redirect('question_list_by_category', category_id=question.category.id)
                return redirect('question_list')
            
            # For multiple choice questions, validate and save choices
            elif question.question_type == 'multiple_choice':
                print(f'[DEBUG] Formset is_valid: {formset.is_valid()}')
                
                # CUSTOM VALIDATION: Check if formset errors are only from optional choices (C, D, E)
                can_proceed = False
                if formset.is_valid():
                    can_proceed = True
                    print('[DEBUG] Formset is valid')
                else:
                    print('[DEBUG] Formset errors:')
                    print('  Non-form errors:', formset.non_form_errors())
                    
                    # Check if errors are only from optional choices (index 2, 3, 4 = C, D, E)
                    critical_errors = False
                    for i, form in enumerate(formset.forms):
                        if form.errors:
                            print(f'  Form {i} ({chr(65+i)}) errors:', form.errors)
                            # Only consider errors from A & B (index 0, 1) as critical
                            if i <= 1:
                                critical_errors = True
                                print(f'    -> CRITICAL ERROR in required choice {chr(65+i)}')
                        # Also show cleaned_data for debugging
                        if hasattr(form, 'cleaned_data'):
                            print(f'  Form {i} ({chr(65+i)}) cleaned_data:', form.cleaned_data)
                    
                    # Check for critical non-form errors
                    if formset.non_form_errors():
                        non_form_errors = formset.non_form_errors()
                        print('[DEBUG] Non-form errors detected:', non_form_errors)
                        # Check if non-form errors are about required choices only
                        error_text = str(non_form_errors).lower()
                        if 'choice a' in error_text or 'choice b' in error_text:
                            critical_errors = True
                            print('[DEBUG] Critical non-form errors detected')
                    
                    if not critical_errors:
                        can_proceed = True
                        print('[DEBUG] Only optional choice errors - proceeding anyway')
                    else:
                        print('[DEBUG] Critical errors found - cannot proceed')
                
                if can_proceed:
                    print('[DEBUG] Formset is valid, proceeding with choice saving...')
                    
                    # ENHANCED DEBUG: Check both raw POST data and formset cleaned_data
                    print('\n[DEBUG] Raw POST checkbox data:')
                    for key, value in request.POST.items():
                        if 'is_correct' in key:
                            print(f'  POST[{key}] = {value}')
                    
                    print('\n[DEBUG] Formset cleaned_data:')
                    for i, form in enumerate(formset):
                        if form.cleaned_data:
                            choice_letter = chr(65 + i)  # A, B, C, D, E
                            print(f'  Choice {choice_letter}: {form.cleaned_data}')
                    
                    # Check if at least one choice is marked as correct
                    correct_choices = 0
                    
                    # ALTERNATIVE APPROACH: Check raw POST data directly for checkbox validation
                    print('\n[DEBUG] Checking POST data for correct answers:')
                    for i in range(5):
                        checkbox_name = f'choices-{i}-is_correct'
                        checkbox_value = request.POST.get(checkbox_name, None)
                        choice_letter = chr(65 + i)  # A, B, C, D, E
                        
                        print(f'  Choice {choice_letter}: POST[{checkbox_name}] = {checkbox_value}')
                        
                        if checkbox_value == 'on' or checkbox_value == 'true' or checkbox_value is True:
                            correct_choices += 1
                            print(f'  -> Choice {choice_letter} counted as CORRECT')
                    
                    # Also check formset cleaned_data as backup
                    for i, form in enumerate(formset):
                        if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                            is_correct = form.cleaned_data.get('is_correct', False)
                            choice_letter = chr(65 + i)  # A, B, C, D, E
                            print(f'[DEBUG] Formset Choice {choice_letter}: is_correct = {is_correct} (type: {type(is_correct)})')
                            
                            # Only count if not already counted from POST data
                            checkbox_name = f'choices-{i}-is_correct'
                            if request.POST.get(checkbox_name) is None:
                                if is_correct is True or is_correct == 'on' or is_correct == 'true':
                                    correct_choices += 1
                                    print(f'[DEBUG] Choice {choice_letter} counted from formset as CORRECT')
                    
                    print(f'[DEBUG] Total correct choices found: {correct_choices}')
                    
                    if correct_choices == 0:
                        messages.error(request, 'Minimal satu pilihan harus ditandai sebagai jawaban yang benar.')
                        return render(request, 'admin/manage_questions/question_form.html', {
                            'form': form,
                            'formset': formset,
                            'title': 'Add New Question',
                            'page_title': 'Create New Question',
                            'page_subtitle': 'Fill in the details to create a new question',
                            'category': question.category if hasattr(question, 'category') else None
                        })
                
                    question.save()
                    
                    # Save choices using formset but handle image URLs manually
                    choices = formset.save(commit=False)
                    print(f'[DEBUG] formset.save(commit=False) returned {len(choices)} choices')
                    
                    # CRITICAL FIX: Force save ALL choices (A through E) even if some are empty
                    # The issue is that Django formset only includes forms with data in save(commit=False)
                    # We need to manually process all 5 choice forms
                    
                    # First, delete any existing choices for this question (in case of update)
                    if hasattr(question, 'id') and question.id:
                        from .models import Choice
                        Choice.objects.filter(question=question).delete()
                        print('[DEBUG] Deleted existing choices for question')
                    
                    saved_choice_count = 0
                    for i in range(5):  # Always process choices 0-4 (A-E)
                        choice_letter = chr(65 + i)  # A, B, C, D, E
                        
                        # Get data from POST directly
                        choice_text = request.POST.get(f'choices-{i}-choice_text', '').strip()
                        is_correct_raw = request.POST.get(f'choices-{i}-is_correct', '')
                        is_correct = is_correct_raw in ['on', 'true', True]
                        
                        print(f'[DEBUG] Processing Choice {choice_letter}: text="{choice_text[:30]}..." is_correct={is_correct}')
                        
                        # ALWAYS create choice object, even if empty (to maintain A-E structure)
                        from .models import Choice
                        choice_obj = Choice()
                        choice_obj.question = question
                        choice_obj.choice_text = choice_text
                        choice_obj.is_correct = is_correct
                        
                        # Handle choice image
                        choice_image_url = request.POST.get(f'choice_image_{i+1}')
                        if choice_image_url and choice_image_url.strip():
                            import urllib.parse
                            from django.core.files.storage import default_storage
                            
                            parsed_url = urllib.parse.urlparse(choice_image_url)
                            if parsed_url.path.startswith('/media/'):
                                file_path = parsed_url.path[7:]
                                if default_storage.exists(file_path):
                                    choice_obj.choice_image = file_path
                        
                        choice_obj.save()
                        saved_choice_count += 1
                        print(f'[DEBUG] SAVED Choice {choice_letter}: text="{choice_text[:30] if choice_text else ""}..." is_correct={is_correct}')
                    
                    print(f'[DEBUG] Total choices saved: {saved_choice_count}')
                    
                    # No need for save_m2m since we're handling choices manually
                    
                    messages.success(request, 'Soal pilihan ganda berhasil dibuat!')
                    
                    # Redirect to category-specific question list if came from there
                    if question.category:
                        return redirect('question_list_by_category', category_id=question.category.id)
                    return redirect('question_list')
                
                else:
                    # DEBUG: formset invalid - dump errors and posted hidden image urls
                    try:
                        print('\n[DEBUG] Choice formset is invalid')
                        print('formset.non_form_errors():', formset.non_form_errors())
                        for idx, f in enumerate(formset.forms, start=1):
                            try:
                                print(f"-- form {idx} prefix={f.prefix} errors=", f.errors.as_json())
                            except Exception:
                                print(f"-- form {idx} prefix={f.prefix} errors=", f.errors)
                        # Also show any hidden image POST fields that JS should set
                        for i in range(1, 10):
                            key = f'choice_image_{i}'
                            if key in request.POST:
                                print(f"POST[{key}] =", request.POST.get(key))
                    except Exception as e:
                        print('[DEBUG] error while printing formset debug:', e)

                    messages.error(request, 'Please correct the errors below.')
        else:
            # DEBUG: form invalid - print errors
            try:
                print('\n[DEBUG] Question form is invalid:')
                print(form.errors.as_json())
            except Exception:
                print('\n[DEBUG] Question form is invalid (non-json):', form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionForm()
        formset = ChoiceFormSet()
        
        # Set initial category if provided
        if initial_category:
            form.fields['category'].initial = initial_category
    
    return render(request, 'admin/manage_questions/question_form.html', {
        'form': form,
        'formset': formset,
        'title': 'Add New Question',
        'page_title': 'Create New Question',
        'page_subtitle': 'Fill in the details to create a new question',
        'category': initial_category
    })

@login_required
@admin_or_teacher_or_operator_required
def question_update(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    
    if request.method == 'POST':
        form = QuestionUpdateForm(request.POST, instance=question)
        ChoiceFormSet = inlineformset_factory(
            Question, Choice,
            fields=('choice_text', 'choice_image', 'is_correct'),
            extra=0, can_delete=True,
            min_num=2, validate_min=True
        )
        formset = ChoiceFormSet(request.POST, instance=question, prefix='choices')
        
        if form.is_valid():
            updated_question = form.save(commit=False)
            
            # For essay questions, choices are not required
            if updated_question.question_type == 'essay':
                # Delete existing choices when converting to essay
                question.choices.all().delete()
                updated_question.save()
                messages.success(request, 'Soal isian berhasil diperbarui!')
                
                # Redirect to category-specific question list if available
                if updated_question.category:
                    return redirect('question_list_by_category', category_id=updated_question.category.id)
                return redirect('question_list')
            
            # For multiple choice questions, validate and save choices
            elif updated_question.question_type == 'multiple_choice' and formset.is_valid():
                # Check if at least one choice is marked as correct
                forms_data = [form.cleaned_data for form in formset if form.cleaned_data and not form.cleaned_data.get('DELETE', False)]
                correct_choices = sum(1 for data in forms_data if data.get('is_correct', False))
                
                if correct_choices == 0:
                    messages.error(request, 'Minimal satu pilihan harus ditandai sebagai jawaban yang benar.')
                    return render(request, 'admin/manage_questions/question_form.html', {
                        'form': form,
                        'formset': formset,
                        'question': question,
                        'title': 'Update Question',
                        'page_title': 'Edit Question',
                        'page_subtitle': 'Update the details of this question',
                        'category': question.category
                    })
                
                with transaction.atomic():
                    updated_question.save()
                    choices = formset.save(commit=False)
                    
                    # Process choice images from uploaded URLs
                    for i, choice in enumerate(choices, 1):
                        # Check if there's an uploaded image URL for this choice
                        choice_image_url = request.POST.get(f'choice_image_{i}')
                        if choice_image_url:
                            # Extract filename from URL and create ImageField
                            import urllib.parse
                            from django.core.files.base import ContentFile
                            from django.core.files.storage import default_storage
                            
                            # Parse the URL to get the file path
                            parsed_url = urllib.parse.urlparse(choice_image_url)
                            if parsed_url.path.startswith('/media/'):
                                file_path = parsed_url.path[7:]  # Remove '/media/' prefix
                                
                                # Check if file exists in media storage
                                if default_storage.exists(file_path):
                                    choice.choice_image = file_path
                        
                        choice.save()
                    
                    # Save any remaining formset instances
                    formset.save_m2m()
                    messages.success(request, 'Soal pilihan ganda berhasil diperbarui!')
                    
                    # Redirect to category-specific question list if available
                    if updated_question.category:
                        return redirect('question_list_by_category', category_id=updated_question.category.id)
                    return redirect('question_list')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = QuestionUpdateForm(instance=question)
        ChoiceFormSet = inlineformset_factory(
            Question, Choice,
            fields=('choice_text', 'choice_image', 'is_correct'),
            extra=0, can_delete=True,
            min_num=2, validate_min=True
        )
        formset = ChoiceFormSet(instance=question, prefix='choices')

    return render(request, 'admin/manage_questions/question_form.html', {
        'form': form,
        'formset': formset,
        'question': question,
        'title': 'Update Question',
        'page_title': 'Edit Question',
        'page_subtitle': 'Update the details of this question',
        'category': question.category
    })

@login_required
@admin_or_teacher_or_operator_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    category_id = question.category.id  # Store category ID before deletion
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('question_list_by_category', category_id=category_id)
    
    return render(request, 'admin/manage_questions/question_confirm_delete.html', {
        'question': question
    })

@login_required
@admin_required
def update_utbk_coefficients(request, category_id):
    """Update UTBK difficulty coefficients for a category"""
    category = get_object_or_404(Category, id=category_id)
    
    if category.scoring_method != 'utbk':
        messages.error(request, f'Category "{category.category_name}" is not using UTBK scoring method.')
        return redirect('question_list_by_category', category_id=category_id)
    
    try:
        # Update coefficients
        Test.update_utbk_difficulty_coefficients(category_id)
        
        # Count questions updated
        question_count = category.question_set.count()
        
        if question_count > 0:
            messages.success(
                request, 
                f'Successfully updated UTBK difficulty coefficients for {question_count} questions in "{category.category_name}".'
            )
        else:
            messages.warning(
                request, 
                f'No questions found in "{category.category_name}" to update coefficients.'
            )
            
    except Exception as e:
        messages.error(request, f'Error updating UTBK coefficients: {str(e)}')
    
    return redirect('question_list_by_category', category_id=category_id)



##STUDENTS##

@login_required
@active_subscription_required
def tryout_list(request):
    # Check if there's an ongoing test - pick the most recent valid unsubmitted test
    ongoing_test = None
    ongoing_tests_qs = Test.objects.filter(student=request.user, is_submitted=False).order_by('-start_time')
    for t in ongoing_tests_qs:
        # Ignore tests that have no start_time (not actually started)
        if not t.start_time:
            continue

        # If time is up, finalize it and continue to next candidate
        if t.is_time_up():
            t.is_submitted = True
            t.end_time = timezone.now()
            try:
                t.calculate_score()
            except Exception:
                pass
            t.save()
            continue

        # Found a valid ongoing test
        ongoing_test = t
        break

    if ongoing_test:
        # Redirect to ongoing test based on type
        if ongoing_test.tryout_package:
            # This is a package test
            current_question_index = ongoing_test.get_current_question_index()
            return redirect('take_package_test_question', 
                          package_id=ongoing_test.tryout_package.id, 
                          question=current_question_index)
        else:
            # This is a category test
            category = ongoing_test.categories.first()
            if category:
                # Get current question index from session or start from 0
                session_key = f'test_session_{category.id}_{request.user.id}'
                current_question_index = 0

                if session_key in request.session:
                    # Get last answered question index
                    answered_questions = request.session[session_key].get('answered_questions', {})
                    if answered_questions:
                        # Find the next unanswered question
                        questions = Question.objects.filter(category=category)
                        for i, question in enumerate(questions):
                            if question.id not in answered_questions:
                                current_question_index = i
                                break
                        else:
                            # All questions answered, go to last question
                            current_question_index = len(questions) - 1 if questions else 0

                return redirect('take_test', category_id=category.id, question=current_question_index)
    
    # Clean up any unsubmitted test sessions for this user
    # This prevents issues when student starts a new test
    session_keys_to_remove = []
    for key in request.session.keys():
        if key.startswith(f'test_session_') and key.endswith(f'_{request.user.id}'):
            # Check if there's an associated unsubmitted test
            session_data = request.session[key]
            if 'test_id' in session_data:
                try:
                    test = Test.objects.get(id=session_data['test_id'])
                    # If test is submitted or time is up, remove session
                    if test.is_submitted or test.is_time_up():
                        session_keys_to_remove.append(key)
                except Test.DoesNotExist:
                    # Test doesn't exist, remove session
                    session_keys_to_remove.append(key)
    
    # Remove invalid sessions
    for key in session_keys_to_remove:
        if key in request.session:
            del request.session[key]

    # Get search and sort parameters and then categories and packages
    search_query = request.GET.get('q', '').strip()
    sort_option = request.GET.get('sort', '').strip()
    categories = Category.objects.all()
    packages = TryoutPackage.objects.filter(is_active=True)
    # Apply search filter if provided
    if search_query:
        categories = categories.filter(category_name__icontains=search_query)
        packages = packages.filter(package_name__icontains=search_query)
    # Apply sort option
    if sort_option == 'newest':
        packages = packages.order_by('-created_at')
    elif sort_option == 'alphabet':
        packages = packages.order_by('package_name')
        categories = categories.order_by('category_name')
    elif sort_option == 'method':
        categories = categories.order_by('scoring_method')
    
    # Add personal best scores for categories
    if request.user.is_authenticated:
        for category in categories:
            user_best = Test.objects.filter(
                student=request.user,
                categories=category,
                is_submitted=True
            ).aggregate(best_score=Max('score'))['best_score']
            category.user_best_score = user_best
    
    context = {
        'categories': categories,
        'packages': packages,
        'search_query': search_query,
        'sort_option': sort_option,
    }
    
    return render(request, 'students/tryouts/tryout_list.html', context)

@login_required
@active_subscription_required
def take_test(request, category_id, question):
    from django.utils import timezone
    from datetime import timedelta

    # DEBUG: trace invocation parameters to diagnose off-by-one skip
    category = get_object_or_404(Category, id=category_id)
    questions_qs = Question.objects.filter(category=category).order_by('id')

    # normalize current question index
    # Accept both 0-based and 1-based incoming values: treat any positive integer as 1-based
    try:
        raw_q = int(question)
    except (TypeError, ValueError):
        raw_q = 0

    if raw_q > 0:
        # incoming is 1-based (template start buttons use 1 for first question)
        current_question_index = raw_q - 1
    else:
        # incoming is 0-based or invalid
        current_question_index = max(0, raw_q)

    # session key and existing test handling (reuse existing logic but create mapping for package-like template)
    session_key = f'test_session_{category_id}_{request.user.id}'
    existing_test = Test.objects.filter(
        student=request.user,
        is_submitted=False,
        categories=category
    ).first()

    # Allow caller to force creating a new test even if a recent submitted test exists
    force_new = request.GET.get('force_new') == '1'
    # Don't force new test for AJAX requests - they should use existing session test
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
        force_new = False

    if (session_key not in request.session or existing_test is None) or force_new:
        # If the user has JUST submitted a test for this category (e.g. clicked back after finishing),
        # avoid creating a new test immediately. Redirect to the latest submitted test results instead.
        # Only do this redirect when user did NOT explicitly request a new test.
        if not force_new:
            try:
                recent_threshold = timezone.now() - timedelta(minutes=5)
                recent_test = Test.objects.filter(
                    student=request.user,
                    categories=category,
                    is_submitted=True,
                    end_time__gte=recent_threshold
                ).order_by('-end_time').first()
                if recent_test:
                    return redirect('test_results', test_id=recent_test.id)
            except Exception:
                # Fall back to normal behavior on any unexpected issue
                pass

        if session_key in request.session:
            del request.session[session_key]

        test = Test.objects.create(
            student=request.user,
            start_time=timezone.now(),
            time_limit=category.time_limit
        )
        test.categories.add(category)

        request.session[session_key] = {
            'test_id': test.id,
            'answered_questions': {},
            'category_id': category_id
        }
    else:
        test_session = request.session[session_key]
        test = get_object_or_404(Test, id=test_session['test_id'])
        if not test.categories.filter(id=category_id).exists():
            test.categories.add(category)
        if not test.start_time:
            test.start_time = timezone.now()
            test.time_limit = category.time_limit
            test.save()

    test_session = request.session[session_key]

    # If time is up or submitted, finalize and redirect
    if test.is_time_up() or test.is_submitted:
        if not test.is_submitted:
            test.is_submitted = True
            test.end_time = timezone.now()
            test.calculate_score()
            test.save()
        if session_key in request.session:
            del request.session[session_key]
        return redirect('test_results', test_id=test.id)

    # Build ordered question list for this category (used to compute question numbers)
    all_questions = list(questions_qs)
    total_questions = len(all_questions)

    # Guard index
    if current_question_index < 0:
        current_question_index = 0
    if current_question_index >= total_questions:
        current_question_index = max(0, total_questions - 1)

    current_question = all_questions[current_question_index] if total_questions > 0 else None
    choices = current_question.choices.all() if current_question else []

    # Load existing answers and map to question numbers
    existing_answers = Answer.objects.filter(test=test).select_related('question', 'selected_choice')
    answered_question_ids = set(existing_answers.values_list('question_id', flat=True))
    answered_question_numbers = [i + 1 for i, q in enumerate(all_questions) if q.id in answered_question_ids]

    # Handle POST (accept both 'choice' and 'answer' names to be compatible)
    if request.method == 'POST':
        choice_id = request.POST.get('choice') or request.POST.get('answer')
        text_answer = request.POST.get('text_answer')
        action = request.POST.get('action')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Handle multiple choice answers
        if choice_id and current_question.is_multiple_choice():
            choice = get_object_or_404(Choice, id=choice_id, question=current_question)
            
            # Use update_or_create to handle race conditions more reliably
            try:
                answer, created = Answer.objects.update_or_create(
                    test=test, 
                    question=current_question,
                    defaults={
                        'selected_choice': choice,
                        'text_answer': None
                    }
                )
                    
                # Clean up any duplicate answers that might still exist
                duplicate_answers = Answer.objects.filter(test=test, question=current_question).exclude(id=answer.id)
                if duplicate_answers.exists():
                    duplicate_answers.delete()
                    
            except Exception as e:
                # Fall back to simple creation if there's an issue
                Answer.objects.filter(test=test, question=current_question).delete()
                answer = Answer.objects.create(test=test, question=current_question, selected_choice=choice)

            # Update session store
            test_session = request.session.get(session_key, {'answered_questions': {}})
            test_session['answered_questions'][current_question.id] = int(choice_id)
            request.session[session_key] = test_session

            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer saved'})

        # Handle essay answers
        elif text_answer is not None and current_question.is_essay():
            existing_answers_qs = Answer.objects.filter(test=test, question=current_question)
            if existing_answers_qs.count() > 1:
                first_answer = existing_answers_qs.first()
                existing_answers_qs.exclude(id=first_answer.id).delete()
                first_answer.text_answer = text_answer
                first_answer.selected_choice = None  # Clear choice
                first_answer.save()
            elif existing_answers_qs.count() == 1:
                ans = existing_answers_qs.first()
                ans.text_answer = text_answer
                ans.selected_choice = None  # Clear choice
                ans.save()
            else:
                Answer.objects.create(test=test, question=current_question, text_answer=text_answer)

            # Update session store
            test_session = request.session.get(session_key, {'answered_questions': {}})
            test_session['answered_questions'][current_question.id] = 'text_answered' if text_answer.strip() else None
            request.session[session_key] = test_session

            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer saved'})

        # Only remove answer if explicitly requested or if no valid answer data was provided
        elif action == 'clear' or (choice_id is None and text_answer is None and action != 'submit'):
            # remove existing answer
            existing_ans = Answer.objects.filter(test=test, question=current_question).first()
            if existing_ans:
                existing_ans.delete()
            if current_question and current_question.id in test_session.get('answered_questions', {}):
                del test_session['answered_questions'][current_question.id]
                request.session[session_key] = test_session
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer removed'})

        # If AJAX request without valid data, just return success to avoid errors
        elif is_ajax:
            return JsonResponse({'status': 'success', 'message': 'No action taken'})

        # Non-AJAX navigation handling
        if not is_ajax:
            # Note: current_question_index is 0-based internally. The `take_test` view
            # accepts either 0-based (<=0) or 1-based (>0) incoming question params.
            # To avoid off-by-one redirects, send 1-based question numbers for outgoing redirects.
            if action == 'next' and current_question_index + 1 < total_questions:
                # Next question (1-based): current 0-based + 2
                return redirect('take_test', category_id=category_id, question=current_question_index + 2)
            elif action == 'previous' and current_question_index > 0:
                # Previous question (1-based): current 0-based (already equals previous 1-based)
                return redirect('take_test', category_id=category_id, question=current_question_index)
            elif action == 'submit':
                if not test.is_submitted:
                    test.is_submitted = True
                    test.end_time = timezone.now()
                    test.calculate_score()
                    test.save()
                    if session_key in request.session:
                        del request.session[session_key]
                return redirect('test_results', test_id=test.id)

    # Update model current question (1-based)
    test.current_question = current_question_index + 1
    test.save(update_fields=['current_question'])

    # Progress stats
    answered_count = Answer.objects.filter(test=test).count()
    unanswered_count = max(0, total_questions - answered_count)
    progress = round((answered_count / total_questions) * 100, 1) if total_questions else 0

    # Compute time remaining as timedelta for template compatibility
    time_remaining = None
    if test.start_time and test.time_limit:
        elapsed = timezone.now() - test.start_time
        total_td = timedelta(minutes=test.time_limit)
        remaining_td = total_td - elapsed
        if remaining_td.total_seconds() <= 0:
            remaining_td = timedelta(0)
        time_remaining = remaining_td

    # Get previous answer for this question
    previous_answer = Answer.objects.filter(test=test, question=current_question).first()
    
    context = {
        'is_package': False,
        'category': category,
        'package': None,
        'test': test,
        'question': current_question,
        'choices': choices,
        'current_question_number': current_question_index + 1,
        'total_questions': total_questions,
        'previous_answer': previous_answer,
        'previous_text_answer': previous_answer.text_answer if previous_answer and previous_answer.text_answer else '',
        'progress': progress,
        'answered_questions': answered_count,
        'unanswered_questions': unanswered_count,
        'answered_question_numbers': answered_question_numbers,
        'time_remaining': time_remaining,
        'can_go_previous': current_question_index > 0,
        'can_go_next': current_question_index + 1 < total_questions,
        'is_last_question': current_question_index + 1 == total_questions,
        'remaining_time': test.get_remaining_time() if test.start_time else 0,
    }

    return render(request, 'students/tryouts/package_test_question.html', context)

@login_required
@active_subscription_required
def submit_test(request, test_id):
    """Submit test manually"""
    from django.utils import timezone
    
    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id, student=request.user)
        
        print(f"[DEBUG submit_test] Test {test_id}: Before submission - Answers count: {test.answers.count()}")
        
        if not test.is_submitted:
            test.is_submitted = True
            test.end_time = timezone.now()
            test.save()  # Save is_submitted and end_time first
            
            print(f"[DEBUG submit_test] Test {test_id}: After marking submitted - Answers count: {test.answers.count()}")
            
            test.calculate_score()  # This will call save() again with the score
            
            print(f"[DEBUG submit_test] Test {test_id}: After calculate_score - Answers count: {test.answers.count()}, Score: {test.score}")
            
            # Clear session - Use correct category_id from test
            test_category = test.categories.first()
            if test_category:
                session_key = f'test_session_{test_category.id}_{request.user.id}'
                if session_key in request.session:
                    del request.session[session_key]
            # Also mark any other unsubmitted tests for this student+category as submitted to avoid duplicates
            try:
                other_tests = Test.objects.filter(student=request.user, is_submitted=False, categories__in=test.categories.all()).exclude(id=test.id)
                for ot in other_tests:
                    ot.is_submitted = True
                    ot.end_time = timezone.now()
                    try:
                        ot.calculate_score()
                    except Exception:
                        pass
                    ot.save()
                    # Remove any session keys referencing those tests
                    for cat in ot.categories.all():
                        sk = f'test_session_{cat.id}_{request.user.id}'
                        if sk in request.session:
                            del request.session[sk]
            except Exception:
                # swallow any unexpected errors here to avoid blocking user flow
                pass
        
        return redirect('test_results', test_id=test.id)
    
    return redirect('home')

@login_required
@active_subscription_required
def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    
    # Get category from test.categories (many-to-many relationship)
    category = test.categories.first()
    package = test.tryout_package if hasattr(test, 'tryout_package') and test.tryout_package else None

    # If no category found from test.categories, try to get from first answer (fallback)
    if not category:
        first_answer = test.answers.first()
        category = first_answer.question.category if first_answer else None

    # Calculate score if not already calculated
    if test.answers.exists():
        test.calculate_score()
        # Refresh test object from database to get updated score
        test.refresh_from_db()

    # Get university recommendations for UTBK tests
    university_recommendations = []
    score_analysis = None

    # Cek scoring_method dari kategori pertama saja (paket UTBK tetap utbk)
    scoring_method = category.scoring_method if category else None
    show_university_section = False
    if scoring_method == 'utbk':
        show_university_section = True
        university_recommendations = test.get_university_recommendations()
        score_analysis = test.get_score_analysis()
        # Calculate achievement percentages for each recommendation
        for rec in university_recommendations:
            min_score = rec['university'].minimum_utbk_score
            achievement_percentage = (test.score / min_score) * 100 if min_score > 0 else 0
            rec['achievement_percentage'] = round(achievement_percentage, 1)
            rec['meets_minimum'] = test.score >= min_score
            rec['score_gap'] = max(0, min_score - test.score)  # Selisih nilai yang dibutuhkan

    # Determine target achievement status
    met_target_type = None
    target_achievement_status = None  # 'all_met', 'some_met', 'none_met'
    
    if show_university_section and university_recommendations:
        # Only check user targets (not 'suggested')
        total_targets = 0
        met_targets = 0
        
        for rec in university_recommendations:
            if rec.get('target_type') != 'suggested':
                total_targets += 1
                if rec.get('meets_minimum'):
                    met_targets += 1
                    if not met_target_type:  # Set first met target type
                        met_target_type = rec.get('target_type')
        
        # Determine status based on how many targets are met
        if total_targets > 0:
            if met_targets == total_targets:
                target_achievement_status = 'all_met'
            elif met_targets > 0:
                target_achievement_status = 'some_met'
            else:
                target_achievement_status = 'none_met'

    context = {
        'test': test,
        'category': category,
        'package': package,
        'university_recommendations': university_recommendations,
        'score_analysis': score_analysis,
        'show_university_section': show_university_section,
        'met_target_type': met_target_type,
        'target_achievement_status': target_achievement_status,
    }

    return render(request, 'students/tryouts/test_results.html', context)

@login_required
def test_results_detail(request, test_id):
    """Detailed test results showing each question, correct/incorrect answers, and scoring explanation

    Note: we intentionally do not apply `active_subscription_required` here because teachers
    and admins should be able to review student submissions even if they don't have a
    student subscription. We enforce subscription checks only for students/visitors.
    """
    # If the requester is a student or visitor, enforce subscription rules (same as decorator)
    if request.user.is_authenticated and (request.user.is_student() or request.user.is_visitor()):
        if not request.user.can_access_tryouts():
            subscription_status = request.user.get_subscription_status()
            if request.user.is_visitor():
                from django.contrib import messages
                messages.warning(request, 'Silakan berlangganan terlebih dahulu untuk mengakses fitur tryout.')
                from django.shortcuts import redirect
                return redirect('subscription_packages')
            elif request.user.is_student() and not request.user.has_active_subscription():
                from django.contrib import messages
                from django.shortcuts import redirect
                if subscription_status['status'] == 'deactivated':
                    messages.warning(request, 'Langganan Anda telah dinonaktifkan oleh admin. Silakan hubungi admin atau berlangganan kembali.')
                elif subscription_status['status'] == 'expired':
                    messages.warning(request, 'Langganan Anda telah berakhir. Silakan perpanjang untuk melanjutkan.')
                else:
                    messages.warning(request, 'Langganan Anda tidak aktif. Silakan berlangganan untuk melanjutkan.')
                return redirect('subscription_packages')
            else:
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, 'Akses ditolak.')
                return redirect('home')
    # Load the test first (do not restrict by student here so teachers/admins can view)
    test = get_object_or_404(Test, id=test_id)
    
    # Get category from test.categories
    category = test.categories.first()
    if not category:
        first_answer = test.answers.first()
        category = first_answer.question.category if first_answer else None
    
    # Permission check: allow the student themself, admins, or the teacher who created the category(ies)
    # If none match, deny access
    try:
        is_owner_teacher = False
        for c in test.categories.all():
            if c.created_by and c.created_by == request.user:
                is_owner_teacher = True
                break
            if c.teachers.filter(pk=request.user.pk).exists():
                is_owner_teacher = True
                break
    except Exception:
        is_owner_teacher = False

    if not (request.user == test.student or request.user.is_superuser or request.user.is_admin() or is_owner_teacher):
        raise PermissionDenied

    # Calculate score if not already calculated
    if test.answers.exists():
        test.calculate_score()
        # Refresh test object from database to get updated score
        test.refresh_from_db()
    
    # Build full question list for this test (include unanswered questions)
    question_list = []
    # Determine source of questions: package or categories
    if test.tryout_package:
        package = test.tryout_package
        all_questions = []
        for pc in package.tryoutpackagecategory_set.all().order_by('order'):
            qs = list(Question.objects.filter(category=pc.category).order_by('id'))
            all_questions.extend(qs)
    else:
        # Collect questions from all categories linked to the test
        all_questions = []
        for cat in test.categories.all():
            qs = list(Question.objects.filter(category=cat).order_by('id'))
            all_questions.extend(qs)

    # Prepare per-category aggregation
    stats_by_category = {}

    correct_count = 0
    total_questions = len(all_questions)

    # Iterate full question list and include answers if present

    for q in all_questions:
        ans = test.answers.filter(question=q).first()
        
        # Handle different question types
        if q.is_multiple_choice():
            selected_choice = ans.selected_choice if ans else None
            correct_choice = q.choices.filter(is_correct=True).first()
            is_correct = (selected_choice and selected_choice.is_correct) if selected_choice else False
            
            # Build labeled choices (A, B, C...)
            all_choices = []
            choices_qs = list(q.choices.all().order_by('id'))
            for idx, ch in enumerate(choices_qs):
                label = chr(65 + idx)  # A, B, C, ...
                all_choices.append({'label': label, 'id': ch.id, 'text': ch.choice_text, 'is_correct': ch.is_correct})

            # Determine labels for selected and correct choices
            your_answer_label = None
            correct_answer_label = None
            if selected_choice:
                for c in all_choices:
                    if c['id'] == selected_choice.id:
                        your_answer_label = c['label']
                        break
            if correct_choice:
                for c in all_choices:
                    if c['id'] == correct_choice.id:
                        correct_answer_label = c['label']
                        break
            
            your_answer_text = selected_choice.choice_text if selected_choice else None
            correct_answer_text = correct_choice.choice_text if correct_choice else None
            
        elif q.is_essay():
            # Essay question handling
            all_choices = []
            selected_choice = None
            correct_choice = None
            your_answer_label = None
            correct_answer_label = None
            
            your_answer_text = ans.text_answer if ans and ans.text_answer else None
            correct_answer_text = q.correct_answer_text
            is_correct = ans.is_correct() if ans else False
        
        else:
            # Fallback for unknown question types
            all_choices = []
            selected_choice = None
            correct_choice = None
            your_answer_label = None
            correct_answer_label = None
            your_answer_text = None
            correct_answer_text = None
            is_correct = False

        if is_correct:
            correct_count += 1

        # Append to question_list in the shape template expects
        question_list.append({
            'question_text': q.question_text,
            'question_type': q.question_type,
            'your_answer': your_answer_text,
            'is_correct': is_correct,
            'correct_answer': correct_answer_text,
            'question_obj': q,
            'all_choices': all_choices,
            'your_choice_label': your_answer_label,
            'correct_choice_label': correct_answer_label,
        })

        # Aggregate per-category stats
        cat_name = q.category.category_name if q.category else 'Umum'
        if cat_name not in stats_by_category:
            stats_by_category[cat_name] = {'category_name': cat_name, 'correct': 0, 'incorrect': 0, 'blank': 0, 'score': 0}

        if selected_choice is None:
            stats_by_category[cat_name]['blank'] += 1
        elif is_correct:
            stats_by_category[cat_name]['correct'] += 1
        else:
            stats_by_category[cat_name]['incorrect'] += 1

    # Convert stats_by_category to list and compute simple score per category
    stats_by_category_list = []
    for cat_stat in stats_by_category.values():
        total_cat = cat_stat['correct'] + cat_stat['incorrect'] + cat_stat['blank']
        # simple percent score: correct / total * 100
        cat_stat['score'] = round((cat_stat['correct'] / total_cat * 100) if total_cat > 0 else 0, 1)
        stats_by_category_list.append(cat_stat)

    incorrect_count = total_questions - correct_count
    accuracy_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0

    # Expose summary fields on the test object so the template (which references test.total_questions etc.) works
    try:
        test.total_questions = total_questions
        test.correct = correct_count
        test.incorrect_or_blank = incorrect_count
    except Exception:
        pass

    # Compute human-readable duration if possible
    try:
        if getattr(test, 'start_time', None) and getattr(test, 'end_time', None):
            delta = test.end_time - test.start_time
            minutes, seconds = divmod(int(delta.total_seconds()), 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                test.duration = f"{hours}h {minutes}m"
            else:
                test.duration = f"{minutes}m {seconds}s"
        else:
            test.duration = None
    except Exception:
        test.duration = None

    context = {
        'test': test,
        'category': category,
        'questions': question_list,
        'stats_by_category': stats_by_category_list,
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'accuracy_percentage': accuracy_percentage,
    }
    
    return render(request, 'students/tryouts/test_results_detail.html', context)

def get_scoring_explanation(category):
    """Get explanation for the scoring method used"""
    if not category:
        return "Tidak ada informasi sistem penilaian."
    
    if category.scoring_method == 'default':
        return f"Sistem Penilaian Default: Setiap soal memiliki bobot yang sama. Total skor dihitung dengan membagi 100 poin secara merata untuk semua soal. Jawaban benar = poin penuh, jawaban salah = 0 poin."
    
    elif category.scoring_method == 'custom':
        return f"Sistem Penilaian Custom: Setiap soal memiliki bobot berbeda sesuai tingkat kesulitan atau kepentingan. Total bobot semua soal = 100 poin. Skor akhir adalah jumlah bobot dari soal-soal yang dijawab benar."
    
    elif category.scoring_method == 'utbk':
        return f"Sistem Penilaian UTBK: Menggunakan metode penilaian berbasis tingkat kesulitan soal. Soal yang lebih sulit memiliki bobot lebih tinggi. Koefisien kesulitan dihitung berdasarkan tingkat keberhasilan siswa lain dalam menjawab soal tersebut."
    
    return "Sistem penilaian tidak diketahui."

@login_required
@active_subscription_required
def test_history(request):
    """Show all completed tests for the student with filtering and pagination"""
    # Get all tests for the current student
    # Only show tryout/UTBK tests in test history
    tests = Test.objects.filter(
        student=request.user,
        is_submitted=True
    ).select_related().prefetch_related('categories').order_by('-date_taken')
    
    # Get filter parameters
    category_filter = request.GET.get('category', '').strip()
    search = request.GET.get('search', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Apply filters
    if category_filter and category_filter.isdigit():
        tests = tests.filter(categories__id=int(category_filter)).distinct()
    
    if search:
        # Search in both category name and tryout package name
        tests = tests.filter(
            Q(categories__category_name__icontains=search) |
            Q(tryout_package__package_name__icontains=search)
        ).distinct()
    
    if date_from:
        try:
            tests = tests.filter(date_taken__date__gte=date_from)
        except (ValueError, TypeError):
            pass  # Invalid date format, skip filter
    
    if date_to:
        try:
            tests = tests.filter(date_taken__date__lte=date_to)
        except (ValueError, TypeError):
            pass  # Invalid date format, skip filter
    
    # Calculate statistics before pagination (for the filtered results)
    total_tests = tests.count()
    if total_tests > 0:
        avg_score = tests.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        highest_score = tests.aggregate(max_score=Max('score'))['max_score'] or 0
        latest_test = tests.first()
    else:
        avg_score = 0
        highest_score = 0
        latest_test = None
    
    # Pagination
    paginator = Paginator(tests, 10)  # Show 10 tests per page
    page_number = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Get all categories for filter dropdown (only categories that have tests)
    categories = Category.objects.filter(
        id__in=Test.objects.filter(
            student=request.user,
            is_submitted=True,
            tryout_package__isnull=False
        ).values_list('categories__id', flat=True)
    ).distinct().order_by('category_name')
    
    # Get selected category name for display
    selected_category_name = None
    if category_filter and category_filter.isdigit():
        try:
            selected_category = Category.objects.get(id=int(category_filter))
            selected_category_name = selected_category.category_name
        except Category.DoesNotExist:
            pass
    
    # Siapkan data rekomendasi universitas dan status target untuk setiap test UTBK
    test_university_info = {}
    for test in page_obj:
        category = test.categories.first()
        if category and category.scoring_method == 'utbk':
            university_recommendations = test.get_university_recommendations() if hasattr(test, 'get_university_recommendations') else []
            # Cek status pencapaian target
            total_targets = 0
            met_targets = 0
            met_target_type = None
            for rec in university_recommendations:
                if rec.get('target_type') != 'suggested':
                    total_targets += 1
                    if rec.get('meets_minimum'):
                        met_targets += 1
                        if not met_target_type:
                            met_target_type = rec.get('target_type')
            if total_targets > 0:
                if met_targets == total_targets:
                    target_achievement_status = 'all_met'
                elif met_targets > 0:
                    target_achievement_status = 'some_met'
                else:
                    target_achievement_status = 'none_met'
            else:
                target_achievement_status = None
            test_university_info[test.id] = {
                'recommendations': university_recommendations,
                'target_achievement_status': target_achievement_status,
                'met_target_type': met_target_type,
            }
        else:
            test_university_info[test.id] = None

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'total_tests': total_tests,
        'avg_score': avg_score,
        'highest_score': highest_score,
        'latest_test': latest_test,
        'current_category': category_filter,
        'current_category_name': selected_category_name,
        'current_search': search,
        'date_from': date_from,
        'date_to': date_to,
        'test_university_info': test_university_info,
    }
    
    return render(request, 'students/tryouts/test_history.html', context)

@login_required
@active_subscription_required
def force_end_test(request, test_id):
    """Force end ongoing test"""
    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id, student=request.user, is_submitted=False)
        
        # Submit the test
        test.is_submitted = True
        test.end_time = timezone.now()
        test.calculate_score()
        test.save()
        
        # Clear session
        test_category = test.categories.first()
        if test_category:
            session_key = f'test_session_{test_category.id}_{request.user.id}'
            if session_key in request.session:
                del request.session[session_key]
        
        messages.success(request, 'Tryout telah diakhiri secara paksa. Skor dihitung berdasarkan jawaban yang telah dikerjakan.')
        return redirect('test_results', test_id=test.id)
    
    return redirect('home')

@login_required
def settings_view(request):
    from .forms import UserProfileForm, ProfilePictureForm, CustomPasswordChangeForm
    from django.contrib.auth import update_session_auth_hash
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            form = UserProfileForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Profil berhasil diperbarui!')
                return redirect('settings')
            else:
                messages.error(request, 'Terjadi kesalahan saat memperbarui profil.')
                
        elif action == 'update_profile_picture':
            try:
                form = ProfilePictureForm(request.POST, request.FILES, instance=request.user)
                if form.is_valid():
                    # Get original file size for feedback
                    uploaded_file = request.FILES.get('profile_picture')
                    if uploaded_file:
                        original_size_kb = uploaded_file.size / 1024
                        form.save()
                        if original_size_kb > 250:
                            messages.success(
                                request, 
                                f'Foto profil berhasil diperbarui dan dikompres dari {original_size_kb:.0f}KB ke ukuran optimal!'
                            )
                        else:
                            messages.success(request, 'Foto profil berhasil diperbarui!')
                    else:
                        form.save()
                        messages.success(request, 'Foto profil berhasil diperbarui!')
                    return redirect('settings')
                else:
                    # Extract specific error messages
                    error_messages = []
                    for field, errors in form.errors.items():
                        for error in errors:
                            error_messages.append(error)
                    
                    if error_messages:
                        messages.error(request, ' '.join(error_messages))
                    else:
                        messages.error(request, 'Terjadi kesalahan saat mengupload foto profil.')
                        
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan saat memproses foto profil: {str(e)}')
                return redirect('settings')
                
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            # Validate current password
            if not request.user.check_password(current_password):
                messages.error(request, 'Password saat ini tidak valid.')
                return redirect('settings')
            
            # Validate new password match
            if new_password != confirm_password:
                messages.error(request, 'Password baru dan konfirmasi password tidak cocok.')
                return redirect('settings')
            
            # Validate password strength
            if len(new_password) < 8:
                messages.error(request, 'Password harus minimal 8 karakter.')
                return redirect('settings')
            
            # Update password
            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password berhasil diubah!')
            return redirect('settings')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'settings.html', context)


# ======================= MESSAGING SYSTEM VIEWS =======================

@login_required
def message_inbox(request):
    """View untuk melihat daftar thread pesan"""
    user = request.user
    
    # Filter thread berdasarkan role user
    if user.role and user.role.role_name == 'Student':
        # Siswa: lihat thread yang mereka buat
        threads = MessageThread.objects.filter(student=user)
    else:
        # Guru/Admin/Operator: lihat thread yang ditugaskan ke mereka atau belum ditugaskan
        threads = MessageThread.objects.filter(
            Q(teacher_or_admin=user) | Q(teacher_or_admin=None)
        )
    
    # Filter berdasarkan status dan tipe jika ada
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        threads = threads.filter(status=status_filter)
    
    if type_filter:
        threads = threads.filter(thread_type=type_filter)
    
    if search_query:
        threads = threads.filter(
            Q(title__icontains=search_query) |
            Q(messages__content__icontains=search_query)
        ).distinct()
    
    # Urutkan berdasarkan aktivitas terakhir
    threads = threads.order_by('-last_activity')
    
    # Pagination
    paginator = Paginator(threads, 10)
    page = request.GET.get('page')
    try:
        threads_page = paginator.page(page)
    except PageNotAnInteger:
        threads_page = paginator.page(1)
    except EmptyPage:
        threads_page = paginator.page(paginator.num_pages)
    
    # Add unread count for each thread
    for thread in threads_page:
        thread.unread_count = thread.get_unread_count_for_user(user)
    
    # Data untuk filter options
    context = {
        'threads': threads_page,
        'status_choices': MessageThread.STATUS_CHOICES,
        'thread_type_choices': MessageThread.THREAD_TYPES,
        'current_status': status_filter,
        'current_type': type_filter,
        'current_search': search_query,
    }
    
    return render(request, 'messages/inbox.html', context)


@login_required
def create_message_thread(request):
    """View untuk membuat thread pesan baru (khusus siswa)"""
    if not (request.user.role and request.user.role.role_name == 'Student'):
        messages.error(request, 'Hanya siswa yang dapat membuat thread pesan baru.')
        return redirect('message_inbox')
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        thread_type = request.POST.get('thread_type', 'general')
        category_id = request.POST.get('category', None)
        teacher_id = request.POST.get('teacher', None)
        priority = request.POST.get('priority', 'normal')
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment', None)
        
        # Validasi
        if not title or not content:
            messages.error(request, 'Judul dan isi pesan harus diisi.')
        else:
            try:
                with transaction.atomic():
                    # Buat thread baru
                    thread = MessageThread.objects.create(
                        title=title,
                        thread_type=thread_type,
                        student=request.user,
                        priority=priority,
                        category_id=category_id if category_id else None
                    )
                    # Assign teacher/admin if provided (optional)
                    if teacher_id:
                        try:
                            teacher_user = User.objects.get(pk=teacher_id)
                            # only assign if user has teacher role (case-insensitive)
                            if teacher_user.role and teacher_user.role.role_name.lower() == 'teacher':
                                thread.teacher_or_admin = teacher_user
                                thread.save()
                        except User.DoesNotExist:
                            pass
                    
                    # Buat pesan pertama
                    Message.objects.create(
                        thread=thread,
                        sender=request.user,
                        content=content,
                        attachment=attachment
                    )
                    
                    messages.success(request, 'Pesan berhasil dikirim!')
                    return redirect('message_thread', thread_id=thread.id)
                    
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
    
    # Data untuk form
    categories = Category.objects.all().order_by('category_name')
    # Teachers list for optional assignment (case-insensitive match on role name)
    teachers = User.objects.filter(role__role_name__iexact='teacher', is_active=True).order_by('first_name', 'last_name')
    context = {
        'categories': categories,
        'teachers': teachers,
        'thread_type_choices': MessageThread.THREAD_TYPES,
        'priority_choices': [
            ('low', 'Rendah'),
            ('normal', 'Normal'),
            ('high', 'Tinggi'),
            ('urgent', 'Mendesak')
        ]
    }
    
    return render(request, 'messages/create_thread.html', context)


@login_required
def message_thread(request, thread_id):
    """View untuk melihat detail thread dan pesan-pesannya"""
    thread = get_object_or_404(MessageThread, id=thread_id)
    
    # Cek akses user
    user = request.user
    has_access = False
    
    if user.role and user.role.role_name == 'Student':
        # Siswa hanya bisa akses thread mereka sendiri
        has_access = (thread.student == user)
    else:
        # Guru/Admin/Operator bisa akses thread yang ditugaskan atau tidak ada yang menangani
        has_access = (thread.teacher_or_admin == user or thread.teacher_or_admin is None)
    
    if not has_access:
        messages.error(request, 'Anda tidak memiliki akses ke thread ini.')
        return redirect('message_inbox')
    
    # Assign guru/admin/operator jika belum ada yang menangani
    if not thread.teacher_or_admin and user.role and user.role.role_name != 'Student':
        thread.teacher_or_admin = user
        thread.save()
    
    # Handle POST request (mengirim balasan)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment', None)
        action = request.POST.get('action', 'reply')
        
        if action == 'reply' and content:
            try:
                Message.objects.create(
                    thread=thread,
                    sender=user,
                    content=content,
                    attachment=attachment
                )
                
                # Update status thread jika perlu
                if thread.status == 'closed':
                    old = thread.status
                    thread.status = 'open'
                    # set reopened metadata
                    thread.reopened_by = user
                    thread.reopened_at = timezone.now()
                    # clear closed metadata
                    thread.closed_by = None
                    thread.closed_at = None
                    thread.save()
                    try:
                        from otosapp.models import ThreadStatusLog
                        ThreadStatusLog.objects.create(
                            thread=thread,
                            changed_by=user,
                            old_status=old,
                            new_status='open',
                            note='Thread dibuka kembali oleh balasan'
                        )
                    except Exception:
                        pass
                
                messages.success(request, 'Balasan berhasil dikirim!')
                return redirect('message_thread', thread_id=thread.id)
                
            except Exception as e:
                messages.error(request, f'Terjadi kesalahan: {str(e)}')
        
        elif action == 'update_status':
            new_status = request.POST.get('status')
            if new_status in dict(MessageThread.STATUS_CHOICES):
                old = thread.status
                thread.status = new_status
                thread.save()
                # create audit log
                try:
                    from otosapp.models import ThreadStatusLog
                    ThreadStatusLog.objects.create(
                        thread=thread,
                        changed_by=user,
                        old_status=old,
                        new_status=new_status,
                        note=f'Status diubah melalui form oleh {user.get_full_name() or user.username}'
                    )
                except Exception:
                    pass
                messages.success(request, f'Status thread diubah menjadi {dict(MessageThread.STATUS_CHOICES)[new_status]}')
                return redirect('message_thread', thread_id=thread.id)
        
        elif action == 'close_thread':
            # Close thread: allowed for the student who created it, or Admin/Operator
            allowed = False
            if user.role and user.role.role_name == 'Student' and thread.student == user:
                allowed = True
            if user.role and user.role.role_name in ['Admin', 'Operator']:
                allowed = True

            if allowed:
                # Prevent closing an already closed thread
                if thread.status == 'closed':
                    messages.info(request, 'Thread ini sudah ditutup.')
                    return redirect('message_thread', thread_id=thread.id)

                old = thread.status
                thread.status = 'closed'
                thread.closed_by = user
                thread.closed_at = timezone.now()
                # clear reopened metadata
                thread.reopened_by = None
                thread.reopened_at = None
                thread.save()
                try:
                    from otosapp.models import ThreadStatusLog
                    ThreadStatusLog.objects.create(
                        thread=thread,
                        changed_by=user,
                        old_status=old,
                        new_status='closed',
                        note='Thread ditutup'
                    )
                except Exception:
                    pass
                # add a system message noting closure
                Message.objects.create(
                    thread=thread,
                    sender=user,
                    content=f'Thread ditutup oleh {user.get_full_name() or user.username} ({user.role.role_name}).'
                )
                messages.success(request, 'Thread berhasil ditutup.')
            else:
                messages.error(request, 'Anda tidak memiliki izin untuk menutup thread ini.')
            return redirect('message_thread', thread_id=thread.id)

        elif action == 'request_close':
            # Teacher requests closing: set status to 'pending' and add a message
            if user.role and user.role.role_name == 'Teacher' and thread.teacher_or_admin == user:
                # Skip if already requested or thread is pending/closed
                if thread.close_requested_by or thread.status in ['pending', 'closed']:
                    messages.info(request, 'Permintaan penutupan sudah ada atau thread tidak dapat diminta ditutup.')
                    return redirect('message_thread', thread_id=thread.id)

                old = thread.status
                thread.status = 'pending'
                thread.close_requested_by = user
                thread.close_requested_at = timezone.now()
                thread.save()
                Message.objects.create(
                    thread=thread,
                    sender=user,
                    content='Guru meminta agar thread ini ditutup. Mohon siswa atau admin memverifikasi dan menutup thread jika sesuai.'
                )
                try:
                    from otosapp.models import ThreadStatusLog
                    ThreadStatusLog.objects.create(
                        thread=thread,
                        changed_by=user,
                        old_status=old,
                        new_status='pending',
                        note='Guru meminta penutupan thread'
                    )
                except Exception:
                    pass
                messages.success(request, 'Permintaan penutupan dikirim. Siswa atau admin akan menerima notifikasi.')
            else:
                messages.error(request, 'Hanya guru yang menangani thread ini dapat meminta penutupan.')
            return redirect('message_thread', thread_id=thread.id)
    
    # Tandai pesan sebagai sudah dibaca
    thread.mark_as_read_for_user(user)
    
    # Ambil semua pesan dalam thread
    messages_list = thread.messages.all().order_by('created_at')
    
    context = {
        'thread': thread,
        'messages_list': messages_list,
        'status_choices': MessageThread.STATUS_CHOICES,
        'can_manage': user.role and user.role.role_name in ['Admin', 'Teacher', 'Operator'],
    }
    
    return render(request, 'messages/thread_detail.html', context)


@login_required
@admin_or_teacher_or_operator_required
def assign_thread(request, thread_id):
    """View untuk assign thread ke guru/admin tertentu"""
    thread = get_object_or_404(MessageThread, id=thread_id)
    
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        
        if teacher_id:
            try:
                teacher = User.objects.get(id=teacher_id)
                if teacher.role and teacher.role.role_name in ['Teacher', 'Admin']:
                    thread.teacher_or_admin = teacher
                    thread.save()
                    messages.success(request, f'Thread berhasil di-assign ke {teacher.username}')
                else:
                    messages.error(request, 'User yang dipilih bukan guru atau admin.')
            except User.DoesNotExist:
                messages.error(request, 'User tidak ditemukan.')
        else:
            # Unassign thread
            thread.teacher_or_admin = None
            thread.save()
            messages.success(request, 'Thread berhasil di-unassign.')
    
    return redirect('message_thread', thread_id=thread.id)


@login_required
def message_api_unread_count(request):
    """API untuk mendapatkan jumlah pesan yang belum dibaca"""
    user = request.user
    
    if user.role and user.role.role_name == 'Student':
        # Siswa: hitung pesan belum dibaca dari guru/admin/operator
        unread_count = Message.objects.filter(
            thread__student=user,
            is_read=False
        ).exclude(sender=user).count()
    else:
        # Guru/Admin/Operator: hitung pesan belum dibaca dari siswa
        unread_count = Message.objects.filter(
            Q(thread__teacher_or_admin=user) | Q(thread__teacher_or_admin=None),
            is_read=False
        ).exclude(sender=user).count()
    
    return JsonResponse({'unread_count': unread_count})


# ======================= SUBSCRIPTION & PAYMENT VIEWS =======================

def subscription_packages(request):
    """View untuk menampilkan paket berlangganan"""
    packages = SubscriptionPackage.objects.filter(is_active=True).order_by('price')
    
    # Get active payment methods
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('payment_type', 'name')
    
    # Check if user has pending payment
    pending_payment = None
    if request.user.is_authenticated:
        pending_payment = PaymentProof.objects.filter(
            user=request.user, 
            status='pending'
        ).first()
    
    context = {
        'packages': packages,
        'payment_methods': payment_methods,
        'pending_payment': pending_payment,
    }
    
    if request.user.is_authenticated:
        context['subscription_status'] = request.user.get_subscription_status()
    
    return render(request, 'subscription/packages.html', context)


@login_required
@visitor_or_student_required
def upload_payment_proof(request, package_id):
    """View untuk visitor upload bukti pembayaran"""
    package = get_object_or_404(SubscriptionPackage, id=package_id, is_active=True)
    
    # Check if user already has pending payment for this package
    existing_payment = PaymentProof.objects.filter(
        user=request.user,
        package=package,
        status='pending'
    ).first()
    
    if existing_payment:
        messages.warning(request, 'Anda sudah memiliki bukti pembayaran yang sedang diverifikasi untuk paket ini.')
        return redirect('subscription_packages')
    
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            payment_proof = form.save(commit=False)
            payment_proof.user = request.user
            payment_proof.save()
            
            messages.success(request, 'Bukti pembayaran berhasil diupload! Silakan tunggu verifikasi dari admin.')
            return redirect('subscription_packages')
    else:
        form = PaymentProofForm(initial={'package': package, 'amount_paid': package.price})
    
    # Get active payment methods for reference
    payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('payment_type', 'name')
    
    context = {
        'form': form,
        'package': package,
        'payment_methods': payment_methods,
    }
    
    return render(request, 'subscription/upload_payment.html', context)


@login_required
def payment_status(request):
    """View untuk melihat status pembayaran user"""
    payments = PaymentProof.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'payments': payments,
        'subscription_status': request.user.get_subscription_status(),
    }
    
    return render(request, 'subscription/payment_status.html', context)


# ======================= ADMIN SUBSCRIPTION MANAGEMENT =======================

@login_required
@admin_required
def admin_payment_methods(request):
    """Admin view untuk mengelola metode pembayaran"""
    payment_methods = PaymentMethod.objects.all().order_by('payment_type', 'name')
    
    # Calculate statistics
    total_methods = payment_methods.count()
    active_methods = payment_methods.filter(is_active=True).count()
    bank_methods = payment_methods.filter(payment_type='bank').count()
    ewallet_methods = payment_methods.filter(payment_type='ewallet').count()
    
    context = {
        'payment_methods': payment_methods,
        'total_methods': total_methods,
        'active_methods': active_methods,
        'bank_methods': bank_methods,
        'ewallet_methods': ewallet_methods,
    }
    
    return render(request, 'admin/subscription/payment_method_list.html', context)


@login_required
@admin_required
def create_payment_method(request):
    """Admin view untuk membuat metode pembayaran baru"""
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Metode pembayaran berhasil ditambahkan!')
            return redirect('admin_payment_methods')
        else:
            messages.error(request, 'Terjadi kesalahan. Periksa kembali data yang dimasukkan.')
    else:
        form = PaymentMethodForm()
    
    return render(request, 'admin/subscription/payment_method_form.html', {
        'form': form,
        'title': 'Tambah Metode Pembayaran'
    })


@login_required
@admin_required
def update_payment_method(request, method_id):
    """Admin view untuk mengupdate metode pembayaran"""
    method = get_object_or_404(PaymentMethod, id=method_id)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, 'Metode pembayaran berhasil diupdate!')
            return redirect('admin_payment_methods')
        else:
            messages.error(request, 'Terjadi kesalahan. Periksa kembali data yang dimasukkan.')
    else:
        form = PaymentMethodForm(instance=method)
    
    return render(request, 'admin/subscription/payment_method_form.html', {
        'form': form,
        'method': method,
        'title': 'Edit Metode Pembayaran'
    })


@login_required
@admin_required
def delete_payment_method(request, method_id):
    """Admin view untuk menghapus metode pembayaran"""
    method = get_object_or_404(PaymentMethod, id=method_id)
    
    if request.method == 'POST':
        method_name = method.name
        method.delete()
        messages.success(request, f'Metode pembayaran "{method_name}" berhasil dihapus!')
        return redirect('admin_payment_methods')
    
    return render(request, 'admin/subscription/payment_method_confirm_delete.html', {
        'method': method
    })


@login_required
@admin_required
def admin_subscription_packages(request):
    """Admin view untuk mengelola paket berlangganan"""
    packages = SubscriptionPackage.objects.all().order_by('price')
    
    # Calculate statistics
    total_packages = packages.count()
    featured_count = packages.filter(is_featured=True).count()
    
    # Calculate average price
    avg_price = 0
    max_duration = 0
    if packages.exists():
        from django.db.models import Avg, Max
        avg_result = packages.aggregate(avg_price=Avg('price'))
        avg_price = avg_result['avg_price'] or 0
        
        max_result = packages.aggregate(max_duration=Max('duration_days'))
        max_duration = max_result['max_duration'] or 0
    
    context = {
        'packages': packages,
        'total_packages': total_packages,
        'featured_count': featured_count,
        'avg_price': avg_price,
        'max_duration': max_duration,
    }
    
    return render(request, 'admin/subscription/package_list.html', context)


@login_required
@admin_required
def create_subscription_package(request):
    """Admin view untuk membuat paket berlangganan baru"""
    if request.method == 'POST':
        form = SubscriptionPackageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paket berlangganan berhasil dibuat!')
            return redirect('admin_subscription_packages')
    else:
        form = SubscriptionPackageForm()
    
    context = {
        'form': form,
        'title': 'Buat Paket Berlangganan Baru'
    }
    
    return render(request, 'admin/subscription/package_form.html', context)


@login_required
@admin_required
def update_subscription_package(request, package_id):
    """Admin view untuk update paket berlangganan"""
    package = get_object_or_404(SubscriptionPackage, id=package_id)
    
    if request.method == 'POST':
        form = SubscriptionPackageForm(request.POST, instance=package)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paket berlangganan berhasil diupdate!')
            return redirect('admin_subscription_packages')
    else:
        form = SubscriptionPackageForm(instance=package)
    
    context = {
        'form': form,
        'package': package,
        'title': 'Edit Paket Berlangganan'
    }
    
    return render(request, 'admin/subscription/package_form.html', context)


@login_required
@admin_required
def delete_subscription_package(request, package_id):
    """Admin view untuk delete paket berlangganan"""
    package = get_object_or_404(SubscriptionPackage, id=package_id)
    active_subscribers = package.subscription_set.filter(is_active=True, end_date__gt=timezone.now()).count()
    warning = None
    if active_subscribers > 0:
        warning = f"Paket ini masih memiliki {active_subscribers} subscriber aktif. Menonaktifkan paket tidak akan memutus langganan yang sedang berjalan, namun tidak bisa dipilih user baru." 
    if request.method == 'POST':
        package.is_active = False
        package.save()
        messages.success(request, 'Paket berhasil dinonaktifkan!')
        return redirect('admin_subscription_packages')
    context = {
        'package': package,
        'warning': warning,
    }
    return render(request, 'admin/subscription/package_confirm_delete.html', context)


@login_required
@admin_or_operator_required
def admin_payment_verifications(request):
    """Admin view untuk verifikasi pembayaran"""
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    payments = PaymentProof.objects.all().order_by('-created_at')
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    if search_query:
        payments = payments.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(package__name__icontains=search_query)
        )
    
    # Calculate statistics for all payments (not filtered)
    all_payments = PaymentProof.objects.all()
    payment_stats = {
        'total_count': all_payments.count(),
        'pending_count': all_payments.filter(status='pending').count(),
        'approved_count': all_payments.filter(status='approved').count(),
        'rejected_count': all_payments.filter(status='rejected').count(),
    }
    
    # Pagination
    paginator = Paginator(payments, 10)
    page = request.GET.get('page')
    try:
        payments_page = paginator.page(page)
    except PageNotAnInteger:
        payments_page = paginator.page(1)
    except EmptyPage:
        payments_page = paginator.page(paginator.num_pages)
    
    context = {
        'payments': payments_page,
        'status_choices': PaymentProof.STATUS_CHOICES,
        'current_status': status_filter,
        'current_search': search_query,
        'payment_stats': payment_stats,
    }
    
    return render(request, 'admin/payment/verification_list.html', context)


@login_required
@admin_or_operator_required
def verify_payment(request, payment_id):
    """Admin view untuk verifikasi individual payment"""
    payment = get_object_or_404(PaymentProof, id=payment_id)
    original_status = payment.status  # Store original status to detect changes
    
    if request.method == 'POST':
        form = PaymentVerificationForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            
            # Handle status changes
            if payment.status == 'approved' and original_status != 'approved':
                # Payment newly approved - upgrade user
                upgrade_user_to_student(payment.user, payment.package, payment)
                messages.success(request, f'Pembayaran disetujui! User {payment.user.email} telah diupgrade ke Student.')
            
            elif payment.status == 'rejected' and original_status == 'approved':
                # Payment was approved but now rejected - deactivate subscription
                deactivate_user_subscription(payment.user, payment)
                
                # Check current user status to provide accurate message
                payment.user.refresh_from_db()
                if payment.user.role.role_name == 'Visitor':
                    messages.warning(request, f'Pembayaran ditolak! User {payment.user.email} telah diturunkan ke Visitor dan subscription dinonaktifkan.')
                else:
                    messages.warning(request, f'Pembayaran ditolak! Subscription terkait telah dinonaktifkan, namun user {payment.user.email} masih memiliki subscription aktif lain.')
            
            elif payment.status == 'rejected':
                # Payment rejected (not previously approved)
                messages.info(request, f'Pembayaran user {payment.user.email} ditolak.')
            
            else:
                # Other status changes
                messages.info(request, f'Status pembayaran user {payment.user.email} telah diupdate.')
            
            return redirect('admin_payment_verifications')
    else:
        form = PaymentVerificationForm(instance=payment)
    
    context = {
        'form': form,
        'payment': payment,
    }
    
    return render(request, 'admin/payment/verify_payment.html', context)


def upgrade_user_to_student(user, package, payment_proof):
    """Upgrade visitor to student with subscription"""
    try:
        student_role = Role.objects.get(role_name='Student')
        
        with transaction.atomic():
            # Change user role
            user.role = student_role
            user.save()
            
            # Create or update subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                defaults={
                    'package': package,
                    'end_date': timezone.now() + timezone.timedelta(days=package.duration_days),
                    'payment_proof': payment_proof
                }
            )
            
            if not created:
                # Extend existing subscription
                subscription.package = package
                subscription.extend_subscription(package.duration_days)
                subscription.payment_proof = payment_proof
                subscription.is_active = True
                subscription.save()
    
    except Role.DoesNotExist:
        # Create Student role if it doesn't exist
        student_role = Role.objects.create(role_name='Student')
        upgrade_user_to_student(user, package, payment_proof)


def deactivate_user_subscription(user, payment_proof):
    """Deactivate user subscription and downgrade to Visitor when payment is rejected"""
    try:
        visitor_role = Role.objects.get(role_name='Visitor')
        
        with transaction.atomic():
            # Since UserSubscription uses OneToOneField, each user has only one subscription
            try:
                subscription = user.subscription  # OneToOneField reverse lookup
                
                # Check if this subscription is linked to the rejected payment
                if subscription.payment_proof == payment_proof:
                    # This subscription is directly linked to the rejected payment
                    subscription.is_active = False
                    subscription.save()
                    
                    # Downgrade user to Visitor since their payment was rejected
                    user.role = visitor_role
                    user.save()
                    
                    print(f"Deactivated subscription {subscription.id} and downgraded user {user.email} to Visitor due to rejected payment {payment_proof.id}")
                else:
                    # The subscription is linked to a different payment
                    # Check if that payment is still approved
                    if subscription.payment_proof and subscription.payment_proof.status == 'approved':
                        # User has an active subscription with an approved payment, don't downgrade
                        print(f"User {user.email} has active subscription linked to approved payment {subscription.payment_proof.id}, not downgrading")
                    else:
                        # The subscription's payment is also not approved, deactivate
                        subscription.is_active = False
                        subscription.save()
                        user.role = visitor_role
                        user.save()
                        print(f"Deactivated subscription {subscription.id} and downgraded user {user.email} to Visitor")
                        
            except UserSubscription.DoesNotExist:
                # User has no subscription, just ensure they're a Visitor
                if user.role.role_name != 'Visitor':
                    user.role = visitor_role
                    user.save()
                    print(f"Downgraded user {user.email} to Visitor (no subscription found)")
    
    except Role.DoesNotExist:
        # Create Visitor role if it doesn't exist
        visitor_role = Role.objects.create(role_name='Visitor')
        deactivate_user_subscription(user, payment_proof)


@login_required
@admin_or_operator_required
def admin_user_subscriptions(request):
    """Admin view untuk melihat semua subscription users"""
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    subscriptions = UserSubscription.objects.select_related('user', 'package').all().order_by('-created_at')
    
    if search_query:
        subscriptions = subscriptions.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    if status_filter == 'active':
        subscriptions = subscriptions.filter(is_active=True, end_date__gt=timezone.now())
    elif status_filter == 'expired':
        subscriptions = subscriptions.filter(end_date__lt=timezone.now())
    elif status_filter == 'expiring_soon':
        week_from_now = timezone.now() + timezone.timedelta(days=7)
        subscriptions = subscriptions.filter(
            is_active=True, 
            end_date__gt=timezone.now(),
            end_date__lt=week_from_now
        )
    
    # Pagination
    paginator = Paginator(subscriptions, 15)
    page = request.GET.get('page')
    try:
        subscriptions_page = paginator.page(page)
    except PageNotAnInteger:
        subscriptions_page = paginator.page(1)
    except EmptyPage:
        subscriptions_page = paginator.page(paginator.num_pages)
    
    # Calculate statistics
    all_subscriptions = UserSubscription.objects.all()
    current_time = timezone.now()
    week_from_now = current_time + timezone.timedelta(days=7)
    
    total_count = all_subscriptions.count()
    active_count = all_subscriptions.filter(
        is_active=True, 
        end_date__gt=current_time
    ).count()
    expired_count = all_subscriptions.filter(
        end_date__lt=current_time
    ).count()
    expiring_soon_count = all_subscriptions.filter(
        is_active=True,
        end_date__gt=current_time,
        end_date__lt=week_from_now
    ).count()
    
    context = {
        'subscriptions': subscriptions_page,
        'current_search': search_query,
        'current_status': status_filter,
        'status_choices': [
            ('', 'Semua'),
            ('active', 'Aktif'),
            ('expired', 'Kadaluarsa'),
            ('expiring_soon', 'Akan Berakhir'),
        ],
        'total_count': total_count,
        'active_count': active_count,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
    }
    
    return render(request, 'admin/subscription/user_subscriptions.html', context)


@login_required
@admin_or_operator_required
def extend_user_subscription(request, subscription_id):
    """Admin view untuk extend subscription user"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    
    if request.method == 'POST':
        days = request.POST.get('days')
        try:
            days = int(days)
            if days > 0:
                subscription.extend_subscription(days)
                messages.success(request, f'Subscription user {subscription.user.email} berhasil diperpanjang {days} hari.')
            else:
                messages.error(request, 'Jumlah hari harus lebih dari 0.')
        except ValueError:
            messages.error(request, 'Jumlah hari tidak valid.')
        
        return redirect('admin_user_subscriptions')
    
    context = {
        'subscription': subscription,
    }
    
    return render(request, 'admin/subscription/extend_subscription.html', context)


@login_required
@admin_or_operator_required
def manual_role_change(request, user_id):
    """Admin view untuk manual change user role dengan subscription"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserRoleChangeForm(request.POST, instance=user)
        if form.is_valid():
            new_role = form.cleaned_data['role']
            # Server-side enforcement: Operator cannot set Admin role
            if request.user.role.role_name == 'Operator' and new_role and new_role.role_name == 'Admin':
                form.add_error('role', 'Operator tidak memiliki izin untuk memberikan role Admin.')
            else:
                old_role = user.role

                with transaction.atomic():
                    user.role = new_role
                    user.save()

                    # Jika upgrade ke Student, buat subscription
                    if new_role.role_name == 'Student' and old_role.role_name == 'Visitor':
                        package = form.cleaned_data.get('subscription_package')
                        days = form.cleaned_data.get('subscription_days', 30)

                        if package:
                            subscription, created = UserSubscription.objects.get_or_create(
                                user=user,
                                defaults={
                                    'package': package,
                                    'end_date': timezone.now() + timezone.timedelta(days=days)
                                }
                            )

                            if not created:
                                subscription.extend_subscription(days)
                                subscription.package = package
                                subscription.is_active = True
                                subscription.save()

                    # Jika downgrade ke Visitor, deaktivasi subscription
                    elif new_role.role_name == 'Visitor' and old_role.role_name == 'Student':
                        try:
                            subscription = user.subscription
                            subscription.is_active = False
                            subscription.save()
                        except UserSubscription.DoesNotExist:
                            pass

                messages.success(request, f'Role user {user.email} berhasil diubah dari {old_role.role_name} ke {new_role.role_name}.')
                return redirect('user_list')
    else:
        form = UserRoleChangeForm(instance=user)
    
    context = {
        'form': form,
        'user': user,
    }
    
    return render(request, 'admin/manage_user/change_role.html', context)


@login_required
@admin_or_operator_required
def toggle_subscription_status(request, subscription_id):
    """API endpoint untuk toggle status subscription"""
    if request.method == 'POST':
        try:
            subscription = get_object_or_404(UserSubscription, id=subscription_id)
            
            # Toggle the is_active status
            subscription.is_active = not subscription.is_active
            subscription.save()
            
            action = 'activated' if subscription.is_active else 'deactivated'
            
            return JsonResponse({
                'success': True,
                'message': f'Subscription {action} successfully',
                'new_status': subscription.is_active
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=405)


@login_required
@admin_or_operator_required
def subscription_details(request, subscription_id):
    """Admin view untuk melihat detail subscription"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    
    context = {
        'subscription': subscription,
        'user': subscription.user,
        'package': subscription.package,
        'payment_proof': subscription.payment_proof,
    }
    
    return render(request, 'admin/subscription/subscription_details.html', context)


@login_required
@admin_or_operator_required
def edit_user_subscription(request, subscription_id):
    """Admin view untuk edit subscription user"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id)
    
    if request.method == 'POST':
        form = UserSubscriptionEditForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, f'Subscription for {subscription.user.email} has been updated successfully!')
            return redirect('admin_user_subscriptions')
    else:
        form = UserSubscriptionEditForm(instance=subscription)
    
    context = {
        'form': form,
        'subscription': subscription,
        'title': f'Edit Subscription - {subscription.user.email}'
    }
    
    return render(request, 'admin/subscription/edit_subscription.html', context)

@login_required
@active_subscription_required
def student_rankings(request):
    """Student rankings page with various filters and sorting options"""
    from django.db.models import Avg, Max, Count, Q
    from django.db import models
    
    # Get filter parameters
    ranking_type = request.GET.get('ranking_type', 'utbk_package_best')  # utbk_package_best, overall_average, category_best, category_average
    category_id = request.GET.get('category_id', '')
    utbk_package_id = request.GET.get('utbk_package_id', '')
    time_period = request.GET.get('time_period', 'all')  # all, week, month, year
    scoring_method = request.GET.get('scoring_method', 'all')  # all, default, custom, utbk
    min_tests = int(request.GET.get('min_tests', 3))  # Minimum number of tests to qualify
    university_id = request.GET.get('university_id', '')
    
    # Base queryset for submitted tests
    base_tests = Test.objects.filter(is_submitted=True).select_related('student')
    
    # Apply time period filter
    if time_period != 'all':
        from datetime import datetime, timedelta
        now = timezone.now()
        
        if time_period == 'week':
            start_date = now - timedelta(days=7)
        elif time_period == 'month':
            start_date = now - timedelta(days=30)
        elif time_period == 'year':
            start_date = now - timedelta(days=365)
        
        base_tests = base_tests.filter(date_taken__gte=start_date)
    
    # Apply scoring method filter
    if scoring_method != 'all':
        base_tests = base_tests.filter(categories__scoring_method=scoring_method)
    
    # Apply category filter if specified
    if category_id and category_id.isdigit():
        base_tests = base_tests.filter(categories__id=int(category_id))
    
    # Build rankings based on type
    rankings = []
    show_utbk_university_info = False
    utbk_category = None
    if scoring_method == 'utbk' or (category_id and category_id.isdigit() and Category.objects.filter(id=category_id, scoring_method='utbk').exists()):
        show_utbk_university_info = True
        if category_id and category_id.isdigit():
            utbk_category = Category.objects.filter(id=category_id, scoring_method='utbk').first()

    if ranking_type == 'utbk_package_best':
        # Best score per UTBK tryout package (default)
        # Get all students who have submitted UTBK tryout package tests
        utbk_tests = Test.objects.filter(is_submitted=True, tryout_package__isnull=False, categories__scoring_method='utbk')
        if utbk_package_id and utbk_package_id.isdigit():
            utbk_tests = utbk_tests.filter(tryout_package__id=int(utbk_package_id))
        if university_id and university_id.isdigit():
            # Only include students whose best/latest UTBK test has this university as a target
            utbk_tests = utbk_tests.filter(
                student__university_target__primary_university_id=university_id
            ) | utbk_tests.filter(
                student__university_target__backup_university_id=university_id
            ) | utbk_tests.filter(
                student__university_target__secondary_university_id=university_id
            )
        # For each student, get their best score in any UTBK tryout package
        student_best = {}
        for test in utbk_tests.select_related('student').order_by('-score'):
            sid = test.student.id
            if sid not in student_best:
                student_best[sid] = test
        # Sort by score
        sorted_best = sorted(student_best.values(), key=lambda t: t.score, reverse=True)
        for i, test in enumerate(sorted_best[:50], 1):
            row = {
                'rank': i,
                'student_id': test.student.id,
                'username': test.student.username,
                'email': test.student.email,
                'score': round(test.score, 1),
                'total_tests': Test.objects.filter(student=test.student, is_submitted=True, tryout_package__isnull=False, categories__scoring_method='utbk').count(),
                'max_score': round(test.score, 1),
                'latest_test': test.date_taken,
                'is_current_user': test.student.id == request.user.id,
                'latest_test_package_name': test.tryout_package.package_name if test.tryout_package else None,
                'latest_test_category_name': test.categories.first().category_name if test.categories.exists() else None,
            }
            # Add university info for UTBK if applicable
            recs = test.get_university_recommendations() if hasattr(test, 'get_university_recommendations') else []
            total_targets = 0
            met_targets = 0
            met_target_type = None
            for rec in recs:
                if rec.get('target_type') != 'suggested':
                    total_targets += 1
                    if rec.get('meets_minimum'):
                        met_targets += 1
                        if not met_target_type:
                            met_target_type = rec.get('target_type')
            if total_targets > 0:
                if met_targets == total_targets:
                    target_achievement_status = 'all_met'
                elif met_targets > 0:
                    target_achievement_status = 'some_met'
                else:
                    target_achievement_status = 'none_met'
            else:
                target_achievement_status = None
            row['university_info'] = {
                'recommendations': recs,
                'target_achievement_status': target_achievement_status,
                'met_target_type': met_target_type,
            }
            rankings.append(row)
    elif ranking_type == 'overall_average':
        student_stats = base_tests.values('student__id', 'student__username', 'student__email') \
            .annotate(
                avg_score=Avg('score'),
                total_tests=Count('id'),
                max_score=Max('score'),
                latest_test=Max('date_taken')
            ) \
            .filter(total_tests__gte=min_tests) \
            .order_by('-avg_score', '-total_tests')
        for i, stat in enumerate(student_stats[:50], 1):
            # Get latest test for this student
            latest_test_obj = Test.objects.filter(student_id=stat['student__id'], is_submitted=True).order_by('-date_taken').first()
            ranking_row = {
                'rank': i,
                'student_id': stat['student__id'],
                'username': stat['student__username'],
                'email': stat['student__email'],
                'score': round(stat['avg_score'], 1),
                'total_tests': stat['total_tests'],
                'max_score': round(stat['max_score'], 1),
                'latest_test': stat['latest_test'],
                'is_current_user': stat['student__id'] == request.user.id,
                'latest_test_package_name': latest_test_obj.tryout_package.package_name if latest_test_obj and latest_test_obj.tryout_package else None,
                'latest_test_category_name': latest_test_obj.categories.first().category_name if latest_test_obj and latest_test_obj.categories.exists() else None,
            }
            # Add university info for UTBK if applicable
            if show_utbk_university_info:
                latest_utbk_test = Test.objects.filter(student_id=stat['student__id'], is_submitted=True, categories__scoring_method='utbk').order_by('-date_taken').first()
                if latest_utbk_test:
                    recs = latest_utbk_test.get_university_recommendations() if hasattr(latest_utbk_test, 'get_university_recommendations') else []
                    # Target achievement status logic
                    total_targets = 0
                    met_targets = 0
                    met_target_type = None
                    for rec in recs:
                        if rec.get('target_type') != 'suggested':
                            total_targets += 1
                            if rec.get('meets_minimum'):
                                met_targets += 1
                                if not met_target_type:
                                    met_target_type = rec.get('target_type')
                    if total_targets > 0:
                        if met_targets == total_targets:
                            target_achievement_status = 'all_met'
                        elif met_targets > 0:
                            target_achievement_status = 'some_met'
                        else:
                            target_achievement_status = 'none_met'
                    else:
                        target_achievement_status = None
                    ranking_row['university_info'] = {
                        'recommendations': recs,
                        'target_achievement_status': target_achievement_status,
                        'met_target_type': met_target_type,
                    }
            rankings.append(ranking_row)
    elif ranking_type == 'category_best':
        if category_id and category_id.isdigit():
            student_stats = base_tests.values('student__id', 'student__username', 'student__email') \
                .annotate(
                    best_score=Max('score'),
                    total_tests=Count('id'),
                    avg_score=Avg('score'),
                    latest_test=Max('date_taken')
                ) \
                .filter(total_tests__gte=min_tests) \
                .order_by('-best_score', '-avg_score')
            for i, stat in enumerate(student_stats[:50], 1):
                # Get latest test for this student
                latest_test_obj = Test.objects.filter(student_id=stat['student__id'], is_submitted=True).order_by('-date_taken').first()
                ranking_row = {
                    'rank': i,
                    'student_id': stat['student__id'],
                    'username': stat['student__username'],
                    'email': stat['student__email'],
                    'score': round(stat['best_score'], 1),
                    'avg_score': round(stat['avg_score'], 1),
                    'total_tests': stat['total_tests'],
                    'latest_test': stat['latest_test'],
                    'is_current_user': stat['student__id'] == request.user.id,
                    'latest_test_package_name': latest_test_obj.tryout_package.package_name if latest_test_obj and latest_test_obj.tryout_package else None,
                    'latest_test_category_name': latest_test_obj.categories.first().category_name if latest_test_obj and latest_test_obj.categories.exists() else None,
                }
                if show_utbk_university_info:
                    latest_utbk_test = Test.objects.filter(student_id=stat['student__id'], is_submitted=True, categories__scoring_method='utbk').order_by('-date_taken').first()
                    if latest_utbk_test:
                        recs = latest_utbk_test.get_university_recommendations() if hasattr(latest_utbk_test, 'get_university_recommendations') else []
                        total_targets = 0
                        met_targets = 0
                        met_target_type = None
                        for rec in recs:
                            if rec.get('target_type') != 'suggested':
                                total_targets += 1
                                if rec.get('meets_minimum'):
                                    met_targets += 1
                                    if not met_target_type:
                                        met_target_type = rec.get('target_type')
                        if total_targets > 0:
                            if met_targets == total_targets:
                                target_achievement_status = 'all_met'
                            elif met_targets > 0:
                                target_achievement_status = 'some_met'
                            else:
                                target_achievement_status = 'none_met'
                        else:
                            target_achievement_status = None
                        ranking_row['university_info'] = {
                            'recommendations': recs,
                            'target_achievement_status': target_achievement_status,
                            'met_target_type': met_target_type,
                        }
                rankings.append(ranking_row)
    elif ranking_type == 'category_average':
        if category_id and category_id.isdigit():
            student_stats = base_tests.values('student__id', 'student__username', 'student__email') \
                .annotate(
                    avg_score=Avg('score'),
                    total_tests=Count('id'),
                    max_score=Max('score'),
                    latest_test=Max('date_taken')
                ) \
                .filter(total_tests__gte=min_tests) \
                .order_by('-avg_score', '-total_tests')
            for i, stat in enumerate(student_stats[:50], 1):
                # Get latest test for this student
                latest_test_obj = Test.objects.filter(student_id=stat['student__id'], is_submitted=True).order_by('-date_taken').first()
                ranking_row = {
                    'rank': i,
                    'student_id': stat['student__id'],
                    'username': stat['student__username'],
                    'email': stat['student__email'],
                    'score': round(stat['avg_score'], 1),
                    'total_tests': stat['total_tests'],
                    'max_score': round(stat['max_score'], 1),
                    'latest_test': stat['latest_test'],
                    'is_current_user': stat['student__id'] == request.user.id,
                    'latest_test_package_name': latest_test_obj.tryout_package.package_name if latest_test_obj and latest_test_obj.tryout_package else None,
                    'latest_test_category_name': latest_test_obj.categories.first().category_name if latest_test_obj and latest_test_obj.categories.exists() else None,
                }
                if show_utbk_university_info:
                    latest_utbk_test = Test.objects.filter(student_id=stat['student__id'], is_submitted=True, categories__scoring_method='utbk').order_by('-date_taken').first()
                    if latest_utbk_test:
                        recs = latest_utbk_test.get_university_recommendations() if hasattr(latest_utbk_test, 'get_university_recommendations') else []
                        total_targets = 0
                        met_targets = 0
                        met_target_type = None
                        for rec in recs:
                            if rec.get('target_type') != 'suggested':
                                total_targets += 1
                                if rec.get('meets_minimum'):
                                    met_targets += 1
                                    if not met_target_type:
                                        met_target_type = rec.get('target_type')
                        if total_targets > 0:
                            if met_targets == total_targets:
                                target_achievement_status = 'all_met'
                            elif met_targets > 0:
                                target_achievement_status = 'some_met'
                            else:
                                target_achievement_status = 'none_met'
                        else:
                            target_achievement_status = None
                        ranking_row['university_info'] = {
                            'recommendations': recs,
                            'target_achievement_status': target_achievement_status,
                            'met_target_type': met_target_type,
                        }
                rankings.append(ranking_row)
    
    # Get current user's position if not in top 50
    current_user_rank = None
    if not any(r['is_current_user'] for r in rankings):
        # Find current user's rank
        if ranking_type == 'overall_average':
            user_stats = base_tests.filter(student=request.user) \
                .aggregate(
                    avg_score=Avg('score'),
                    total_tests=Count('id')
                )
            
            if user_stats['total_tests'] and user_stats['total_tests'] >= min_tests:
                # Count how many students have better average score
                better_students = base_tests.values('student__id') \
                    .annotate(
                        avg_score=Avg('score'),
                        total_tests=Count('id')
                    ) \
                    .filter(
                        total_tests__gte=min_tests,
                        avg_score__gt=user_stats['avg_score']
                    ).count()
                
                current_user_rank = {
                    'rank': better_students + 1,
                    'score': round(user_stats['avg_score'], 1),
                    'total_tests': user_stats['total_tests']
                }
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(
        id__in=Test.objects.filter(is_submitted=True).values_list('categories__id', flat=True)
    ).distinct().order_by('category_name')
    # Get universities for filter dropdown
    universities = University.objects.filter(is_active=True).order_by('name')
    # Get UTBK tryout packages for filter dropdown
    from otosapp.models import TryoutPackage
    utbk_packages = TryoutPackage.objects.filter(
        is_active=True,
        categories__scoring_method='utbk'
    ).distinct().order_by('package_name')
    
    # Get selected category name
    selected_category = None
    if category_id and category_id.isdigit():
        try:
            selected_category = Category.objects.get(id=int(category_id))
        except Category.DoesNotExist:
            pass
    
    # Enrich rankings with avatars and chosen university targets
    if rankings:
        try:
            student_ids = [r.get('student_id') for r in rankings if r.get('student_id')]
            # Batch fetch users for avatars
            users_qs = User.objects.filter(id__in=student_ids).only('id', 'profile_picture', 'first_name', 'last_name', 'email')
            user_map = {u.id: u for u in users_qs}
            # Batch fetch university targets
            from otosapp.models import UniversityTarget
            targets_qs = UniversityTarget.objects.select_related(
                'primary_university', 'secondary_university', 'backup_university'
            ).filter(user_id__in=student_ids)
            targets_map = {t.user_id: t for t in targets_qs}
            for row in rankings:
                sid = row.get('student_id')
                user_obj = user_map.get(sid)
                row['profile_picture'] = getattr(user_obj, 'profile_picture', None) if user_obj else None
                # Compute display name (full name; fallback to email)
                full_name = ''
                if user_obj:
                    first = getattr(user_obj, 'first_name', '') or ''
                    last = getattr(user_obj, 'last_name', '') or ''
                    full_name = f"{first} {last}".strip()
                email_fb = (getattr(user_obj, 'email', None) if user_obj else None) or row.get('email') or row.get('username')
                row['display_name'] = full_name if full_name else email_fb
                ut = targets_map.get(sid)
                targets = []
                if ut:
                    if ut.primary_university_id:
                        targets.append({'label': 'Target Utama', 'university': ut.primary_university})
                    if ut.backup_university_id:
                        targets.append({'label': 'Target Aman', 'university': ut.backup_university})
                    if ut.secondary_university_id:
                        targets.append({'label': 'Target Cadangan', 'university': ut.secondary_university})
                row['user_targets'] = targets
        except Exception as e:
            # Fail-safe: don't break page if enrichment fails
            try:
                from django.conf import settings as dj_settings
                if dj_settings.DEBUG:
                    print(f"[DEBUG] Rankings enrichment error: {e}")
            except Exception:
                pass

        # Compute normalized score percentage and color for progress bars
        try:
            max_score_value = max((r.get('score') or 0) for r in rankings) or 1
        except ValueError:
            max_score_value = 1
        for r in rankings:
            raw = r.get('score') or 0
            pct = int(round((raw / max_score_value) * 100))
            if pct < 0:
                pct = 0
            if pct > 100:
                pct = 100
            r['score_pct'] = pct
            r['score_left_pct'] = 100 - pct
            if pct >= 85:
                r['bar_color'] = 'bg-green-500'
            elif pct >= 70:
                r['bar_color'] = 'bg-blue-500'
            elif pct >= 50:
                r['bar_color'] = 'bg-yellow-500'
            else:
                r['bar_color'] = 'bg-red-500'

    # Get some general statistics
    total_students = User.objects.filter(
        role__role_name='Student',
        tests__is_submitted=True
    ).distinct().count()
    
    total_tests_taken = base_tests.count()
    
    context = {
        'rankings': rankings,
        'current_user_rank': current_user_rank,
        'categories': categories,
        'universities': universities,
        'utbk_packages': utbk_packages,
        'selected_category': selected_category,
        'ranking_type': ranking_type,
        'category_id': category_id,
        'utbk_package_id': utbk_package_id,
        'university_id': university_id,
        'time_period': time_period,
        'scoring_method': scoring_method,
        'min_tests': min_tests,
        'total_students': total_students,
        'total_tests_taken': total_tests_taken,
    }
    
    return render(request, 'students/rankings/student_rankings.html', context)


# ======================= UNIVERSITY MANAGEMENT VIEWS =======================

@login_required
@admin_or_operator_required
def admin_university_list(request):
    """Admin view untuk mengelola daftar universitas"""
    search_query = request.GET.get('search', '')
    tier_filter = request.GET.get('tier', '')
    
    universities = University.objects.all().order_by('tier', 'name')
    
    if search_query:
        universities = universities.filter(
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if tier_filter:
        universities = universities.filter(tier=tier_filter)
    
    # Pagination
    paginator = Paginator(universities, 10)
    page = request.GET.get('page')
    try:
        universities_page = paginator.page(page)
    except PageNotAnInteger:
        universities_page = paginator.page(1)
    except EmptyPage:
        universities_page = paginator.page(paginator.num_pages)
    
    # Calculate statistics
    total_universities = University.objects.count()
    active_universities = University.objects.filter(is_active=True).count()
    tier1_count = University.objects.filter(tier='tier1').count()
    tier2_count = University.objects.filter(tier='tier2').count()
    tier3_count = University.objects.filter(tier='tier3').count()
    
    context = {
        'universities': universities_page,
        'current_search': search_query,
        'current_tier': tier_filter,
        'tier_choices': University._meta.get_field('tier').choices,
        'total_universities': total_universities,
        'active_universities': active_universities,
        'tier1_count': tier1_count,
        'tier2_count': tier2_count,
        'tier3_count': tier3_count,
    }
    
    return render(request, 'admin/university/university_list.html', context)


@login_required
@admin_or_operator_required
def admin_university_create(request):
    """Admin view untuk membuat universitas baru"""
    if request.method == 'POST':
        form = UniversityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Universitas berhasil ditambahkan!')
            return redirect('admin_university_list')
    else:
        form = UniversityForm()
    
    context = {
        'form': form,
        'title': 'Tambah Universitas Baru'
    }
    
    return render(request, 'admin/university/university_form.html', context)


@login_required
@admin_or_operator_required
def admin_university_update(request, university_id):
    """Admin view untuk mengupdate universitas"""
    university = get_object_or_404(University, id=university_id)
    
    if request.method == 'POST':
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data universitas berhasil diupdate!')
            return redirect('admin_university_list')
    else:
        form = UniversityForm(instance=university)
    
    context = {
        'form': form,
        'university': university,
        'title': f'Edit Universitas - {university.name}'
    }
    
    return render(request, 'admin/university/university_form.html', context)


@login_required
@admin_or_operator_required
def admin_university_delete(request, university_id):
    """Admin view untuk menghapus universitas"""
    university = get_object_or_404(University, id=university_id)
    
    # Check if university is being used as target
    target_count = UniversityTarget.objects.filter(
        Q(primary_university=university) |
        Q(secondary_university=university) |
        Q(backup_university=university)
    ).count()
    
    if request.method == 'POST':
        if target_count > 0:
            # Don't actually delete, just deactivate
            university.is_active = False
            university.save()
            messages.warning(request, f'Universitas dinonaktifkan karena masih digunakan sebagai target oleh {target_count} student(s).')
        else:
            university.delete()
            messages.success(request, 'Universitas berhasil dihapus!')
        return redirect('admin_university_list')
    
    context = {
        'university': university,
        'target_count': target_count,
    }
    
    return render(request, 'admin/university/university_confirm_delete.html', context)


@login_required
@active_subscription_required
def student_university_target(request):
    """Student view untuk mengatur target universitas"""
    try:
        university_target = request.user.university_target
    except UniversityTarget.DoesNotExist:
        university_target = None
    
    if request.method == 'POST':
        if university_target:
            form = UniversityTargetForm(request.POST, instance=university_target)
        else:
            form = UniversityTargetForm(request.POST)
        
        if form.is_valid():
            target = form.save(commit=False)
            target.user = request.user
            target.save()
            messages.success(request, 'Target universitas berhasil disimpan!')
            return redirect('student_university_target')
    else:
        if university_target:
            form = UniversityTargetForm(instance=university_target)
        else:
            form = UniversityTargetForm()
    
    # Get recommendations based on latest UTBK test score
    recommendations = []
    latest_utbk_test = Test.objects.filter(
        student=request.user,
        is_submitted=True,
        categories__scoring_method='utbk'
    ).order_by('-date_taken').first()
    
    if latest_utbk_test and university_target:
        recommendations = university_target.get_recommendations_for_score(latest_utbk_test.score)
    
    # Get all universities for suggestions (top 10 by tier)
    suggested_universities = University.objects.filter(is_active=True).order_by('tier', 'minimum_utbk_score')[:10]
    
    # Calculate score percentage for progress bar
    score_percentage = 0
    if latest_utbk_test:
        score_percentage = min((latest_utbk_test.score / 7000) * 100, 100)
    
    context = {
        'form': form,
        'university_target': university_target,
        'recommendations': recommendations,
        'latest_utbk_test': latest_utbk_test,
        'suggested_universities': suggested_universities,
        'score_percentage': score_percentage,
    }
    
    return render(request, 'students/university/target_settings.html', context)


@login_required
@active_subscription_required
def student_university_recommendations(request):
    """Student view untuk melihat rekomendasi universitas berdasarkan skor terbaru"""
    # Get latest UTBK test
    latest_utbk_test = Test.objects.filter(
        student=request.user,
        is_submitted=True,
        categories__scoring_method='utbk'
    ).order_by('-date_taken').first()
    
    if not latest_utbk_test:
        messages.info(request, 'Anda perlu mengerjakan tryout UTBK terlebih dahulu untuk mendapatkan rekomendasi.')
        return redirect('tryout_list')
    
    # Get user's targets
    try:
        user_targets = request.user.university_target
        target_recommendations = user_targets.get_recommendations_for_score(latest_utbk_test.score)
    except UniversityTarget.DoesNotExist:
        user_targets = None
        target_recommendations = []
    
    # Get general recommendations (all universities sorted by suitability)
    all_universities = University.objects.filter(is_active=True).order_by('tier', 'minimum_utbk_score')
    general_recommendations = []
    
    for university in all_universities:
        recommendation = university.get_recommendation_for_score(latest_utbk_test.score)
        general_recommendations.append({
            'university': university,
            'recommendation': recommendation
        })
    
    # Sort by recommendation status (sangat_aman first, then aman, etc.)
    status_order = {'sangat_aman': 1, 'aman': 2, 'kurang_aman': 3, 'tidak_aman': 4}
    general_recommendations.sort(key=lambda x: (
        status_order.get(x['recommendation']['status'], 5),
        -x['recommendation']['percentage']
    ))
    
    context = {
        'latest_utbk_test': latest_utbk_test,
        'user_targets': user_targets,
        'target_recommendations': target_recommendations,
        'general_recommendations': general_recommendations[:20],  # Limit to top 20
        'test_score_analysis': latest_utbk_test.get_score_analysis(),
    }
    
    return render(request, 'students/university/recommendations.html', context)

# ============================
# TRYOUT PACKAGE MANAGEMENT
# ============================

@admin_or_operator_required
def admin_package_list(request):
    """List all tryout packages for admin/operator"""
    packages = TryoutPackage.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        packages = packages.filter(
            Q(package_name__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(packages, 10)
    page = request.GET.get('page')
    
    try:
        packages = paginator.page(page)
    except PageNotAnInteger:
        packages = paginator.page(1)
    except EmptyPage:
        packages = paginator.page(paginator.num_pages)
    
    context = {
        'packages': packages,
        'search_query': search_query,
        'total_packages': TryoutPackage.objects.count(),
        'active_packages': TryoutPackage.objects.filter(is_active=True).count(),
        'inactive_packages': TryoutPackage.objects.filter(is_active=False).count(),
    }
    
    return render(request, 'admin/package/package_list.html', context)

@admin_or_operator_required
def admin_package_create(request):
    """Create new tryout package"""
    if request.method == 'POST':
        form = TryoutPackageForm(request.POST)
        formset = TryoutPackageCategoryFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                package = form.save(commit=False)
                package.created_by = request.user
                package.save()
                
                formset.instance = package
                formset.save()
                
                # Validate total score
                total_score = package.get_total_max_score()
                if abs(total_score - 7000) > 0.01:
                    messages.warning(request, f'Peringatan: Total skor adalah {total_score}, bukan 7000. Silakan sesuaikan.')
                else:
                    messages.success(request, f'Paket "{package.package_name}" berhasil dibuat!')
                
                return redirect('admin_package_update', package_id=package.id)
    else:
        form = TryoutPackageForm()
        formset = TryoutPackageCategoryFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Buat Paket Tryout Baru'
    }
    
    return render(request, 'admin/package/package_form.html', context)

@admin_or_operator_required
def admin_package_update(request, package_id):
    """Update existing tryout package"""
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    if request.method == 'POST':
        form = TryoutPackageForm(request.POST, instance=package)
        formset = TryoutPackageCategoryFormSet(request.POST, instance=package)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                package = form.save()
                formset.save()
                
                # Validate total score
                total_score = package.get_total_max_score()
                if abs(total_score - 7000) > 0.01:
                    messages.warning(request, f'Peringatan: Total skor adalah {total_score}, bukan 7000. Silakan sesuaikan.')
                else:
                    messages.success(request, f'Paket "{package.package_name}" berhasil diperbarui!')
                
                return redirect('admin_package_list')
    else:
        form = TryoutPackageForm(instance=package)
        formset = TryoutPackageCategoryFormSet(instance=package)
    
    context = {
        'form': form,
        'formset': formset,
        'package': package,
        'title': f'Edit Paket: {package.package_name}',
        'total_score': package.get_total_max_score(),
        'total_questions': package.get_total_questions(),
        'is_scoring_complete': package.is_scoring_complete()
    }
    
    return render(request, 'admin/package/package_form.html', context)

@admin_or_operator_required
def admin_package_delete(request, package_id):
    """Delete tryout package"""
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    if request.method == 'POST':
        # Check if package has been used by students
        if Test.objects.filter(tryout_package=package).exists():
            messages.error(request, f'Paket "{package.package_name}" tidak dapat dihapus karena sudah digunakan oleh siswa.')
        else:
            package_name = package.package_name
            package.delete()
            messages.success(request, f'Paket "{package_name}" berhasil dihapus!')
        
        return redirect('admin_package_list')
    
    context = {
        'package': package,
        'tests_count': Test.objects.filter(tryout_package=package).count()
    }
    
    return render(request, 'admin/package/package_confirm_delete.html', context)


@admin_or_operator_required
def api_category_question_count(request, category_id):
    """Return JSON with question count for a category (for AJAX)"""
    try:
        category = Category.objects.get(id=category_id)
        return JsonResponse({'count': category.get_question_count()})
    except Category.DoesNotExist:
        return JsonResponse({'count': 0}, status=404)

@admin_or_operator_required
def admin_package_detail(request, package_id):
    """View package details and statistics"""
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    # Get package statistics
    package_tests = Test.objects.filter(tryout_package=package, is_submitted=True)
    
    statistics = {
        'total_attempts': package_tests.count(),
        'average_score': package_tests.aggregate(avg_score=Avg('score'))['avg_score'] or 0,
        'highest_score': package_tests.aggregate(max_score=Max('score'))['max_score'] or 0,
        'pass_rate': 0
    }
    
    # Calculate pass rate (60% of 7000 = 4200)
    if statistics['total_attempts'] > 0:
        passed_tests = package_tests.filter(score__gte=4200).count()
        statistics['pass_rate'] = round((passed_tests / statistics['total_attempts']) * 100, 1)
    
    # Get recent test results
    recent_tests = package_tests.select_related('student').order_by('-date_taken')[:10]
    
    context = {
        'package': package,
        'statistics': statistics,
        'recent_tests': recent_tests,
        'category_breakdown': package.tryoutpackagecategory_set.all().order_by('order')
    }
    
    return render(request, 'admin/package/package_detail.html', context)


@login_required
@active_subscription_required
def take_package_test(request, package_id):
    """Start a tryout package test session"""
    from django.utils import timezone
    
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    # Check if package can be taken
    if not package.can_be_taken:
        messages.error(request, 'Paket tryout ini belum dapat diambil.')
        return redirect('tryout_list')
    
    # Check if there's an existing unsubmitted test for this package and user
    existing_test = Test.objects.filter(
        student=request.user,
        is_submitted=False,
        tryout_package=package
    ).first()
    
    if existing_test:
        # Continue existing test
        # Find the current question position
        answered_count = existing_test.answer_set.count()
        next_question = answered_count + 1
        
        # Get first category for redirection
        first_category = package.tryoutpackagecategory_set.first()
        if first_category:
            return redirect('take_package_test_question', 
                          package_id=package_id, 
                          question=next_question)
    
    # Allow forcing a new test via GET parameter (used when user explicitly clicks 'Mulai')
    force_new = request.GET.get('force_new') == '1'

    # If the user has JUST submitted a test for this package (e.g. clicked back after finishing),
    # avoid creating a new test immediately. Redirect to the latest submitted test results instead.
    # Only do this when not forcing a new test.
    if not force_new:
        try:
            recent_threshold = timezone.now() - timedelta(minutes=5)
            recent_test = Test.objects.filter(
                student=request.user,
                tryout_package=package,
                is_submitted=True,
                end_time__gte=recent_threshold
            ).order_by('-end_time').first()
            if recent_test:
                return redirect('test_results', test_id=recent_test.id)
        except Exception:
            # if something goes wrong (timedelta not available etc.), fall back to normal behavior
            pass

    # Create a new test instance for this package
    test = Test.objects.create(
        student=request.user,
        tryout_package=package,
        start_time=timezone.now(),
        time_limit=package.total_time
    )
    
    # Connect test to all categories in the package
    for package_category in package.tryoutpackagecategory_set.all():
        test.categories.add(package_category.category)
    
    messages.success(request, f'Tryout paket "{package.package_name}" dimulai.')
    
    # Redirect to first question
    return redirect('take_package_test_question', 
                   package_id=package_id, 
                   question=1)


@login_required
@active_subscription_required
def take_package_test_question(request, package_id, question):
    """Handle individual questions in package test"""
    from django.utils import timezone
    
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    # Get the current test for this package
    test = Test.objects.filter(
        student=request.user,
        is_submitted=False,
        tryout_package=package
    ).first()
    
    if not test:
        messages.error(request, 'Sesi tryout tidak ditemukan. Silakan mulai ulang.')
        return redirect('tryout_list')
    
    # Check if time is up
    if test.is_time_up():
        test.is_submitted = True
        test.end_time = timezone.now()
        test.calculate_score()
        test.save()
        messages.warning(request, 'Waktu tryout telah habis. Test otomatis disubmit.')
        return redirect('test_results', test_id=test.id)
    
    # Get all questions for this package in order
    all_questions = []
    for package_category in package.tryoutpackagecategory_set.all().order_by('order'):
        category_questions = list(Question.objects.filter(
            category=package_category.category
        ).order_by('id'))
        all_questions.extend(category_questions)
    
    # Validate question number
    if question < 1 or question > len(all_questions):
        messages.error(request, 'Nomor soal tidak valid.')
        return redirect('tryout_list')
    
    current_question = all_questions[question - 1]
    choices = current_question.choices.all()
    
    # Get previous answer if exists
    previous_answer = Answer.objects.filter(
        test=test,
        question=current_question
    ).first()
    
    # Get previous text answer if exists (for essay questions)
    previous_text_answer = previous_answer.text_answer if previous_answer and previous_answer.text_answer else ''
    
    # Update current question position in the test model
    test.current_question = question
    test.save(update_fields=['current_question'])
    
    if request.method == 'POST':
        choice_id = request.POST.get('choice')
        text_answer = request.POST.get('text_answer')
        action = request.POST.get('action')
        
        # Handle AJAX requests for saving answers
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Debug logging: record incoming POST attempts for troubleshooting
        print(f"[DEBUG] take_package_test_question POST - user={getattr(request.user, 'email', request.user)} package_id={package_id} question_index={question} choice_id={choice_id} text_answer={text_answer} is_ajax={is_ajax} test_id={getattr(test, 'id', None)}")

        if choice_id and current_question.is_multiple_choice():
            choice = get_object_or_404(Choice, id=choice_id, question=current_question)
            
            # Check for existing answers and clean up duplicates if any
            existing_answers = Answer.objects.filter(
                test=test,
                question=current_question
            )
            
            if existing_answers.count() > 1:
                # Keep the first answer and delete the rest
                first_answer = existing_answers.first()
                existing_answers.exclude(id=first_answer.id).delete()
                
                # Update the remaining answer
                first_answer.selected_choice = choice
                first_answer.text_answer = None  # Clear text answer for multiple choice
                first_answer.save()
                answer = first_answer
                created = False
            elif existing_answers.count() == 1:
                # Update existing single answer
                answer = existing_answers.first()
                answer.selected_choice = choice
                answer.text_answer = None  # Clear text answer for multiple choice
                answer.save()
                created = False
            else:
                # Create new answer
                answer = Answer.objects.create(
                    test=test,
                    question=current_question,
                    selected_choice=choice
                )
                created = True

            # Debug logging: report result of save
            try:
                print(f"[DEBUG] Multiple choice answer saved - test_id={test.id} question_id={current_question.id} answer_id={answer.id} created={created} selected_choice={getattr(answer.selected_choice, 'id', None)}")
            except Exception as _e:
                print(f"[DEBUG] Answer save - exception while logging: {_e}")

            # If this is AJAX, return JSON response
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Answer saved'})
                
        elif text_answer is not None and current_question.is_essay():
            # Handle essay answer
            existing_answers = Answer.objects.filter(
                test=test,
                question=current_question
            )
            
            if existing_answers.count() > 1:
                # Keep the first answer and delete the rest
                first_answer = existing_answers.first()
                existing_answers.exclude(id=first_answer.id).delete()
                
                # Update the remaining answer
                first_answer.text_answer = text_answer
                first_answer.selected_choice = None  # Clear selected choice for essay
                first_answer.save()
                answer = first_answer
                created = False
            elif existing_answers.count() == 1:
                # Update existing single answer
                answer = existing_answers.first()
                answer.text_answer = text_answer
                answer.selected_choice = None  # Clear selected choice for essay
                answer.save()
                created = False
            else:
                # Create new answer
                answer = Answer.objects.create(
                    test=test,
                    question=current_question,
                    text_answer=text_answer
                )
                created = True

            # Debug logging: report result of save
            try:
                print(f"[DEBUG] Essay answer saved - test_id={test.id} question_id={current_question.id} answer_id={answer.id} created={created} text_answer='{text_answer}'")
            except Exception as _e:
                print(f"[DEBUG] Essay answer save - exception while logging: {_e}")

            # If this is AJAX, return JSON response
            if is_ajax:
                return JsonResponse({'status': 'success', 'message': 'Essay answer saved'})
        
        # If not AJAX, handle navigation
        if not is_ajax:
            # Handle navigation
            if action == 'next' and question < len(all_questions):
                return redirect('take_package_test_question', 
                              package_id=package_id, 
                              question=question + 1)
            elif action == 'previous' and question > 1:
                return redirect('take_package_test_question', 
                              package_id=package_id, 
                              question=question - 1)
            elif action == 'submit':
                # Direct submit without confirmation page - let the modal handle it
                test.is_submitted = True
                test.end_time = timezone.now()
                test.calculate_score()
                test.save()
                messages.success(request, 'Tryout berhasil disubmit!')
                return redirect('test_results', test_id=test.id)
    
    # Calculate progress and answered questions
    answered_questions = Answer.objects.filter(test=test).count()
    answered_question_ids = set(Answer.objects.filter(test=test).values_list('question_id', flat=True))
    answered_question_numbers = []
    
    # Map question IDs to question numbers in the package
    for i, q in enumerate(all_questions):
        if q.id in answered_question_ids:
            answered_question_numbers.append(i + 1)
    
    progress = round((answered_questions / len(all_questions)) * 100, 1) if all_questions else 0
    unanswered_questions = len(all_questions) - answered_questions
    
    # Time remaining
    time_remaining = None
    if test.start_time and test.time_limit:
        from datetime import timedelta
        elapsed_time = timezone.now() - test.start_time
        total_time = timedelta(minutes=test.time_limit)
        time_remaining = total_time - elapsed_time
        
        if time_remaining.total_seconds() <= 0:
            time_remaining = timedelta(0)
    
    context = {
        'package': package,
        'test': test,
        'question': current_question,
        'choices': choices,
        'current_question_number': question,
        'total_questions': len(all_questions),
        'previous_answer': previous_answer,
        'previous_text_answer': previous_text_answer,
        'progress': progress,
        'answered_questions': answered_questions,
        'unanswered_questions': unanswered_questions,
        'answered_question_numbers': answered_question_numbers,
        'time_remaining': time_remaining,
        'can_go_previous': question > 1,
        'can_go_next': question < len(all_questions),
        'is_last_question': question == len(all_questions),
        'remaining_time': test.get_remaining_time() if test.start_time else 0,
    'is_package': True,
    }
    # Build per-subtest metadata (start index and question count) for client-side navigation
    try:
        package_subtests = []
        running = 1
        for pc in package.tryoutpackagecategory_set.all().order_by('order'):
            qcount = Question.objects.filter(category=pc.category).count()
            package_subtests.append({
                'category_id': pc.category.id,
                'category_name': pc.category.category_name,
                'start': running,
                'count': qcount,
            })
            running += qcount
        context['package_subtests'] = package_subtests
    except Exception:
        context['package_subtests'] = []
    
    return render(request, 'students/tryouts/package_test_question.html', context)


@login_required
@active_subscription_required
def submit_package_test(request, package_id):
    """Submit package test and calculate results"""
    from django.utils import timezone
    
    package = get_object_or_404(TryoutPackage, id=package_id)
    
    # Get the current test for this package
    test = Test.objects.filter(
        student=request.user,
        is_submitted=False,
        tryout_package=package
    ).first()
    
    if not test:
        messages.error(request, 'Sesi tryout tidak ditemukan.')
        return redirect('tryout_list')
    
    # Only accept POST requests (direct submit, no confirmation page)
    if request.method == 'POST':
        # Submit the test
        test.is_submitted = True
        test.end_time = timezone.now()
        test.calculate_score()
        test.save()
        # Remove any session keys that reference categories in this package
        try:
            for cat in package.categories.all():
                sk = f'test_session_{cat.id}_{request.user.id}'
                if sk in request.session:
                    del request.session[sk]
        except Exception:
            pass

        # Also mark any other unsubmitted package tests for this student as submitted to avoid duplicates
        try:
            other_tests = Test.objects.filter(student=request.user, is_submitted=False, tryout_package=package).exclude(id=test.id)
            for ot in other_tests:
                ot.is_submitted = True
                ot.end_time = timezone.now()
                try:
                    ot.calculate_score()
                except Exception:
                    pass
                ot.save()
                # Remove session keys referencing those tests' categories as well
                for cat in ot.categories.all():
                    sk = f'test_session_{cat.id}_{request.user.id}'
                    if sk in request.session:
                        del request.session[sk]
        except Exception:
            pass

        messages.success(request, 'Tryout berhasil disubmit!')
        return redirect('test_results', test_id=test.id)
    
    # If GET request, redirect back to the test (no separate confirmation page)
    return redirect('take_package_test_question', package_id=package_id, question=1)


@csrf_exempt
def api_universities(request):
    """API endpoint untuk pencarian universitas (ajax search)"""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        # Normalize query untuk pencarian tier
        q_lower = q.lower().replace(' ', '')
        
        # Prioritized search results
        exact_tier_matches = []
        partial_matches = []
        name_location_matches = []
        
        # Check for exact tier matches first
        if q_lower == 'tier1' or q_lower == 'tier3':
            tier_value = q_lower
            exact_tier_matches = University.objects.filter(
                is_active=True, tier=tier_value
            ).order_by('name')
        elif q_lower == 'tier2':
            exact_tier_matches = University.objects.filter(
                is_active=True, tier='tier2'
            ).order_by('name')
        elif 'tier1' in q_lower or 'top' in q_lower:
            exact_tier_matches = University.objects.filter(
                is_active=True, tier='tier1'
            ).order_by('name')
        elif 'tier2' in q_lower or 'good' in q_lower:
            exact_tier_matches = University.objects.filter(
                is_active=True, tier='tier2'
            ).order_by('name')
        elif 'tier3' in q_lower or 'standard' in q_lower:
            exact_tier_matches = University.objects.filter(
                is_active=True, tier='tier3'
            ).order_by('name')
        
        # If we have exact tier matches, prioritize them
        if exact_tier_matches:
            # For exact tier search, show only that tier unless query is just "tier"
            if q_lower == 'tier':
                # Show all tiers when just searching "tier"
                partial_matches = University.objects.filter(
                    is_active=True, tier__icontains='tier'
                ).exclude(
                    id__in=[u.id for u in exact_tier_matches]
                ).order_by('tier', 'name')[:30]
            
            # Also include name/location matches for the query
            name_location_matches = University.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=q) | Q(location__icontains=q)
            ).exclude(
                id__in=[u.id for u in exact_tier_matches]
            ).order_by('name')[:20]
        else:
            # No tier match, search by name and location
            name_location_matches = University.objects.filter(
                is_active=True
            ).filter(
                Q(name__icontains=q) | Q(location__icontains=q)
            ).order_by('name')[:50]
        
        # Combine results with priority
        queryset = list(exact_tier_matches) + list(partial_matches) + list(name_location_matches)
        queryset = queryset[:50]  # Limit total results
    else:
        # Tanpa query, ambil semua universitas (untuk preload)
        queryset = University.objects.filter(is_active=True).order_by('tier', 'name')[:100]

    for uni in queryset:
        results.append({
            'id': uni.id,
            'name': uni.name,
            'tier': uni.tier,
            'tier_display': uni.get_tier_display(),
            'minimum_utbk_score': uni.minimum_utbk_score,
            'location': uni.location,
        })
    
    # Debug logging
    print(f"API Search - Query: '{q}', Results: {len(results)}")
    if results:
        print(f"First 3 results: {[r['name'] + ' (' + r['tier'] + ')' for r in results[:3]]}")
    
    return JsonResponse({'results': results})


@csrf_exempt
@require_POST
def image_upload(request):
    """Handle image uploads for Quill.js editor"""
    try:
        if 'upload' not in request.FILES:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        uploaded_file = request.FILES['upload']
        
        # Validate file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return JsonResponse({'error': 'Invalid file type'}, status=400)
        
        # Validate file size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            return JsonResponse({'error': 'File too large (max 5MB)'}, status=400)
        
        # Generate unique filename
        from .utils import generate_unique_filename
        filename = generate_unique_filename(uploaded_file.name)
        
        # Use VercelBlobStorage for Quill image uploads
        try:
            from .storage import VercelBlobStorage
            storage = VercelBlobStorage()
        except Exception:
            storage = default_storage
        
        # Save file using appropriate storage
        file_path = storage.save(f'uploads/{filename}', ContentFile(uploaded_file.read()))
        file_url = storage.url(file_path)
        
        return JsonResponse({'url': file_url})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

