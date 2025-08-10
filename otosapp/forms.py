from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.forms import inlineformset_factory
from .models import User, Role, Category, Question, Choice, SubscriptionPackage, PaymentProof, UserSubscription
from django_ckeditor_5.widgets import CKEditor5Widget

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        
        # Set default role sebagai Visitor untuk user baru
        if not user.role:
            default_role, created = Role.objects.get_or_create(role_name='Visitor')
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


# ======================= SUBSCRIPTION & PAYMENT FORMS =======================

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
            'payment_method': forms.TextInput(attrs={
                'class': 'bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'placeholder': 'Contoh: Transfer Bank BCA, OVO, GoPay, dll'
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hanya tampilkan paket yang aktif
        self.fields['package'].queryset = SubscriptionPackage.objects.filter(is_active=True)
        self.fields['proof_image'].help_text = "Upload screenshot atau foto bukti pembayaran (format: JPG, PNG, max 5MB)"
        self.fields['payment_date'].help_text = "Tanggal dan waktu melakukan pembayaran"
        
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