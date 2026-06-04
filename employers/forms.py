from django import forms

from .models import EmployerProfile


class EmployerProfileForm(forms.ModelForm):

    class Meta:

        model = EmployerProfile

        fields = [
            'company_name',
            'company_email',
            'company_phone',
            'company_location',
            'industry',
            'company_description',
            'website',
            'logo',
        ]

        widgets = {

            'logo': forms.ClearableFileInput(
    attrs={
        'class': 'form-control',
        'accept': 'image/*'
    }
),

            'company_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Enter company name'
                }
            ),

            'company_email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'company@example.com'
                }
            ),

            'company_phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Company phone number'
                }
            ),

            'company_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'City, Country'
                }
            ),

            'industry': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Technology, Healthcare, Finance...'
                }
            ),

            'company_description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 5,
                    'placeholder': 'Describe your company...'
                }
            ),

            'website': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://yourcompany.com'
                }
            ),

            'logo': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),
        }