from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
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

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            })

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].widget.attrs.update({
            'accept': 'image/*',
            'class': 'hidden'
        })
        # Add file size validation help text
        self.fields['profile_picture'].help_text = 'Maksimal ukuran file 250KB. File akan dikompres otomatis jika terlalu besar.'
    
    def clean_profile_picture(self):
        from .utils import validate_image_size
        
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if profile_picture:
            # Validate file type
            if not profile_picture.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                raise forms.ValidationError('Format file tidak didukung. Gunakan format: PNG, JPG, JPEG, GIF, BMP, atau WebP.')
            
            # Check file size (will raise ValidationError if too large)
            try:
                validate_image_size(profile_picture)
            except Exception:
                # If validation fails, we'll compress it in the save method
                pass
                
        return profile_picture
    
    def save(self, commit=True):
        from .utils import compress_image
        
        instance = super().save(commit=False)
        
        # Get the uploaded file
        profile_picture = self.cleaned_data.get('profile_picture')
        
        if profile_picture:
            # Always compress the image to ensure optimal size and quality
            compressed_image = compress_image(profile_picture)
            instance.profile_picture = compressed_image
        
        if commit:
            instance.save()
        
        return instance

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            })
    
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
        fields = ('category_name', 'time_limit', 'scoring_method', 'passing_score')
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Enter category name'
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Enter time limit in minutes (default: 60)',
                'min': '1',
                'max': '300'
            }),
            'scoring_method': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'passing_score': forms.NumberInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Enter minimum passing score (0-100)',
                'min': '0',
                'max': '100',
                'step': '0.1'
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
    
    time_limit = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter time limit in minutes',
            'min': '1',
            'max': '300'
        })
    )
    
    scoring_method = forms.ChoiceField(
        choices=Category.SCORING_METHODS,
        required=True,
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        })
    )
    
    passing_score = forms.FloatField(
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter minimum passing score (0-100)',
            'min': '0',
            'max': '100',
            'step': '0.1'
        })
    )

    class Meta:
        model = Category
        fields = ['category_name', 'time_limit', 'scoring_method', 'passing_score']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add help text for fields
        self.fields['category_name'].help_text = "Category will be used for categorizing questions"
        self.fields['time_limit'].help_text = "Time limit for this category in minutes (1-300 minutes)"
        self.fields['scoring_method'].help_text = "Choose scoring method: Default (equal points), Custom (manual weights), or UTBK (difficulty-based)"

        # Customize labels
        self.fields['category_name'].label = "Category Name"
        self.fields['scoring_method'].label = "Scoring Method"

    def save(self, commit=True):
        category = super().save(commit=False)
        if commit:
            category.save()
        return category

class QuestionForm(forms.ModelForm):
    question_text = forms.CharField(widget=CKEditor5Widget(config_name='extends'))
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500'
        })
    )
    custom_weight = forms.FloatField(
        required=False,
        initial=0,
        widget=forms.NumberInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Enter custom weight (0-100)',
            'min': '0',
            'max': '100',
            'step': '0.01'
        })
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'category', 'custom_weight']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['custom_weight'].help_text = "Only used for custom scoring method (leave 0 for default/UTBK)"
    
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
    custom_weight = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
            'min': '0',
            'max': '100',
            'step': '0.01'
        })
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'category', 'custom_weight']
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
        
        self.fields['custom_weight'].label = "Custom Weight"
        self.fields['custom_weight'].help_text = "Weight for custom scoring (0-100 points)"

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