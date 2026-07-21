from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True, 'autocomplete': 'username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'current-password'})
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('username', 'password1', 'password2'):
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    skills = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Python, SQL, Django',
        }),
        help_text='Comma-separated list of skills.',
    )

    class Meta:
        model = Profile
        fields = [
            'experience_level',
            'preferred_location',
            'preferred_job_type',
            'preferred_salary_min',
            'preferred_categories',
        ]
        widgets = {
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'preferred_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Kampala, Remote',
            }),
            'preferred_job_type': forms.Select(attrs={'class': 'form-select'}),
            'preferred_salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 500000',
            }),
            'preferred_categories': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['skills'] = ', '.join(
                self.instance.skills.values_list('name', flat=True)
            )
