from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Category, Question, Choice, Test, Answer

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_active', 'role', 'full_name')
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

# Registering models in the admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Test)
admin.site.register(Answer)
