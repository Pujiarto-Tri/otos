from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
import re
from django.conf import settings
import os
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from .utils import generate_unique_filename

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True, verbose_name='Phone Number')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Add a custom related name here
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",  # Add a custom related name here
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions"
    )
    
    def is_visitor(self):
        """Check if user has visitor role"""
        return self.role and self.role.role_name == 'Visitor'
    
    def is_student(self):
        """Check if user has student role"""
        return self.role and self.role.role_name == 'Student'
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role and self.role.role_name == 'Admin'
    
    def is_operator(self):
        """Check if user has operator role"""
        return self.role and self.role.role_name == 'Operator'
    
    def is_teacher(self):
        """Check if user has teacher role"""
        return self.role and self.role.role_name == 'Teacher'
    
    def has_active_subscription(self):
        """Check if user has active subscription"""
        try:
            subscription = self.subscription
            # Subscription aktif jika: is_active=True DAN belum expired
            return subscription.is_active and not subscription.is_expired()
        except UserSubscription.DoesNotExist:
            return False
    
    def can_access_tryouts(self):
        """Check if user can access tryout features"""
        return self.is_student() and self.has_active_subscription()
    
    def get_subscription_status(self):
        """Get detailed subscription status"""
        try:
            subscription = self.subscription
            
            # Jika subscription di-deactivate oleh admin
            if not subscription.is_active:
                return {
                    'status': 'deactivated',
                    'message': 'Langganan Anda telah dinonaktifkan oleh admin',
                    'end_date': subscription.end_date,
                    'package': subscription.package
                }
            # Jika subscription expired berdasarkan tanggal
            elif subscription.is_expired():
                return {
                    'status': 'expired',
                    'message': 'Langganan Anda telah berakhir',
                    'end_date': subscription.end_date,
                    'package': subscription.package
                }
            # Jika akan expired dalam 7 hari
            elif subscription.days_remaining() <= 7:
                return {
                    'status': 'expiring_soon',
                    'message': f'Langganan akan berakhir dalam {subscription.days_remaining()} hari',
                    'end_date': subscription.end_date,
                    'package': subscription.package
                }
            # Jika masih aktif
            else:
                return {
                    'status': 'active',
                    'message': f'Langganan aktif hingga {subscription.end_date.strftime("%d %B %Y")}',
                    'end_date': subscription.end_date,
                    'package': subscription.package
                }
        except UserSubscription.DoesNotExist:
            return {
                'status': 'none',
                'message': 'Tidak ada langganan aktif',
                'end_date': None,
                'package': None
            }
    
    def has_university_target(self):
        """Check if user has set any university target (utama, aman, atau cadangan)"""
        try:
            if not hasattr(self, 'university_target'):
                return False
            ut = self.university_target
            return bool(ut.primary_university or ut.backup_university or ut.secondary_university)
        except:
            return False
    
    def get_university_target(self):
        """Get user's university targets"""
        try:
            return self.university_target
        except UniversityTarget.DoesNotExist:
            return None

class Role(models.Model):
    role_name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.role_name

class Category(models.Model):
    SCORING_METHODS = [
        ('default', 'Default (100/jumlah soal)'),
        ('custom', 'Custom (nilai per soal)'),
        ('utbk', 'UTBK (difficulty-based)'),
    ]
    
    category_name = models.CharField(max_length=200)
    time_limit = models.IntegerField(default=60, help_text="Time limit in minutes (default: 60 minutes)")
    scoring_method = models.CharField(max_length=10, choices=SCORING_METHODS, default='default')
    passing_score = models.FloatField(default=75.0, help_text="Minimum score required to pass (0-100)")
    # Optional owner (teacher) who created/maintains this category
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_created',
        help_text='Teacher who created this category'
    )
    # Multiple teachers can be assigned to a category
    teachers = models.ManyToManyField(
        User,
        related_name='teaching_categories',
        blank=True,
        help_text='Additional teachers assigned to this category'
    )
    
    def __str__(self):
        return self.category_name
    
    def get_question_count(self):
        """Get total number of questions in this category"""
        return self.question_set.count()
    
    def get_difficulty_level(self):
        """Get difficulty level based on pass rate statistics"""
        pass_rate = self.get_pass_rate()
        
        if pass_rate is None:
            return "Belum Ada Data"
        elif pass_rate >= 60:
            return "Mudah"
        elif pass_rate >= 40:
            return "Sedang"
        else:
            return "Sulit"
    
    def get_difficulty_color(self):
        """Get color class for difficulty badge"""
        difficulty = self.get_difficulty_level()
        if difficulty == "Mudah":
            return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
        elif difficulty == "Sedang":
            return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
        elif difficulty == "Sulit":
            return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
        else:
            return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300"
    
    def get_pass_rate(self):
        """Calculate pass rate percentage for this category"""
        # Get all submitted tests for this category
        completed_tests = Test.objects.filter(
            categories=self,
            is_submitted=True
        )
        
        if not completed_tests.exists():
            return None
        
        total_tests = completed_tests.count()
        passed_tests = completed_tests.filter(score__gte=self.passing_score).count()
        
        return round((passed_tests / total_tests) * 100, 1)
    
    def get_test_statistics(self):
        """Get comprehensive test statistics for this category"""
        completed_tests = Test.objects.filter(
            categories=self,
            is_submitted=True
        )
        
        if not completed_tests.exists():
            return {
                'total_tests': 0,
                'total_students': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'pass_rate': None,
                'average_score': None
            }
        
        total_tests = completed_tests.count()
        
        # Count unique students who took the test
        total_students = completed_tests.values('student').distinct().count()
        
        passed_tests = completed_tests.filter(score__gte=self.passing_score).count()
        failed_tests = total_tests - passed_tests
        pass_rate = round((passed_tests / total_tests) * 100, 1)
        
        # Calculate average score per this category
        total_score = 0
        for test in completed_tests:
            # If test is a package test, compute this category's contribution
            if test.tryout_package:
                pkg_cat = test.tryout_package.tryoutpackagecategory_set.filter(category=self).first()
                if not pkg_cat:
                    # Category not part of the package for this test — try to compute from answers if any
                    category_answers = test.answers.filter(question__category=self)
                    if category_answers.exists():
                        correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
                        total_questions = category_answers.count()
                        if total_questions:
                            # Fallback: scale to 100 (or to package unit if unknown) — use percentage * 100
                            total_score += (correct_answers / total_questions) * 100
                    # otherwise skip
                    continue

                # Compute contribution based on the answers for this category
                category_answers = test.answers.filter(question__category=self)
                if category_answers.exists():
                    correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
                    total_questions = category_answers.count()
                    category_score_percentage = (correct_answers / total_questions) if total_questions else 0
                    category_contribution = category_score_percentage * pkg_cat.max_score
                    total_score += category_contribution
                else:
                    # No answers for this category in this package test — treat as 0
                    total_score += 0
            else:
                # Non-package test: score field already represents this category
                total_score += test.score

        average_score = round(total_score / total_tests, 1)

        # Calculate average completion time (in minutes) for submitted tests
        durations_seconds = []
        for t in completed_tests:
            if t.start_time and t.end_time:
                try:
                    delta = t.end_time - t.start_time
                    seconds = delta.total_seconds()
                    if seconds and seconds > 0:
                        durations_seconds.append(seconds)
                except Exception:
                    # Skip any problematic timestamps
                    continue

        average_completion_minutes = None
        if durations_seconds:
            average_completion_minutes = round((sum(durations_seconds) / len(durations_seconds)) / 60, 1)

        return {
            'total_tests': total_tests,
            'total_students': total_students,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': pass_rate,
            'average_score': average_score,
            'average_completion_minutes': average_completion_minutes
        }
    
    def get_passing_score(self):
        """Get passing score for this category"""
        return f"{self.passing_score}%"
    
    def is_passing_score(self, score):
        """Check if the given score meets the passing requirement"""
        return score >= self.passing_score
    
    def get_scoring_method_display_name(self):
        """Get user-friendly scoring method name"""
        method_names = {
            'default': 'Penilaian Standar',
            'custom': 'Penilaian Berbobot',
            'utbk': 'Sistem UTBK'
        }
        return method_names.get(self.scoring_method, 'Penilaian Standar')
    
    def get_total_custom_points(self):
        """Calculate total points from custom question weights"""
        return sum(q.custom_weight for q in self.question_set.all())
    
    def is_custom_scoring_complete(self):
        """Check if custom scoring totals to 100"""
        if self.scoring_method == 'custom':
            return abs(self.get_total_custom_points() - 100) < 0.01
        return True

class TryoutPackage(models.Model):
    """Model for creating packages of multiple categories for UTBK simulation"""
    package_name = models.CharField(max_length=200, help_text="Nama paket tryout (contoh: UTBK Saintek 2025)")
    description = models.TextField(blank=True, help_text="Deskripsi paket tryout")
    is_active = models.BooleanField(default=True, help_text="Apakah paket ini aktif dan tersedia untuk siswa")
    total_time = models.IntegerField(help_text="Total waktu pengerjaan dalam menit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Categories in this package
    categories = models.ManyToManyField(Category, through='TryoutPackageCategory')
    
    def __str__(self):
        return self.package_name
    
    def get_total_questions(self):
        """Get total number of questions in this package"""
        return sum([pc.question_count for pc in self.tryoutpackagecategory_set.all()])
    
    def get_total_max_score(self):
        """Get total maximum score (should be 1000 for UTBK)"""
        return sum([pc.max_score for pc in self.tryoutpackagecategory_set.all()])
    
    def is_scoring_complete(self):
        """Check if total max score equals 1000"""
        return abs(self.get_total_max_score() - 1000) < 0.01
    
    def get_category_composition(self):
        """Get formatted string of category composition"""
        compositions = []
        for pc in self.tryoutpackagecategory_set.all():
            compositions.append(f"{pc.category.category_name} ({pc.question_count} soal, {pc.max_score} poin)")
        return " | ".join(compositions)
    
    def can_be_taken(self):
        """Check if package can be taken by students"""
        return (
            self.is_active and 
            self.is_scoring_complete() and 
            self.get_total_questions() > 0 and
            all(pc.category.get_question_count() >= pc.question_count for pc in self.tryoutpackagecategory_set.all())
        )

class TryoutPackageCategory(models.Model):
    """Through model for TryoutPackage and Category relationship with scoring configuration"""
    package = models.ForeignKey(TryoutPackage, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    question_count = models.PositiveIntegerField(help_text="Jumlah soal dari kategori ini dalam paket")
    max_score = models.FloatField(help_text="Skor maksimum untuk kategori ini (kontribusi ke total 1000)")
    order = models.PositiveIntegerField(default=1, help_text="Urutan kategori dalam paket")
    
    class Meta:
        unique_together = ('package', 'category')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.package.package_name} - {self.category.category_name}"
    
    def get_score_per_question(self):
        """Get score per question for this category in the package"""
        if self.question_count > 0:
            return self.max_score / self.question_count
        return 0
    
    def validate_question_count(self):
        """Validate if category has enough questions"""
        available_questions = self.category.get_question_count()
        return available_questions >= self.question_count

class Question(models.Model):
    question_text = CKEditor5Field('Text', config_name='extends')
    pub_date = models.DateTimeField('date published')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    custom_weight = models.FloatField(default=0, help_text="Custom weight for scoring (0-100)")
    difficulty_coefficient = models.FloatField(default=1.0, help_text="UTBK difficulty coefficient (auto-calculated)")

    def delete_media_files(self):
        """Delete associated media files without calling delete()"""
        pattern = r'src="([^"]+)"'
        matches = re.findall(pattern, self.question_text)
        
        for match in matches:
            if match.startswith(settings.MEDIA_URL):
                file_path = match[len(settings.MEDIA_URL):]
                absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                if os.path.exists(absolute_path):
                    try:
                        os.remove(absolute_path)
                    except (OSError, PermissionError):
                        pass  # Handle file deletion errors gracefully

    def __str__(self):
        return self.question_text

    def delete(self, *args, **kwargs):
        self.delete_media_files()
        for choice in self.choices.all():
            choice.delete_media_files()
        super().delete(*args, **kwargs)

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = CKEditor5Field('Text', config_name='extends')
    is_correct = models.BooleanField(default=False)

    def delete_media_files(self):
        """Delete associated media files without calling delete()"""
        pattern = r'src="([^"]+)"'
        matches = re.findall(pattern, self.choice_text)
        
        for match in matches:
            if match.startswith(settings.MEDIA_URL):
                file_path = match[len(settings.MEDIA_URL):]
                absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
                
                if os.path.exists(absolute_path):
                    try:
                        os.remove(absolute_path)
                    except (OSError, PermissionError):
                        pass

    def delete(self, *args, **kwargs):
        self.delete_media_files()
        super().delete(*args, **kwargs)

class Test(models.Model):
    student = models.ForeignKey(
        User, on_delete=models.CASCADE,
        limit_choices_to={'userprofile__role__role_name': 'Student'},
        related_name="tests"
    )
    score = models.FloatField(default=0, verbose_name="Score")
    date_taken = models.DateTimeField(auto_now_add=True, verbose_name="Date Taken")
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Test Start Time")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Test End Time")
    time_limit = models.IntegerField(default=60, verbose_name="Time Limit (minutes)")
    is_submitted = models.BooleanField(default=False, verbose_name="Is Submitted")
    categories = models.ManyToManyField(Category, related_name="tests", blank=True)
    
    # Add support for tryout packages
    tryout_package = models.ForeignKey(
        TryoutPackage, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Paket tryout yang digunakan (jika ada)"
    )
    
    # Track current question position
    current_question = models.IntegerField(default=1, verbose_name="Current Question Index")

    def __str__(self):
        return f"Test by {self.student.username} on {self.date_taken}"

    def calculate_score(self):
        """Calculate score based on category scoring method or package scoring"""
        answers = self.answers.all()
        if not answers.exists():
            self.score = 0
            self.save()
            return

        # If this is a package test, use package scoring
        if self.tryout_package:
            self._calculate_package_score()
        else:
            # Single category test
            category = answers.first().question.category
            
            if category.scoring_method == 'default':
                self._calculate_default_score()
            elif category.scoring_method == 'custom':
                self._calculate_custom_score()
            elif category.scoring_method == 'utbk':
                self._calculate_utbk_score()
        
        self.save()
    
    def _calculate_package_score(self):
        """Calculate score for package-based test with weighted categories"""
        total_score = 0
        
        # Calculate score for each category in the package
        for package_category in self.tryout_package.tryoutpackagecategory_set.all():
            category = package_category.category
            
            # Get answers for this specific category
            category_answers = self.answers.filter(question__category=category)
            if not category_answers.exists():
                continue
            
            # Calculate correct answers for this category
            correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
            total_questions = category_answers.count()
            
            if total_questions > 0:
                # Calculate score for this category based on package configuration
                category_score_percentage = correct_answers / total_questions
                category_contribution = category_score_percentage * package_category.max_score
                total_score += category_contribution
        
        self.score = total_score
    
    def _calculate_default_score(self):
        """Default scoring: 100 points divided equally among questions"""
        total_answered = self.answers.count()
        if total_answered == 0:
            self.score = 0
        else:
            correct_answers = self.answers.filter(selected_choice__is_correct=True).count()
            self.score = (correct_answers / total_answered) * 100
    
    def _calculate_custom_score(self):
        """Custom scoring: Each question has custom weight"""
        total_score = 0
        for answer in self.answers.all():
            if answer.selected_choice.is_correct:
                total_score += answer.question.custom_weight
        self.score = total_score
    
    def _calculate_utbk_score(self):
        """UTBK scoring: Difficulty-based scoring with 1000 max score"""
        total_score = 0
        total_possible_score = 0
        
        for answer in self.answers.all():
            question_weight = answer.question.difficulty_coefficient
            total_possible_score += question_weight
            
            if answer.selected_choice.is_correct:
                total_score += question_weight
        
        if total_possible_score > 0:
            # Normalize to 1000 scale for UTBK
            self.score = (total_score / total_possible_score) * 1000
        else:
            self.score = 0
        
    def is_time_up(self):
        """Check if test time is up"""
        if not self.start_time:
            return False
        from django.utils import timezone
        elapsed_time = timezone.now() - self.start_time
        return elapsed_time.total_seconds() > (self.time_limit * 60)
        
    def get_remaining_time(self):
        """Get remaining time in seconds"""
        if not self.start_time:
            return self.time_limit * 60
        from django.utils import timezone
        elapsed_time = timezone.now() - self.start_time
        remaining_seconds = (self.time_limit * 60) - elapsed_time.total_seconds()
        return max(0, int(remaining_seconds))
    
    def get_current_question_index(self):
        """Get the current question index based on answered questions"""
        if self.tryout_package:
            # For package tests, get all questions from all categories
            all_questions = []
            for package_category in self.tryout_package.tryoutpackagecategory_set.all():
                category_questions = list(package_category.category.question_set.all())
                all_questions.extend(category_questions)
            
            # Find first unanswered question
            answered_question_ids = set(self.answers.values_list('question_id', flat=True))
            for i, question in enumerate(all_questions):
                if question.id not in answered_question_ids:
                    return i + 1  # 1-based index
            
            # If all questions answered, return last question
            return len(all_questions) if all_questions else 1
        else:
            # For single category tests
            category = self.categories.first()
            if not category:
                return 1
            
            questions = list(category.question_set.all())
            answered_question_ids = set(self.answers.values_list('question_id', flat=True))
            
            for i, question in enumerate(questions):
                if question.id not in answered_question_ids:
                    return i + 1  # 1-based index
            
            # If all questions answered, return last question
            return len(questions) if questions else 1
    
    def is_passed(self):
        """Check if test score meets the category's passing requirement"""
        if self.tryout_package:
            # For package tests, use 60% of 1000 as passing score
            return self.score >= 600
        
        answers = self.answers.all()
        if not answers.exists():
            return False
        
        # Get the category from the first answer (all questions in a test should be from same category)
        category = answers.first().question.category
        return category.is_passing_score(self.score)
    
    def get_package_score_breakdown(self):
        """Get detailed score breakdown for package tests"""
        if not self.tryout_package:
            return None
        
        breakdown = []
        for package_category in self.tryout_package.tryoutpackagecategory_set.all():
            category = package_category.category
            category_answers = self.answers.filter(question__category=category)
            
            if category_answers.exists():
                correct_answers = category_answers.filter(selected_choice__is_correct=True).count()
                total_questions = category_answers.count()
                score_percentage = correct_answers / total_questions if total_questions > 0 else 0
                category_score = score_percentage * package_category.max_score
                
                breakdown.append({
                    'category_name': category.category_name,
                    'correct_answers': correct_answers,
                    'total_questions': total_questions,
                    'max_score': package_category.max_score,
                    'achieved_score': round(category_score, 1),
                    'percentage': round(score_percentage * 100, 1)
                })
        
        return breakdown
    
    def is_package_test(self):
        """Check if this is a package test"""
        return self.tryout_package is not None
    
    def get_pass_status(self):
        """Get pass/fail status with color for display"""
        if self.is_passed():
            return {'status': 'LULUS', 'color': 'green'}
        else:
            return {'status': 'TIDAK LULUS', 'color': 'red'}
    
    def get_university_recommendations(self):
        """Get university recommendations based on test score. Target universitas akan selalu ditampilkan, plus saran universitas hanya jika ada target yang tidak memenuhi."""
        # Only for UTBK scoring method
        category = self.categories.first()
        if not category or category.scoring_method != 'utbk':
            return []
        
        # Get user's university targets
        try:
            user_targets = self.student.university_target
            target_recs = user_targets.get_recommendations_for_score(self.score)
            
            # Tambahkan informasi meets_minimum untuk setiap target
            for rec in target_recs:
                rec['meets_minimum'] = self.score >= rec['university'].minimum_utbk_score
                rec['achievement_percentage'] = round((self.score / rec['university'].minimum_utbk_score) * 100, 1) if rec['university'].minimum_utbk_score > 0 else 0
            
            # Cek apakah ada target yang tidak memenuhi syarat
            unmet_targets = [rec for rec in target_recs if not rec['meets_minimum']]
            
            # Jika semua target sudah memenuhi, tidak perlu rekomendasi
            suggestions = []
            if unmet_targets:
                target_ids = [rec['university'].id for rec in target_recs]
                from .models import University
                
                # Kumpulkan tier dari target yang tidak terpenuhi untuk menentukan rekomendasi
                unmet_tiers = list(set([rec['university'].tier for rec in unmet_targets]))
                
                # Prioritas rekomendasi berdasarkan tier target yang tidak terpenuhi
                # Mulai dari tier yang sama, lalu tier di bawahnya
                suggested_tiers = []
                for tier in ['tier1', 'tier2', 'tier3']:
                    if tier in unmet_tiers:
                        # Untuk tier yang tidak terpenuhi, rekomendasikan:
                        if tier == 'tier1':
                            # Jika tier 1 tidak terpenuhi → coba tier 1 lain dulu, lalu tier 2
                            suggested_tiers.extend(['tier1', 'tier2'])
                        elif tier == 'tier2':
                            # Jika tier 2 tidak terpenuhi → coba tier 2 lain dulu, lalu tier 3
                            suggested_tiers.extend(['tier2', 'tier3'])
                        else:
                            # Jika tier 3 tidak terpenuhi → coba tier 3 lain
                            suggested_tiers.append('tier3')
                
                # Hapus duplikat dan urutkan
                suggested_tiers = list(dict.fromkeys(suggested_tiers))  # Remove duplicates while preserving order
                
                # Cari universitas yang memenuhi syarat (skor >= minimum) dari tier yang disarankan
                suggestions_qs = University.objects.filter(
                    is_active=True, 
                    tier__in=suggested_tiers,
                    minimum_utbk_score__lte=self.score
                ).exclude(id__in=target_ids).order_by('tier', 'minimum_utbk_score')[:3]
                
                for uni in suggestions_qs:
                    rec = uni.get_recommendation_for_score(self.score)
                    suggestions.append({
                        'university': uni,
                        'target_type': 'suggested',
                        'target_label': f'Rekomendasi {uni.get_tier_display_short()}',
                        'recommendation': rec,
                        'achievement_percentage': round((self.score / uni.minimum_utbk_score) * 100, 1) if uni.minimum_utbk_score > 0 else 0,
                        'meets_minimum': self.score >= uni.minimum_utbk_score
                    })
                
                # Jika tidak ada universitas yang memenuhi, tampilkan yang paling mendekati (sebagai motivasi)
                if not suggestions and suggested_tiers:
                    fallback_qs = University.objects.filter(
                        is_active=True,
                        tier__in=suggested_tiers
                    ).exclude(id__in=target_ids).order_by('minimum_utbk_score')[:2]
                    
                    for uni in fallback_qs:
                        rec = uni.get_recommendation_for_score(self.score)
                        suggestions.append({
                            'university': uni,
                            'target_type': 'suggested',
                            'target_label': f'Opsi {uni.get_tier_display_short()}',
                            'recommendation': rec,
                            'achievement_percentage': round((self.score / uni.minimum_utbk_score) * 100, 1) if uni.minimum_utbk_score > 0 else 0,
                            'meets_minimum': self.score >= uni.minimum_utbk_score
                        })
            
            # Return target universitas + saran universitas (hanya jika ada target yang tidak terpenuhi)
            return list(target_recs) + suggestions
            
        except Exception as e:
            # Jika user belum set target, berikan saran universitas yang sesuai dengan skor
            from .models import University
            suggestions = []
            
            # Cari universitas yang memenuhi dari tier 3 dulu (paling mudah), lalu tier 2, lalu tier 1
            for tier in ['tier3', 'tier2', 'tier1']:
                suggestions_qs = University.objects.filter(
                    is_active=True, 
                    tier=tier,
                    minimum_utbk_score__lte=self.score
                ).order_by('minimum_utbk_score')[:2]
                
                for uni in suggestions_qs:
                    rec = uni.get_recommendation_for_score(self.score)
                    suggestions.append({
                        'university': uni,
                        'target_type': 'suggested',
                        'target_label': f'Rekomendasi {uni.get_tier_display_short()}',
                        'recommendation': rec,
                        'achievement_percentage': round((self.score / uni.minimum_utbk_score) * 100, 1) if uni.minimum_utbk_score > 0 else 0,
                        'meets_minimum': self.score >= uni.minimum_utbk_score
                    })
                
                # Batasi maksimal 3 rekomendasi
                if len(suggestions) >= 3:
                    break
            
            return suggestions[:3]
    
    def get_score_analysis(self):
        """Get detailed score analysis for UTBK tests"""
        category = self.categories.first()
        if not category or category.scoring_method != 'utbk':
            return None
        
        return {
            'raw_score': self.score,
            'max_score': 1000,
            'percentage': (self.score / 1000) * 100,
            'grade': self._get_utbk_grade(),
            'interpretation': self._get_score_interpretation()
        }
    
    def _get_utbk_grade(self):
        """Get letter grade based on UTBK score"""
        if self.score >= 800:
            return {'grade': 'A', 'color': 'green'}
        elif self.score >= 700:
            return {'grade': 'B+', 'color': 'blue'}
        elif self.score >= 600:
            return {'grade': 'B', 'color': 'blue'}
        elif self.score >= 500:
            return {'grade': 'C+', 'color': 'yellow'}
        elif self.score >= 400:
            return {'grade': 'C', 'color': 'orange'}
        else:
            return {'grade': 'D', 'color': 'red'}
    
    def _get_score_interpretation(self):
        """Get interpretation of the score"""
        if self.score >= 800:
            return "Excellent! Nilai sangat tinggi untuk universitas top."
        elif self.score >= 700:
            return "Very Good! Nilai tinggi untuk universitas favorit."
        elif self.score >= 600:
            return "Good! Nilai baik untuk sebagian besar universitas."
        elif self.score >= 500:
            return "Fair. Perlu peningkatan untuk universitas favorit."
        elif self.score >= 400:
            return "Below Average. Perlu banyak latihan tambahan."
        else:
            return "Poor. Perlu fokus belajar yang intensif."
    
    @classmethod
    def update_utbk_difficulty_coefficients(cls, category_id):
        """Update UTBK difficulty coefficients for all questions in a category"""
        from django.db.models import Count, F
        
        # Get all questions in the category with answer statistics
        questions = Question.objects.filter(category_id=category_id).annotate(
            total_answers=Count('answer'),
            correct_answers=Count('answer', filter=models.Q(answer__selected_choice__is_correct=True))
        ).filter(total_answers__gt=0)
        
        if not questions.exists():
            return
        
        # Calculate success rates
        question_stats = []
        for question in questions:
            success_rate = question.correct_answers / question.total_answers if question.total_answers > 0 else 0
            question_stats.append({
                'question': question,
                'success_rate': success_rate,
                'difficulty': 1 - success_rate  # Higher difficulty = lower success rate
            })
        
        # Sort by difficulty (hardest first)
        question_stats.sort(key=lambda x: x['difficulty'], reverse=True)
        
        # Assign coefficients based on difficulty ranking
        total_questions = len(question_stats)
        total_coefficient = total_questions  # Base coefficient sum
        
        for i, stat in enumerate(question_stats):
            # More difficult questions get higher coefficients
            # Linear distribution from 1.5 (hardest) to 0.5 (easiest)
            coefficient = 1.5 - (i / (total_questions - 1)) if total_questions > 1 else 1.0
            stat['question'].difficulty_coefficient = coefficient
            stat['question'].save()
        
        # Normalize coefficients so total equals 1000 when all questions answered correctly
        current_total = sum(q.difficulty_coefficient for q in questions)
        if current_total > 0:
            normalization_factor = 1000 / current_total
            for question in questions:
                question.difficulty_coefficient *= normalization_factor
                question.save()

class Answer(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    def __str__(self):
        return f"Answer by {self.test.student.username} for {self.question.question_text}"

@receiver(pre_delete, sender=Question)
def question_pre_delete(sender, instance, **kwargs):
    """Handle file deletion before the question is deleted"""
    instance.delete_media_files()

@receiver(pre_delete, sender=Choice)
def choice_pre_delete(sender, instance, **kwargs):
    """Handle file deletion before the choice is deleted"""
    instance.delete_media_files()


class MessageThread(models.Model):
    """Model untuk thread pesan antara siswa dan guru/admin"""
    THREAD_TYPES = [
        ('academic', 'Pertanyaan Materi'),
        ('technical', 'Masalah Teknis/Aplikasi'),
        ('report', 'Pelaporan Masalah'),
        ('general', 'Umum'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Terbuka'),
        ('pending', 'Menunggu Respons'),
        ('resolved', 'Selesai'),
        ('closed', 'Ditutup'),
    ]
    
    title = models.CharField(max_length=200, help_text="Judul thread pesan")
    thread_type = models.CharField(max_length=20, choices=THREAD_TYPES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    # Participants
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_threads')
    teacher_or_admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='handled_threads', 
                                       help_text="Guru atau admin yang menangani")
    
    # Optional: Category untuk pertanyaan materi
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                               help_text="Kategori materi (untuk pertanyaan akademik)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Priority level
    priority = models.CharField(max_length=10, choices=[
        ('low', 'Rendah'),
        ('normal', 'Normal'),
        ('high', 'Tinggi'),
        ('urgent', 'Mendesak')
    ], default='normal')
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = "Thread Pesan"
        verbose_name_plural = "Thread Pesan"
    
    def __str__(self):
        return f"{self.title} - {self.student.username}"
    
    def get_last_message(self):
        """Ambil pesan terakhir dalam thread"""
        return self.messages.last()
    
    def get_unread_count_for_user(self, user):
        """Hitung pesan yang belum dibaca oleh user tertentu"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def mark_as_read_for_user(self, user):
        """Tandai semua pesan sebagai sudah dibaca untuk user tertentu"""
        self.messages.exclude(sender=user).update(is_read=True)
    
    def get_participants(self):
        """Ambil semua participant dalam thread"""
        participants = [self.student]
        if self.teacher_or_admin:
            participants.append(self.teacher_or_admin)
        return participants


class Message(models.Model):
    """Model untuk pesan individual dalam thread"""
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(help_text="Isi pesan")
    
    # Optional attachment
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True,
                                help_text="File lampiran (opsional)")
    
    # Status
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = "Pesan"
        verbose_name_plural = "Pesan"
    
    def __str__(self):
        return f"Pesan dari {self.sender.username} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
    
    def save(self, *args, **kwargs):
        # Update last activity di thread ketika ada pesan baru
        if not self.pk:  # Only for new messages
            super().save(*args, **kwargs)
            self.thread.last_activity = self.created_at
            self.thread.save()
        else:
            super().save(*args, **kwargs)
    
    def delete_attachment(self):
        """Hapus file attachment jika ada"""
        if self.attachment:
            if os.path.isfile(self.attachment.path):
                os.remove(self.attachment.path)


@receiver(pre_delete, sender=Message)
def message_pre_delete(sender, instance, **kwargs):
    """Handle file deletion sebelum message dihapus"""
    instance.delete_attachment()


# ======================= SUBSCRIPTION & PAYMENT MODELS =======================

class PaymentMethod(models.Model):
    """Model untuk metode pembayaran"""
    PAYMENT_TYPES = [
        ('bank', 'Transfer Bank'),
        ('ewallet', 'E-Wallet'),
        ('other', 'Lainnya'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nama Metode Pembayaran")
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default='bank', verbose_name="Jenis Pembayaran")
    account_number = models.CharField(max_length=50, verbose_name="Nomor Rekening/Akun")
    account_name = models.CharField(max_length=100, verbose_name="Nama Pemilik Rekening")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Metode Pembayaran"
        verbose_name_plural = "Metode Pembayaran"
        ordering = ['payment_type', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.account_number} (a.n. {self.account_name})"
    
    def get_display_text(self):
        """Format display untuk dropdown"""
        return f"{self.name} - {self.account_number} (a.n. {self.account_name})"


class SubscriptionPackage(models.Model):
    """Model untuk paket berlangganan"""
    name = models.CharField(max_length=100, verbose_name="Nama Paket")
    # package_type removed (redundant)
    description = models.TextField(verbose_name="Deskripsi Paket")
    features = models.TextField(help_text="Fitur-fitur yang tersedia (satu per baris)", verbose_name="Fitur")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Harga")
    duration_days = models.IntegerField(verbose_name="Durasi (hari)")
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Featured package highlighting
    is_featured = models.BooleanField(default=False, verbose_name="Paket Unggulan")
    
    class Meta:
        verbose_name = "Paket Berlangganan"
        verbose_name_plural = "Paket Berlangganan"
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - Rp {self.price:,.0f}"
    
    def get_features_list(self):
        """Return features as a list"""
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]
    
    def get_price_formatted(self):
        """Return formatted price"""
        return f"Rp {self.price:,.0f}"


class PaymentProof(models.Model):
    """Model untuk bukti pembayaran yang diupload user"""
    STATUS_CHOICES = [
        ('pending', 'Menunggu Verifikasi'),
        ('approved', 'Disetujui'),
        ('rejected', 'Ditolak'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_proofs')
    package = models.ForeignKey(SubscriptionPackage, on_delete=models.CASCADE)
    proof_image = models.ImageField(upload_to='payment_proofs/', verbose_name="Bukti Pembayaran")
    payment_method = models.CharField(max_length=100, verbose_name="Metode Pembayaran")
    payment_date = models.DateTimeField(verbose_name="Tanggal Pembayaran")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Jumlah Bayar")
    notes = models.TextField(blank=True, null=True, verbose_name="Catatan")
    
    # Admin verification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  related_name='verified_payments', verbose_name="Diverifikasi oleh")
    verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Catatan Admin")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Bukti Pembayaran"
        verbose_name_plural = "Bukti Pembayaran"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.package.name} - {self.get_status_display()}"
    
    def delete_proof_image(self):
        """Delete proof image file"""
        if self.proof_image:
            if os.path.isfile(self.proof_image.path):
                os.remove(self.proof_image.path)


class UserSubscription(models.Model):
    """Model untuk subscription aktif user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    package = models.ForeignKey(SubscriptionPackage, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    payment_proof = models.ForeignKey(PaymentProof, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Auto expiry tracking
    auto_downgrade_processed = models.BooleanField(default=False, help_text="Apakah downgrade otomatis sudah diproses")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Subscription User"
        verbose_name_plural = "Subscription User"
        ordering = ['-end_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.package.name} (expires: {self.end_date.strftime('%Y-%m-%d')})"
    
    def is_expired(self):
        """Check if subscription is expired"""
        from django.utils import timezone
        return timezone.now() > self.end_date
    
    def days_remaining(self):
        """Get days remaining in subscription"""
        from django.utils import timezone
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return delta.days
    
    def extend_subscription(self, days):
        """Extend subscription by specified days"""
        from django.utils import timezone
        if self.is_expired():
            self.end_date = timezone.now() + timezone.timedelta(days=days)
        else:
            self.end_date = self.end_date + timezone.timedelta(days=days)
        self.auto_downgrade_processed = False
        self.save()


@receiver(pre_delete, sender=PaymentProof)
def payment_proof_pre_delete(sender, instance, **kwargs):
    """Handle file deletion sebelum PaymentProof dihapus"""
    instance.delete_proof_image()


# ======================= UNIVERSITY & TARGET MODELS =======================

class University(models.Model):
    """Model untuk data universitas dan passing grade"""
    name = models.CharField(max_length=200, verbose_name="Nama Universitas")
    location = models.CharField(max_length=100, verbose_name="Lokasi")
    website = models.URLField(blank=True, null=True, verbose_name="Website")
    description = models.TextField(blank=True, null=True, verbose_name="Deskripsi")
    
    # UTBK minimum scores for different categories
    minimum_utbk_score = models.IntegerField(
        default=400, 
        verbose_name="Nilai UTBK Minimum (Aman)",
        help_text="Nilai minimum UTBK yang aman untuk masuk universitas ini (0-1000)"
    )
    
    # University rank/tier for sorting
    tier = models.CharField(max_length=20, choices=[
        ('tier1', 'Tier 1 (Top Universities)'),
        ('tier2', 'Tier 2 (Good Universities)'),
        ('tier3', 'Tier 3 (Standard Universities)'),
    ], default='tier3', verbose_name="Tingkatan")
    
    is_active = models.BooleanField(default=True, verbose_name="Aktif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Universitas"
        verbose_name_plural = "Universitas"
        ordering = ['tier', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.location}"
    
    def get_tier_display_short(self):
        """Get short tier display"""
        tier_map = {
            'tier1': 'T1',
            'tier2': 'T2', 
            'tier3': 'T3'
        }
        return tier_map.get(self.tier, 'T3')
    
    def get_recommendation_for_score(self, utbk_score):
        """Get recommendation status based on UTBK score"""
        if utbk_score >= self.minimum_utbk_score + 100:
            return {
                'status': 'sangat_aman',
                'message': 'Sangat Aman',
                'color': 'green',
                'percentage': min(100, (utbk_score / self.minimum_utbk_score) * 100)
            }
        elif utbk_score >= self.minimum_utbk_score:
            return {
                'status': 'aman',
                'message': 'Aman',
                'color': 'blue',
                'percentage': (utbk_score / self.minimum_utbk_score) * 100
            }
        elif utbk_score >= self.minimum_utbk_score - 50:
            return {
                'status': 'kurang_aman',
                'message': 'Kurang Aman',
                'color': 'yellow',
                'percentage': (utbk_score / self.minimum_utbk_score) * 100
            }
        else:
            return {
                'status': 'tidak_aman',
                'message': 'Tidak Aman',
                'color': 'red',
                'percentage': (utbk_score / self.minimum_utbk_score) * 100
            }


class UniversityTarget(models.Model):
    """Model untuk target universitas student"""
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='university_target',
        limit_choices_to={'role__role_name': 'Student'}
    )
    primary_university = models.ForeignKey(
        University, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='primary_targets',
        verbose_name="Universitas Target Utama"
    )
    secondary_university = models.ForeignKey(
        University, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='secondary_targets',
        verbose_name="Universitas Target Cadangan"
    )
    backup_university = models.ForeignKey(
        University, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='backup_targets',
        verbose_name="Universitas Target Aman"
    )
    
    notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Catatan",
        help_text="Catatan personal tentang target universitas"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Target Universitas Student"
        verbose_name_plural = "Target Universitas Student"
    
    def __str__(self):
        return f"Target {self.user.email} - {self.primary_university}"
    
    def get_all_targets(self):
        """Get all university targets as list in order: utama, aman, cadangan"""
        targets = []
        if self.primary_university:
            targets.append({
                'university': self.primary_university,
                'type': 'primary',
                'label': 'Target Utama'
            })
        if self.backup_university:
            targets.append({
                'university': self.backup_university,
                'type': 'backup',
                'label': 'Target Aman'
            })
        if self.secondary_university:
            targets.append({
                'university': self.secondary_university,
                'type': 'secondary',
                'label': 'Target Cadangan'
            })
        return targets
    
    def get_recommendations_for_score(self, utbk_score):
        """Get recommendations for all target universities based on score, sorted by priority"""
        recommendations = []
        for target in self.get_all_targets():
            university = target['university']
            recommendation = university.get_recommendation_for_score(utbk_score)
            recommendations.append({
                'university': university,
                'target_type': target['type'],
                'target_label': target['label'],
                'recommendation': recommendation
            })
        
        # Sort recommendations by priority: primary -> backup -> secondary
        priority_order = {'primary': 1, 'backup': 2, 'secondary': 3}
        recommendations.sort(key=lambda x: priority_order.get(x['target_type'], 4))
        
        return recommendations
