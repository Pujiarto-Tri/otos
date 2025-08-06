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
        
        # Calculate average score
        total_score = sum(test.score for test in completed_tests)
        average_score = round(total_score / total_tests, 1)
        
        return {
            'total_tests': total_tests,
            'total_students': total_students,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': pass_rate,
            'average_score': average_score
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

    def __str__(self):
        return f"Test by {self.student.username} on {self.date_taken}"

    def calculate_score(self):
        """Calculate score based on category scoring method"""
        answers = self.answers.all()
        if not answers.exists():
            self.score = 0
            self.save()
            return

        category = answers.first().question.category
        
        if category.scoring_method == 'default':
            self._calculate_default_score()
        elif category.scoring_method == 'custom':
            self._calculate_custom_score()
        elif category.scoring_method == 'utbk':
            self._calculate_utbk_score()
        
        self.save()
    
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
        """UTBK scoring: Difficulty-based scoring"""
        total_score = 0
        total_possible_score = 0
        
        for answer in self.answers.all():
            question_weight = answer.question.difficulty_coefficient
            total_possible_score += question_weight
            
            if answer.selected_choice.is_correct:
                total_score += question_weight
        
        if total_possible_score > 0:
            # Normalize to 100 scale
            self.score = (total_score / total_possible_score) * 100
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
    
    def is_passed(self):
        """Check if test score meets the category's passing requirement"""
        answers = self.answers.all()
        if not answers.exists():
            return False
        
        # Get the category from the first answer (all questions in a test should be from same category)
        category = answers.first().question.category
        return category.is_passing_score(self.score)
    
    def get_pass_status(self):
        """Get pass/fail status with color for display"""
        if self.is_passed():
            return {'status': 'LULUS', 'color': 'green'}
        else:
            return {'status': 'TIDAK LULUS', 'color': 'red'}
    
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
        
        # Normalize coefficients so total equals 100 when all questions answered correctly
        current_total = sum(q.difficulty_coefficient for q in questions)
        if current_total > 0:
            normalization_factor = 100 / current_total
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

class SubscriptionPackage(models.Model):
    """Model untuk paket berlangganan"""
    PACKAGE_TYPES = [
        ('basic', 'Paket Dasar'),
        ('premium', 'Paket Premium'),
        ('pro', 'Paket Pro'),
        ('ultimate', 'Paket Ultimate'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nama Paket")
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, verbose_name="Tipe Paket")
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
