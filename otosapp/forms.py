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
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Enter email address'
        })
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Enter first name'
        })
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            'placeholder': 'Enter last name'
        })
    )
    
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        required=True,
        label="User Role",
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
        })
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help text for fields
        self.fields['email'].help_text = "The user's email address will be used for login and communications"
        self.fields['first_name'].help_text = "Enter the user's first name"
        self.fields['last_name'].help_text = "Enter the user's last name"
        self.fields['role'].help_text = "Select the appropriate role for this user"

        # Customize labels
        self.fields['email'].label = "Email Address"
        self.fields['first_name'].label = "First Name"
        self.fields['last_name'].label = "Last Name"

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user