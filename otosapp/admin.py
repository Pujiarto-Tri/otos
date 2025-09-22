from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Role, Category, Question, Choice, Test, Answer, MessageThread, Message, University, UniversityTarget, TryoutPackage, TryoutPackageCategory

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_active', 'role')
    list_filter = ('is_staff', 'is_active', 'role')
    search_fields = ('email', 'username')
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        if not obj.role:
            default_role = Role.objects.get(role_name='Student')  # or get your default role
            obj.role = default_role
        super().save_model(request, obj, form, change)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'time_limit', 'scoring_method', 'scoring_status', 'teachers_list')
    list_filter = ('scoring_method',)
    search_fields = ('category_name', 'teachers__email', 'teachers__username')
    
    def scoring_status(self, obj):
        if obj.scoring_method == 'custom':
            total_points = obj.get_total_custom_points()
            if abs(total_points - 100) < 0.01:
                return format_html('<span style="color: green;">✓ Complete ({})</span>', total_points)
            else:
                return format_html('<span style="color: red;">⚠ Incomplete ({}/100)</span>', total_points)
        return format_html('<span style="color: blue;">Auto-calculated</span>')
    scoring_status.short_description = 'Scoring Status'

    def teachers_list(self, obj):
        names = [t.get_full_name() or t.email for t in obj.teachers.all()]
        return ", ".join(names)
    teachers_list.short_description = 'Teachers'

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text_short', 'category', 'custom_weight', 'difficulty_coefficient', 'pub_date')
    list_filter = ('category', 'category__scoring_method')
    search_fields = ('question_text',)
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question Text'

# Registering models in the admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice)
admin.site.register(Test)
admin.site.register(Answer)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'created_at', 'is_read')
    fields = ('sender', 'content', 'is_read', 'created_at')


class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'teacher_or_admin', 'thread_type', 'status', 'priority', 'closed_by', 'closed_at', 'reopened_by', 'reopened_at', 'last_activity')
    list_filter = ('thread_type', 'status', 'priority', 'created_at')
    search_fields = ('title', 'student__username', 'student__email', 'teacher_or_admin__username')
    readonly_fields = ('created_at', 'updated_at', 'last_activity', 'closed_by', 'closed_at', 'reopened_by', 'reopened_at')
    date_hierarchy = 'created_at'
    inlines = [MessageInline]
    
    fieldsets = (
        ('Informasi Utama', {
            'fields': ('title', 'thread_type', 'status', 'priority')
        }),
            ('Peserta', {
            'fields': ('student', 'teacher_or_admin', 'category', 'closed_by', 'closed_at', 'reopened_by', 'reopened_at')
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'teacher_or_admin', 'category')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('thread_title', 'sender', 'content_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at', 'thread__thread_type')
    search_fields = ('content', 'sender__username', 'thread__title')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    def thread_title(self, obj):
        return obj.thread.title
    thread_title.short_description = 'Thread'
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Preview Pesan'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('thread', 'sender')


admin.site.register(MessageThread, MessageThreadAdmin)
admin.site.register(Message, MessageAdmin)
from .models import ThreadStatusLog

class ThreadStatusLogAdmin(admin.ModelAdmin):
    list_display = ('thread', 'changed_by', 'old_status', 'new_status', 'created_at')
    list_filter = ('old_status', 'new_status', 'created_at')
    search_fields = ('thread__title', 'changed_by__username', 'note')

admin.site.register(ThreadStatusLog, ThreadStatusLogAdmin)


# ======================= UNIVERSITY ADMIN =======================

class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'tier', 'minimum_utbk_score', 'is_active', 'created_at')
    list_filter = ('tier', 'is_active', 'created_at')
    search_fields = ('name', 'location')
    ordering = ('tier', 'name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('name', 'location', 'website', 'description')
        }),
        ('Klasifikasi & Scoring', {
            'fields': ('tier', 'minimum_utbk_score')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class UniversityTargetAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'primary_university', 'secondary_university', 'backup_university', 'updated_at')
    list_filter = ('primary_university__tier', 'updated_at')
    search_fields = ('user__email', 'user__username', 'primary_university__name', 'secondary_university__name', 'backup_university__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Target Universitas', {
            'fields': ('primary_university', 'secondary_university', 'backup_university')
        }),
        ('Catatan', {
            'fields': ('notes',)
        }),
        ('Timestamp', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


admin.site.register(University, UniversityAdmin)
admin.site.register(UniversityTarget, UniversityTargetAdmin)


# ======================= TRYOUT PACKAGE ADMIN =======================

class TryoutPackageCategoryInline(admin.TabularInline):
    model = TryoutPackageCategory
    extra = 1
    fields = ('category', 'question_count', 'max_score', 'order')
    ordering = ('order',)

class TryoutPackageAdmin(admin.ModelAdmin):
    list_display = ('package_name', 'total_questions', 'total_score', 'total_time', 'is_active', 'can_be_taken_status', 'created_at')
    list_filter = ('is_active', 'created_at', 'created_by')
    search_fields = ('package_name', 'description')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    inlines = [TryoutPackageCategoryInline]
    
    fieldsets = (
        ('Informasi Dasar', {
            'fields': ('package_name', 'description', 'total_time', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_questions(self, obj):
        count = obj.get_total_questions()
        return f"{count} soal"
    total_questions.short_description = 'Total Soal'
    
    def total_score(self, obj):
        score = obj.get_total_max_score()
        if abs(score - 1000) < 0.01:
            return format_html('<span style="color: green;">✓ {} poin</span>', score)
        else:
            return format_html('<span style="color: red;">⚠ {} poin</span>', score)
    total_score.short_description = 'Total Skor'
    
    def can_be_taken_status(self, obj):
        if obj.can_be_taken():
            return format_html('<span style="color: green;">✓ Siap</span>')
        else:
            return format_html('<span style="color: red;">⚠ Perlu Perbaikan</span>')
    can_be_taken_status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class TryoutPackageCategoryAdmin(admin.ModelAdmin):
    list_display = ('package', 'category', 'question_count', 'max_score', 'score_per_question', 'order', 'validation_status')
    list_filter = ('package', 'category')
    search_fields = ('package__package_name', 'category__category_name')
    ordering = ('package', 'order')
    
    def score_per_question(self, obj):
        return f"{obj.get_score_per_question():.1f} poin"
    score_per_question.short_description = 'Poin per Soal'
    
    def validation_status(self, obj):
        if obj.validate_question_count():
            return format_html('<span style="color: green;">✓ Valid</span>')
        else:
            available = obj.category.get_question_count()
            return format_html('<span style="color: red;">⚠ Hanya {} soal tersedia</span>', available)
    validation_status.short_description = 'Validasi'


admin.site.register(TryoutPackage, TryoutPackageAdmin)
admin.site.register(TryoutPackageCategory, TryoutPackageCategoryAdmin)
