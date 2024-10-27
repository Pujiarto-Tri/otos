from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Category, Question, Choice, Test, Answer

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_active', 'role')  # Customize the fields displayed
    list_filter = ('is_staff', 'is_active', 'role')  # Add filters for easy searching
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),  # Include 'role' in the User model fields
    )

# Registering models in the admin
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)
admin.site.register(Category)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Test)
admin.site.register(Answer)
