from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, Role, Category, Question, Choice, Test, Answer

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
    list_display = ('category_name', 'time_limit', 'scoring_method', 'scoring_status')
    list_filter = ('scoring_method',)
    search_fields = ('category_name',)
    
    def scoring_status(self, obj):
        if obj.scoring_method == 'custom':
            total_points = obj.get_total_custom_points()
            if abs(total_points - 100) < 0.01:
                return format_html('<span style="color: green;">✓ Complete ({})</span>', total_points)
            else:
                return format_html('<span style="color: red;">⚠ Incomplete ({}/100)</span>', total_points)
        return format_html('<span style="color: blue;">Auto-calculated</span>')
    scoring_status.short_description = 'Scoring Status'

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
