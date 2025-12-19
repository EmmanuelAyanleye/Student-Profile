from django import forms
from .models import AdminStaff, Student, StudentImage, StudentAchievement
from django.forms import modelformset_factory

class AdminStaffForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password'
    }))

    class Meta:
        model = AdminStaff
        fields = ['title', 'first_name', 'last_name', 'email', 'role', 'password']
        widgets = {
            'title': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'role': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }

class ModifyMemberForm(forms.ModelForm):
    class Meta:
        model = AdminStaff
        fields = ['title', 'first_name', 'last_name', 'email', 'role']
        widgets = {
            'title': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }


class StudentAchievementForm(forms.ModelForm):
    class Meta:
        model = StudentAchievement
        fields = ['id', 'file', 'label']
        widgets = {
            'id': forms.HiddenInput(),
            'file': forms.FileInput(attrs={
                'accept': '.pdf,.doc,.docx',
                'class': 'achievement-file-input',
                'style': 'display: none;'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-input label-input achievement-label',
                'placeholder': 'Achievement Label',
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; margin-top: 0.5rem;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['label'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Skip all validation if form is marked for deletion or is existing instance
        if cleaned_data.get('DELETE') or self.instance.pk:
            return cleaned_data
        
        file_field = cleaned_data.get('file')
        label = cleaned_data.get('label')
        
        # Only validate for completely new instances
        if file_field and not label:
            raise forms.ValidationError("Label is required when uploading a file.")
        
        if label and not file_field:
            raise forms.ValidationError("File is required when providing a label.")
        
        return cleaned_data

StudentAchievementFormSet = modelformset_factory(
    StudentAchievement,
    form=StudentAchievementForm,
    extra=0,
    can_delete=True,
    max_num=6
)

class StudentImageForm(forms.ModelForm):
    class Meta:
        model = StudentImage
        fields = ['id', 'image', 'label']
        widgets = {
            'id': forms.HiddenInput(),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'student-image-input',
                'style': 'display: none;'
            }),
            'label': forms.TextInput(attrs={
                'class': 'form-input label-input image-label',
                'placeholder': 'Image Label',
                'style': 'width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 8px; margin-top: 0.5rem;'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['label'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Skip all validation if form is marked for deletion or is existing instance
        if cleaned_data.get('DELETE') or self.instance.pk:
            return cleaned_data
        
        image = cleaned_data.get('image')
        label = cleaned_data.get('label')
        
        # Only validate for completely new instances
        if image and not label:
            raise forms.ValidationError("Label is required when uploading an image.")
        
        if label and not image:
            raise forms.ValidationError("Image is required when providing a label.")
        
        if image:
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            file_name = image.name if hasattr(image, 'name') else str(image)
            file_ext = '.' + file_name.split('.')[-1].lower()
            
            if file_ext not in valid_extensions:
                raise forms.ValidationError("Only image files (jpg, png, gif, webp) are allowed.")
        
        return cleaned_data

StudentImageFormSet = modelformset_factory(
    StudentImage,
    form=StudentImageForm,
    extra=0,
    can_delete=True,
    max_num=6
)

class StudentForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Password'
    }), required=False)

    class Meta:
        model = Student
        fields = [
            'surname', 'other_names', 'date_of_birth', 'level', 'department',
            'matric_number', 'password', 'session', 'home_address', 'place_of_origin',
            'skin_tone', 'weight', 'height', 'please_state_others',
            'parent_surname', 'parent_other_names', 'parent_email', 'parent_phone',
            'allergies', 'blood_group', 'genotype', 'if_more_stone',
            'other_achievement_info', 'photo'
        ]
        widgets = {
            'surname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Surname'}),
            'other_names': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Other Names'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'placeholder': 'Date of Birth'}),
            'level': forms.Select(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'matric_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Matric Number'}),
            'session': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Session'}),
            'home_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Home Address'}),
            'place_of_origin': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Place of Origin'}),
            'skin_tone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Skin Tone'}),
            'weight': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Weight'}),
            'height': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Height'}),
            'please_state_others': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Please state others', 'rows': 3}),
            'parent_surname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Surname'}),
            'parent_other_names': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Other Names'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'}),
            'allergies': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Allergies'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Blood Group'}),
            'genotype': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Genotype'}),
            'if_more_stone': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'If there is any other that isn\'t of the above', 'rows': 2}),
            'other_achievement_info': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Other Achievement Info', 'rows': 2}),
        }
    
    def clean_matric_number(self):
        matric_number = self.cleaned_data.get('matric_number')
        # Check if matric number exists and exclude the current instance
        if Student.objects.filter(matric_number=matric_number).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This matric number already exists in the system.")
        return matric_number


class StudentSignupForm(forms.ModelForm):
    """Simple form for student self-signup"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Password'
    }))

    class Meta:
        model = Student
        fields = ['surname', 'other_names', 'level', 'matric_number', 'password']
        widgets = {
            'surname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'other_names': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Other Names'}),
            'level': forms.Select(attrs={'class': 'form-input'}),
            'matric_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Matric Number'}),
        }
    
    def clean_matric_number(self):
        matric_number = self.cleaned_data.get('matric_number')
        # Check if matric number already exists
        if Student.objects.filter(matric_number=matric_number).exists():
            raise forms.ValidationError("This matric number is already registered.")
        return matric_number


class StudentViewForm(forms.ModelForm):
    """Form for viewing student details without password field"""
    
    class Meta:
        model = Student
        fields = [
            'surname', 'other_names', 'date_of_birth', 'level', 'department',
            'matric_number', 'session', 'home_address', 'place_of_origin',
            'skin_tone', 'weight', 'height', 'please_state_others',
            'parent_surname', 'parent_other_names', 'parent_email', 'parent_phone',
            'allergies', 'blood_group', 'genotype', 'if_more_stone',
            'other_achievement_info', 'photo'
        ]
        widgets = {
            'surname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Surname'}),
            'other_names': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Other Names'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date', 'placeholder': 'Date of Birth'}),
            'level': forms.Select(attrs={'class': 'form-input'}),
            'department': forms.Select(attrs={'class': 'form-input'}),
            'matric_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Matric Number'}),
            'session': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Session'}),
            'home_address': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Home Address'}),
            'place_of_origin': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Place of Origin'}),
            'skin_tone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Skin Tone'}),
            'weight': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Weight'}),
            'height': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Height'}),
            'please_state_others': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Please state others', 'rows': 3}),
            'parent_surname': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Surname'}),
            'parent_other_names': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Other Names'}),
            'parent_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone Number'}),
            'allergies': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Allergies'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Blood Group'}),
            'genotype': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Genotype'}),
            'if_more_stone': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'If there is any other that isn\'t of the above', 'rows': 2}),
            'other_achievement_info': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Other Achievement Info', 'rows': 2}),
        }
    
    def clean_matric_number(self):
        matric_number = self.cleaned_data.get('matric_number')
        # Check if matric number exists and exclude the current instance
        if Student.objects.filter(matric_number=matric_number).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This matric number already exists in the system.")
        return matric_number