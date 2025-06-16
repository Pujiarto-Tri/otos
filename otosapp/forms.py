from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import User, Role, Category, Question, Choice
from django_ckeditor_5.widgets import CKEditor5Widget

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

class QuestionForm(forms.ModelForm):
    question_text = forms.CharField(widget=CKEditor5Widget(config_name='extends'))
    
    class Meta:
        model = Question
        fields = ['question_text', 'category']
    
    def save(self, commit=True):
        question = super().save(commit=False)
        question.pub_date = timezone.now()  # Set the publication date
        if commit:
            question.save()
        return question

class ChoiceForm(forms.ModelForm):
    choice_text = forms.CharField(widget=CKEditor5Widget(config_name='extends'))
    
    class Meta:
        model = Choice
        fields = ['choice_text', 'is_correct']
        widgets = {
            'is_correct': forms.CheckboxInput(attrs={'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'})
        }

ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=2,
    min_num=2,
    max_num=10,
    can_delete=True
)

class QuestionUpdateForm(forms.ModelForm):
    question_text = forms.CharField(widget=CKEditor5Widget(config_name='extends'))
    
    class Meta:
        model = Question
        fields = ['question_text', 'category']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['question_text'].label = "Question"
        self.fields['question_text'].help_text = "Enter the question text here"

        self.fields['category'].label = "Category"
        self.fields['category'].help_text = "Select the category"

    def save(self, commit=True):
        question = super().save(commit=False)
        if commit:
            question.save()
        return question

class AnswerForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', None)
        super().__init__(*args, **kwargs)

        if questions:
            for question in questions:
                # Create a choice field for each question
                self.fields[f'question_{question.id}'] = forms.ChoiceField(
                    choices=[(choice.id, choice.choice_text) for choice in question.choices.all()],
                    widget=forms.RadioSelect,
                    label=question.question_text
                )