from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


def can_replace_pending_user(user):

    return (
        user.role in [
            'student',
            'employer'
        ]
        and not user.is_email_verified
        and not user.is_approved
    )


class ReplacePendingAccountMixin:

    def clean(self):

        cleaned_data = super().clean()

        self.replace_pending_conflict(
            cleaned_data,
            'email',
            'email__iexact'
        )

        self.replace_pending_conflict(
            cleaned_data,
            'username',
            'username__iexact'
        )

        return cleaned_data

    def replace_pending_conflict(self, cleaned_data, field_name, lookup):

        value = cleaned_data.get(field_name)

        if not value:
            return

        existing_user = User.objects.filter(
            **{
                lookup: value
            }
        ).first()

        if existing_user is None:
            return

        if can_replace_pending_user(existing_user):
            existing_user.delete()
            return

        if field_name == 'email':
            self.add_error(
                field_name,
                'This email is already registered to an active or verified account. Please log in or use another email.'
            )

        if field_name == 'username':
            self.add_error(
                field_name,
                'This username is already registered to an active or verified account. Please choose another username.'
            )


class CustomLoginForm(AuthenticationForm):

    username = forms.CharField(
        label='Username or Email',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter username or email',
                'autocapitalize': 'none',
                'autocomplete': 'username',
                'spellcheck': 'false',
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter password',
                'autocomplete': 'current-password',
            }
        )
    )

    error_messages = {
        'invalid_login': (
            'Enter the correct username/email and password. '
            'Check that your phone keyboard did not add spaces or capital letters.'
        ),
        'inactive': (
            'This account is not active yet. Please complete OTP verification '
            'and wait for admin approval.'
        ),
    }

    def clean_username(self):

        return self.cleaned_data.get(
            'username',
            ''
        ).strip()

    def clean(self):

        username_or_email = self.cleaned_data.get(
            'username',
            ''
        ).strip()

        password = self.cleaned_data.get('password')

        if username_or_email and password:

            lookup = {
                'email__iexact': username_or_email
            }

            if '@' not in username_or_email:
                lookup = {
                    'username__iexact': username_or_email
                }

            matching_user = User.objects.filter(
                **lookup
            ).first()

            username = username_or_email

            if matching_user is not None:
                username = matching_user.get_username()

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password
            )

            if self.user_cache is None:

                raise ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={
                        'username': self.username_field.verbose_name
                    },
                )

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

class StudentRegistrationForm(ReplacePendingAccountMixin, UserCreationForm):

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

        email = self.cleaned_data.get('email', '').strip().lower()

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

class EmployerRegistrationForm(ReplacePendingAccountMixin, UserCreationForm):

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

        email = self.cleaned_data.get('email', '').strip().lower()

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
