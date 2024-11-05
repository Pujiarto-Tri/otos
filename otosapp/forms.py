from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import User, Role, Category, Question, Choice

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
    
class CategoryCreationForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('category_name',)
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Enter category name'
            }),
        } 

    def save(self, commit=True):
        category = super().save(commit=False)
            
        if commit:
            category.save()
        return category
    
class CategoryUpdateForm(forms.ModelForm):
    category_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter Category Name'
        })
    )

    class Meta:
        model = Category
        fields = ['category_name',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help text for fields
        self.fields['category_name'].help_text = "category will be used for Categorizing Question"

        # Customize labels
        self.fields['category_name'].label = "Category Name"

    def save(self, commit=True):
        category = super().save(commit=False)
        if commit:
            category.save()
        return category
    
    

class QuestionCreationForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question_text', 'category')
        widgets = {
            'question_text': forms.TextInput(attrs={
                'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
                'placeholder': 'Enter question text'
            }),
            'category': forms.Select(attrs={
                'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5'
            })
        }

ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    fields=('choice_text', 'is_correct'),
    extra=2,
    min_num=2,
    max_num=10,
    validate_min=True,
    can_delete=False,
    widgets={
        'choice_text': forms.TextInput(attrs={
            'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
            'placeholder': 'Enter choice text'
        }),
        'is_correct': forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
        })
    }
)
class QuestionUpdateForm(forms.ModelForm):
    category_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter Category Name'
        })
    )

    class Meta:
        model = Category
        fields = ['category_name',]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help text for fields
        self.fields['category_name'].help_text = "category will be used for Categorizing Question"

        # Customize labels
        self.fields['category_name'].label = "Category Name"

    def save(self, commit=True):
        category = super().save(commit=False)
        if commit:
            category.save()
        return category