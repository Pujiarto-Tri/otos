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
    
    def __str__(self):
        return self.category_name
    
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
