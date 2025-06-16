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
    category_name = models.CharField(max_length=200)

    def __str__(self):
        return self.category_name

class Question(models.Model):
    question_text = CKEditor5Field('Text', config_name='extends')
    pub_date = models.DateTimeField('date published')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

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
    categories = models.ManyToManyField(Category, related_name="tests", blank=True)

    def __str__(self):
        return f"Test by {self.student.username} on {self.date_taken}"

    def calculate_score(self):
        correct_answers = self.answers.filter(selected_choice__is_correct=True).count()
        total_questions = self.answers.count()
        self.score = (correct_answers / total_questions) * 100 if total_questions else 0
        self.save()

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
