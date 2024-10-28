from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Role

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        
        # Set default role if none is specified
        if not user.role:
            default_role = Role.objects.get(role_name='Student')  # or get your default role
            user.role = default_role
            
        if commit:
            user.save()
        return user
    
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'role']  # Include other fields you want admins to edit

    # Optionally, add a role dropdown limited to available roles in Role model
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        label="User Role"
    )

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user