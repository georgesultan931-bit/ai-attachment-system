from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class CustomLoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter password'
            }
        )
    )

class StudentRegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email address'
            }
        )
    )

    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter your phone number'
            }
        )
    )

    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'phone_number',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose username'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def save(self, commit=True):

        user = super().save(commit=False)

        user.role = 'student'
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']

        user.is_active = False
        user.is_email_verified = False
        user.is_approved = False

        if commit:
            user.save()

        return user

class EmployerRegistrationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter company email address'
            }
        )
    )

    phone_number = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter company phone number'
            }
        )
    )

    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'phone_number',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose employer username'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Create password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError(
                'An account with this email already exists.'
            )

        return email

    def save(self, commit=True):

        user = super().save(commit=False)

        user.role = 'employer'
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']

        user.is_active = False
        user.is_email_verified = False
        user.is_approved = False

        if commit:
            user.save()

        return user


class OTPVerificationForm(forms.Form):

    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter 6-digit OTP'
            }
        )
    )
