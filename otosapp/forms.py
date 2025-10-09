from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.forms import inlineformset_factory
from .models import User, Role, Category, Question, Choice, SubscriptionPackage, PaymentMethod, PaymentProof, UserSubscription, University, UniversityTarget, TryoutPackage, TryoutPackageCategory, StudentGoal

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg block w-full p-2.5',
            'placeholder': 'Masukkan nomor HP (contoh: +62812...)'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'phone_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        # Remove current_user from kwargs since we no longer need it for role selection
        kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        # save phone number from form
        user.phone_number = self.cleaned_data.get('phone_number')

        # Set default role to Visitor for new registrations (security: users cannot choose their own role)
        try:
            visitor_role = Role.objects.get(role_name='Visitor')
            user.role = visitor_role
        except Role.DoesNotExist:
            # Fallback: create Visitor role if it doesn't exist
            visitor_role = Role.objects.create(role_name='Visitor')
            user.role = visitor_role

        if commit:
            user.save()
        return user

class AdminUserCreationForm(UserCreationForm):
    """Form for admins/operators to create users with role selection"""
    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg block w-full p-2.5',
            'placeholder': 'Masukkan nomor HP (contoh: +62812...)'
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
        fields = ('email', 'phone_number', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        # Extract current_user from kwargs if provided
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Filter roles based on current user permissions
        if current_user and current_user.is_operator():
            # Operators cannot assign Admin role
            self.fields['role'].queryset = Role.objects.exclude(role_name='Admin')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        # save phone number from form
        user.phone_number = self.cleaned_data.get('phone_number')

        # Set role from form data
        user.role = self.cleaned_data.get('role')

        if commit:
            user.save()
        return user

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        # allow starting + and digits only
        import re
        if not phone:
            raise forms.ValidationError('Nomor HP wajib diisi.')
        if not re.match(r'^\+?\d{9,20}$', phone):
            raise forms.ValidationError('Format nomor tidak valid. Contoh: +628123456789')
        return phone

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        # allow starting + and digits only
        import re
        if not phone:
            raise forms.ValidationError('Nomor HP wajib diisi.')
        if not re.match(r'^\+?\d{9,20}$', phone):
            raise forms.ValidationError('Format nomor tidak valid. Contoh: +628123456789')
        return phone

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

    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5',
            'placeholder': 'Enter phone number (e.g. +62812...)'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'role', 'phone_number']

    def __init__(self, *args, **kwargs):
        # Extract current_user from kwargs if provided
        current_user = kwargs.pop('current_user', None)
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
        
        # Filter roles based on current user permissions
        if current_user and current_user.is_operator():
            # Operators cannot assign Admin role
            self.fields['role'].queryset = Role.objects.exclude(role_name='Admin')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number', '')
        import re
        if phone:
            if not re.match(r'^\+?\d{9,20}$', phone):
                raise forms.ValidationError('Format nomor tidak valid. Contoh: +628123456789')
        return phone
    
class CategoryCreationForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('category_name', 'time_limit', 'scoring_method', 'passing_score', 'teachers')
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

    teachers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role__role_name='Teacher'),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white',
        }),
        help_text='Assign teachers to this category (optional)'
    )
    # Display full name + email in choice labels for clearer Tom Select dropdown
    try:
        teachers.label_from_instance = lambda u: f"{u.get_full_name() or u.email} ({u.email})"
    except Exception:
        pass

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
        fields = ['category_name', 'time_limit', 'scoring_method', 'passing_score', 'teachers']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Teachers multi-select (show current teachers if instance provided)
        self.fields['teachers'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.filter(role__role_name='Teacher'),
            required=False,
            widget=forms.SelectMultiple(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white',
            }),
            help_text='Assign teachers to this category (optional)'
        )
        # show full name + email in select option labels
        try:
            self.fields['teachers'].label_from_instance = lambda u: f"{u.get_full_name() or u.email} ({u.email})"
        except Exception:
            pass

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
    question_text = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        'placeholder': 'Type your question here...',
        'rows': 6
    }))
    question_type = forms.ChoiceField(
        choices=Question.QUESTION_TYPES,
        widget=forms.RadioSelect(attrs={
            'class': 'question-type-radio'
        }),
        initial='multiple_choice'
    )
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
    correct_answer_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Masukkan jawaban benar (pisahkan dengan koma jika ada beberapa jawaban yang benar)',
            'rows': 3
        }),
        help_text="Untuk soal isian: masukkan jawaban benar. Jika ada beberapa jawaban yang benar, pisahkan dengan koma."
    )
    explanation = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Pembahasan/penjelasan mengapa jawabannya demikian (opsional)',
            'rows': 4
        }),
        help_text="Pembahasan atau penjelasan mengapa jawabannya demikian (opsional)"
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'category', 'custom_weight', 'correct_answer_text', 'explanation']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['custom_weight'].help_text = "Only used for custom scoring method (leave 0 for default/UTBK)"
        self.fields['question_type'].help_text = "Pilih tipe soal yang akan dibuat"
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        correct_answer_text = cleaned_data.get('correct_answer_text')
        
        if question_type == 'essay' and not correct_answer_text:
            raise forms.ValidationError("Jawaban benar wajib diisi untuk soal isian.")
        
        return cleaned_data
    
    def save(self, commit=True):
        question = super().save(commit=False)
        question.pub_date = timezone.now()  # Set the publication date
        if commit:
            question.save()
        return question

class ChoiceForm(forms.ModelForm):
    # Allow empty choice_text so a choice can be image-only. Validation below
    # will ensure at least one of text or image exists.
    choice_text = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        'placeholder': 'Enter choice text...',
        'rows': 2
    }))
    
    class Meta:
        model = Choice
        fields = ['choice_text', 'choice_image', 'is_correct']
        widgets = {
            'choice_image': forms.FileInput(attrs={'class': 'hidden'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'choice-checkbox'})
        }

    def clean(self):
        cleaned = super().clean()
        text = cleaned.get('choice_text')
        image = cleaned.get('choice_image')

        # ENHANCED: Clean WYSIWYG HTML content to check for actual text
        has_meaningful_text = False
        if text:
            # Remove HTML tags and check if there's actual text content
            import re
            from html import unescape
            
            # Strip HTML tags
            clean_text = re.sub(r'<[^>]+>', '', text)
            # Decode HTML entities
            clean_text = unescape(clean_text)
            # Remove extra whitespace and check if there's content
            clean_text = clean_text.strip()
            
            if clean_text:
                has_meaningful_text = True
                # Update the cleaned data with the original HTML (preserve formatting)
                cleaned['choice_text'] = text
            else:
                # Set to empty string if no meaningful content
                cleaned['choice_text'] = ''

        # If no text and no newly uploaded image, check existing instance image
        has_existing_image = False
        try:
            if self.instance and getattr(self.instance, 'choice_image'):
                # instance.choice_image may be a FieldFile
                if getattr(self.instance.choice_image, 'name', None):
                    has_existing_image = True
        except Exception:
            has_existing_image = False

        # Additional check: some flows upload the image via AJAX and place the
        # resulting URL into a hidden input named `choice_image_<1-based-index>`
        # in the template. The form `prefix` is usually like 'choices-0', so we
        # derive the 1-based index from the prefix and look for that POST key.
        has_uploaded_url = False
        try:
            prefix = getattr(self, 'prefix', '')  # e.g. 'choices-0'
            if prefix and '-' in prefix:
                parts = prefix.split('-')
                # last part should be the numeric index
                idx = int(parts[-1])
                hidden_name = f'choice_image_{idx+1}'
                # self.data contains POST values (QueryDict)
                uploaded_url = self.data.get(hidden_name)
                if uploaded_url and str(uploaded_url).strip():
                    has_uploaded_url = True
        except Exception:
            has_uploaded_url = False

        # NEW: Determine if this choice is required based on its index
        choice_index = None
        try:
            prefix = getattr(self, 'prefix', '')  # e.g. 'choices-0'
            if prefix and '-' in prefix:
                parts = prefix.split('-')
                choice_index = int(parts[-1])  # 0-based index
        except Exception:
            choice_index = None
        
        # Only validate if this is choice A or B (index 0 or 1)
        is_required_choice = choice_index is not None and choice_index <= 1
        
        # For optional choices (C, D, E), if they're empty, don't validate further
        if not is_required_choice and not has_meaningful_text and not image and not has_existing_image and not has_uploaded_url:
            # This is an optional empty choice - that's perfectly fine
            return cleaned
        
        # For required choices (A, B), enforce validation
        if is_required_choice and not has_meaningful_text and not image and not has_existing_image and not has_uploaded_url:
            choice_letter = 'A' if choice_index == 0 else 'B'
            raise forms.ValidationError(f'Choice {choice_letter} is required. Please provide either choice text or an image.')

        return cleaned
    
    def has_changed(self):
        """
        Override to prevent Django from treating empty optional choices as 'changed'
        which could trigger unnecessary validation
        """
        # Get choice index
        choice_index = None
        try:
            prefix = getattr(self, 'prefix', '')
            if prefix and '-' in prefix:
                parts = prefix.split('-')
                choice_index = int(parts[-1])
        except Exception:
            choice_index = None
        
        # For optional choices (C, D, E), if they're empty, consider them unchanged
        if choice_index is not None and choice_index > 1:
            text = self.cleaned_data.get('choice_text', '') if hasattr(self, 'cleaned_data') else ''
            image = self.cleaned_data.get('choice_image') if hasattr(self, 'cleaned_data') else None
            
            if not text and not image:
                return False
        
        return super().has_changed()

class BaseChoiceFormSet(forms.BaseInlineFormSet):
    def clean(self):
        """
        Custom formset validation that only requires choices A & B to be filled
        """
        # Don't validate if there are already form-level errors
        if any(self.errors):
            # Check if the errors are only from optional choices (C, D, E)
            has_critical_errors = False
            for i, form_errors in enumerate(self.errors):
                if form_errors and i <= 1:  # Only consider errors from A & B as critical
                    has_critical_errors = True
                    break
            
            if has_critical_errors:
                return
            # If only optional choices have errors, we can proceed
        
        filled_choices = 0
        choice_a_filled = False
        choice_b_filled = False
        
        for i, form in enumerate(self.forms):
            # Skip deleted forms
            if form.cleaned_data and form.cleaned_data.get('DELETE', False):
                continue
                
            # For choices C, D, E (index 2, 3, 4), we're more lenient
            if i >= 2:
                # Optional choices - don't require validation
                continue
                
            # For choices A & B (index 0, 1), validate normally
            if form.cleaned_data:
                text = form.cleaned_data.get('choice_text', '').strip()
                image = form.cleaned_data.get('choice_image')
                
                # Clean HTML content to check for actual text
                has_content = False
                if text:
                    import re
                    from html import unescape
                    clean_text = re.sub(r'<[^>]+>', '', text)
                    clean_text = unescape(clean_text).strip()
                    if clean_text:
                        has_content = True
                
                if has_content or image:
                    filled_choices += 1
                    if i == 0:  # Choice A
                        choice_a_filled = True
                    elif i == 1:  # Choice B
                        choice_b_filled = True
        
        # Only require A & B to be filled
        if not choice_a_filled:
            raise forms.ValidationError('Choice A is required.')
        if not choice_b_filled:
            raise forms.ValidationError('Choice B is required.')
    
    def is_valid(self):
        """
        Override to handle optional empty forms for choices C, D, E
        """
        # First check the parent validation
        result = super().is_valid()
        
        # If there are errors, check if they're only from optional choices
        if not result and self.errors:
            critical_errors = False
            for i, form_errors in enumerate(self.errors):
                if form_errors and i <= 1:  # Only A & B are critical
                    critical_errors = True
                    break
            
            # If no critical errors, we can consider it valid
            if not critical_errors:
                # Clear errors from optional choices
                for i in range(2, len(self.errors)):
                    if i < len(self.errors):
                        self.errors[i] = {}
                result = True
        
        return result

ChoiceFormSet = forms.inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    formset=BaseChoiceFormSet,
    extra=5,
    min_num=0,  # Set to 0 - we'll handle validation in BaseChoiceFormSet.clean()
    max_num=5,
    validate_max=True,
    can_delete=False
)

class EssayAnswerForm(forms.Form):
    """Form for essay/fill-in-the-blank answers"""
    answer_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-y',
            'placeholder': 'Tulis jawaban Anda di sini...',
            'rows': 4
        }),
        required=False,
        help_text="Masukkan jawaban Anda untuk soal isian ini."
    )

class QuestionUpdateForm(forms.ModelForm):
    question_text = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        'placeholder': 'Type your question here...',
        'rows': 6
    }))
    question_type = forms.ChoiceField(
        choices=Question.QUESTION_TYPES,
        widget=forms.RadioSelect(attrs={
            'class': 'question-type-radio'
        })
    )
    custom_weight = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
            'min': '0',
            'max': '100',
            'step': '0.01'
        })
    )
    correct_answer_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
            'placeholder': 'Masukkan jawaban benar (pisahkan dengan koma jika ada beberapa jawaban yang benar)',
            'rows': 3
        })
    )
    explanation = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'bg-white dark:bg-gray-600 border border-gray-300 dark:border-gray-500 text-gray-900 dark:text-white text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5',
            'placeholder': 'Pembahasan/penjelasan mengapa jawabannya demikian (opsional)',
            'rows': 4
        })
    )
    
    class Meta:
        model = Question
        fields = ['question_text', 'question_type', 'category', 'custom_weight', 'correct_answer_text', 'explanation']
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
        
        self.fields['question_type'].help_text = "Pilih tipe soal: pilihan ganda atau isian"
        self.fields['correct_answer_text'].help_text = "Untuk soal isian: masukkan jawaban benar (pisahkan dengan koma jika ada beberapa jawaban yang benar)"
    
    def clean(self):
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        correct_answer_text = cleaned_data.get('correct_answer_text')
        
        if question_type == 'essay' and not correct_answer_text:
            raise forms.ValidationError("Jawaban benar wajib diisi untuk soal isian.")
        
        return cleaned_data

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


# ======================= SUBSCRIPTION & PAYMENT FORMS =======================

class PaymentMethodForm(forms.ModelForm):
    """Form untuk admin mengelola metode pembayaran"""
    class Meta:
        model = PaymentMethod
        fields = ['name', 'payment_type', 'account_number', 'account_name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Contoh: Bank BCA, OVO, GoPay'
            }),
            'payment_type': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Nomor rekening atau akun'
            }),
            'account_name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Nama pemilik rekening'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].help_text = "Nama metode pembayaran (contoh: Bank BCA, OVO)"
        self.fields['account_number'].help_text = "Nomor rekening atau nomor akun"
        self.fields['account_name'].help_text = "Nama pemilik rekening atau akun"


class SubscriptionPackageForm(forms.ModelForm):
    """Form untuk admin mengelola paket berlangganan"""
    class Meta:
        model = SubscriptionPackage
        # Remove 'package_type' from fields
        fields = ['name', 'description', 'features', 'price', 'duration_days', 'is_active', 'is_featured']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Nama paket berlangganan'
            }),
            'description': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'rows': 4,
                'placeholder': 'Deskripsi paket berlangganan'
            }),
            'features': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'rows': 6,
                'placeholder': 'Fitur 1\nFitur 2\nFitur 3\n...'
            }),
            'price': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Harga dalam rupiah',
                'inputmode': 'numeric',
                'autocomplete': 'off',
            }),
            'duration_days': forms.NumberInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Durasi dalam hari',
                'min': '1'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['features'].help_text = "Masukkan setiap fitur dalam baris terpisah"
        self.fields['duration_days'].help_text = "Durasi berlangganan dalam hari (contoh: 30 untuk 1 bulan)"
        self.fields['is_featured'].help_text = "Tandai jika ini adalah paket unggulan"


class PaymentProofForm(forms.ModelForm):
    """Form untuk visitor upload bukti pembayaran"""
    # Override payment_method as ChoiceField to make it a dropdown
    payment_method = forms.ChoiceField(
        label="Metode Pembayaran",
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hanya tampilkan paket yang aktif
        self.fields['package'].queryset = SubscriptionPackage.objects.filter(is_active=True)
        
        # Dynamic choices untuk payment method berdasarkan PaymentMethod model
        payment_methods = PaymentMethod.objects.filter(is_active=True).order_by('payment_type', 'name')
        choices = [('', 'Pilih metode pembayaran')]
        for method in payment_methods:
            choices.append((method.get_display_text(), method.get_display_text()))
        
        # Set choices on the payment_method field
        self.fields['payment_method'].choices = choices
        
        self.fields['proof_image'].help_text = "Upload screenshot atau foto bukti pembayaran (format: JPG, PNG, max 5MB)"
        self.fields['payment_date'].help_text = "Tanggal dan waktu melakukan pembayaran"
    
    class Meta:
        model = PaymentProof
        fields = ['package', 'proof_image', 'payment_method', 'payment_date', 'amount_paid', 'notes']
        widgets = {
            'package': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
            }),
            'proof_image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 dark:text-gray-400 focus:outline-none dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400',
                'accept': 'image/*'
            }),
            'payment_date': forms.DateTimeInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'type': 'datetime-local'
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'placeholder': 'Jumlah yang dibayarkan',
                'min': '0',
                'step': '1000'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Catatan tambahan (opsional)'
            }),
        }
        
    def clean_proof_image(self):
        image = self.cleaned_data.get('proof_image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('Ukuran file terlalu besar. Maksimal 5MB.')
            
            # Check file type
            if not image.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise forms.ValidationError('Format file tidak didukung. Gunakan format JPG atau PNG.')
        
        return image
    
    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        package = self.cleaned_data.get('package')
        
        if amount and package:
            if amount != package.price:
                raise forms.ValidationError(f'Jumlah pembayaran harus sesuai dengan harga paket: Rp {package.price:,.0f}')
        
        return amount


class PaymentVerificationForm(forms.ModelForm):
    """Form untuk admin verifikasi pembayaran"""
    class Meta:
        model = PaymentProof
        fields = ['status', 'admin_notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'admin_notes': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'rows': 4,
                'placeholder': 'Catatan untuk user mengenai status pembayaran'
            }),
        }


class UserRoleChangeForm(forms.ModelForm):
    """Form khusus untuk admin mengubah role user"""
    subscription_days = forms.IntegerField(
        required=False,
        initial=30,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            'placeholder': 'Jumlah hari berlangganan'
        })
    )
    
    subscription_package = forms.ModelChoiceField(
        queryset=SubscriptionPackage.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
        })
    )
    
    class Meta:
        model = User
        fields = ['role']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['subscription_days'].help_text = "Durasi berlangganan (hanya untuk upgrade ke Student)"
        self.fields['subscription_package'].help_text = "Paket berlangganan (hanya untuk upgrade ke Student)"


class UserSubscriptionEditForm(forms.ModelForm):
    """Form untuk admin mengedit subscription user"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active packages
        self.fields['package'].queryset = SubscriptionPackage.objects.filter(is_active=True)
        self.fields['end_date'].help_text = "Tanggal berakhir berlangganan (tidak boleh sebelum hari ini)"
        self.fields['is_active'].help_text = "Status aktif subscription"
        
        # Format the initial value for datetime-local input
        if self.instance and self.instance.end_date:
            # Convert to local timezone and format for datetime-local input
            from django.utils import timezone
            local_dt = timezone.localtime(self.instance.end_date)
            formatted_dt = local_dt.strftime('%Y-%m-%dT%H:%M')
            self.fields['end_date'].widget.attrs['value'] = formatted_dt
    
    def clean_end_date(self):
        """Validate that end_date is not in the past"""
        from django.utils import timezone
        end_date = self.cleaned_data.get('end_date')
        
        if end_date:
            # Make sure end_date is timezone aware
            if timezone.is_naive(end_date):
                end_date = timezone.make_aware(end_date)
            
            # Check if end_date is in the past
            now = timezone.now()
            if end_date < now:
                raise forms.ValidationError(
                    'End date cannot be in the past. Please select a future date and time.'
                )
        
        return end_date
    
    class Meta:
        model = UserSubscription
        fields = ['package', 'end_date', 'is_active']
        widgets = {
            'package': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'end_date': forms.DateTimeInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'type': 'datetime-local',
                'step': '1'  # Allow seconds
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
            }),
        }


# ======================= UNIVERSITY FORMS =======================

class UniversityForm(forms.ModelForm):
    """Form untuk mengelola data universitas"""
    
    class Meta:
        model = University
        fields = ['name', 'location', 'website', 'description', 'minimum_utbk_score', 'tier', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Nama Universitas'
            }),
            'location': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'Lokasi/Kota'
            }),
            'website': forms.URLInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'placeholder': 'https://university.ac.id'
            }),
            'description': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Deskripsi singkat tentang universitas'
            }),
            'minimum_utbk_score': forms.NumberInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'min': '0',
                'max': '7000',
                'placeholder': 'Nilai minimum UTBK (0-7000)'
            }),
            'tier': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-primary-600 bg-gray-100 dark:bg-gray-600 border-gray-300 dark:border-gray-500 rounded focus:ring-primary-500 dark:focus:ring-primary-600'
            }),
        }
    
    def clean_minimum_utbk_score(self):
        """Validate UTBK score range"""
        score = self.cleaned_data.get('minimum_utbk_score')
        if score is not None:
            if score < 0 or score > 7000:
                raise forms.ValidationError('Nilai UTBK harus antara 0-7000')
        return score


class UniversityTargetForm(forms.ModelForm):
    """Form untuk student mengatur target universitas"""
    
    class Meta:
        model = UniversityTarget
        fields = ['primary_university', 'secondary_university', 'backup_university', 'notes']
        widgets = {
            'primary_university': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'secondary_university': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'backup_university': forms.Select(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                'rows': 3,
                'placeholder': 'Catatan personal tentang target universitas Anda'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure queryset for AJAX - allow all universities for validation
        for field in ['primary_university', 'backup_university', 'secondary_university']:
            if field in self.fields:
                # Set queryset to all universities so any valid ID can be accepted
                self.fields[field].queryset = University.objects.all()
                self.fields[field].required = False
                self.fields[field].empty_label = "-- Pilih Universitas --"
        
        self.fields['primary_university'].help_text = "Universitas impian/target utama"
        self.fields['backup_university'].help_text = "Universitas yang relatif aman untuk nilai Anda"
        self.fields['secondary_university'].help_text = "Universitas cadangan jika target utama tidak tercapai"
        self.fields['notes'].help_text = "Catatan personal, motivasi, atau rencana belajar"
    
    def clean(self):
        """Validate that universities are different"""
        cleaned_data = super().clean()
        primary = cleaned_data.get('primary_university')
        secondary = cleaned_data.get('secondary_university')
        backup = cleaned_data.get('backup_university')
        
        universities = [primary, secondary, backup]
        non_empty_universities = [u for u in universities if u is not None]
        
        # Check for duplicates
        if len(non_empty_universities) != len(set(non_empty_universities)):
            raise forms.ValidationError('Pilih universitas yang berbeda untuk setiap target.')
        
        return cleaned_data


class StudentGoalForm(forms.ModelForm):
    """Form untuk siswa mengatur target belajar"""

    class Meta:
        model = StudentGoal
        fields = ['goal_type', 'title', 'target_value', 'timeframe_start', 'timeframe_end']
        widgets = {
            'goal_type': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'placeholder': 'Contoh: Selesaikan 5 Tryout Oktober'
            }),
            'target_value': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'min': '0',
                'step': '0.1',
                'placeholder': 'Nilai target'
            }),
            'timeframe_start': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'type': 'date'
            }),
            'timeframe_end': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white',
                'type': 'date'
            }),
        }

    def clean_target_value(self):
        value = self.cleaned_data.get('target_value')
        if value is None or value <= 0:
            raise forms.ValidationError('Target harus lebih besar dari 0.')
        return value

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('timeframe_start')
        end = cleaned_data.get('timeframe_end')

        if not start:
            self.add_error('timeframe_start', 'Tanggal mulai wajib diisi untuk menghitung progres target.')

        if start and end and end < start:
            self.add_error('timeframe_end', 'Tanggal selesai harus setelah tanggal mulai.')
        return cleaned_data


class TryoutPackageForm(forms.ModelForm):
    """Form for creating and editing tryout packages"""
    
    class Meta:
        model = TryoutPackage
        fields = ['package_name', 'description', 'total_time', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style form fields
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600'
                })
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({
                    'class': 'block p-2.5 w-full text-sm text-gray-900 bg-gray-50 rounded-lg border border-gray-300 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
                })
            else:
                field.widget.attrs.update({
                    'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
                })
        
        # Set help texts
            fields = ['primary_university', 'backup_university', 'secondary_university', 'notes']
            widgets = {
                'primary_university': forms.Select(attrs={
                    'class': 'form-select w-full rounded-lg border-gray-300 dark:bg-gray-800 dark:text-white dark:border-gray-600',
                }),
                'backup_university': forms.Select(attrs={
                    'class': 'form-select w-full rounded-lg border-gray-300 dark:bg-gray-800 dark:text-white dark:border-gray-600',
                }),
                'secondary_university': forms.Select(attrs={
                    'class': 'form-select w-full rounded-lg border-gray-300 dark:bg-gray-800 dark:text-white dark:border-gray-600',
                }),
                'notes': forms.Textarea(attrs={
                    'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500',
                    'rows': 3,
                    'placeholder': 'Catatan personal tentang target universitas Anda'
                }),
            }
        self.fields['description'].help_text = "Deskripsi paket dan target peserta"
        self.fields['total_time'].help_text = "Total waktu pengerjaan dalam menit (contoh: 180 untuk 3 jam)"
        self.fields['is_active'].help_text = "Centang untuk membuat paket tersedia untuk siswa"

class TryoutPackageCategoryForm(forms.ModelForm):
    """Form for configuring categories within a package"""
    
    class Meta:
        model = TryoutPackageCategory
        fields = ['category', 'question_count', 'max_score', 'order']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500'
            })
        
        # Only show categories that have questions
        self.fields['category'].queryset = Category.objects.filter(question__isnull=False).distinct()
        
        # Set help texts
        self.fields['category'].help_text = "Pilih kategori soal"
        self.fields['question_count'].help_text = "Jumlah soal dari kategori ini"
        self.fields['max_score'].help_text = "Skor maksimum untuk kategori ini (kontribusi ke total 7000)"
        self.fields['order'].help_text = "Urutan kategori dalam paket (1 = pertama)"
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        question_count = cleaned_data.get('question_count')
        
        if category and question_count:
            available_questions = category.get_question_count()
            if question_count > available_questions:
                raise forms.ValidationError(
                    f'Kategori "{category.category_name}" hanya memiliki {available_questions} soal. '
                    f'Anda meminta {question_count} soal.'
                )
        
        return cleaned_data

# Create formset for package categories
TryoutPackageCategoryFormSet = inlineformset_factory(
    TryoutPackage,
    TryoutPackageCategory,
    form=TryoutPackageCategoryForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)