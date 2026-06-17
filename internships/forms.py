from django import forms
from django.utils import timezone

from .models import (
    InternshipOpportunity,
    Application,
    ApplicationMessage
)


class InternshipOpportunityForm(forms.ModelForm):

    class Meta:

        model = InternshipOpportunity

        fields = [
            'company_name',
            'company_email',
            'company_image',
            'title',
            'internship_type',
            'description',
            'required_skills',
            'location',
            'slots_available',
            'deadline',
            'status',
        ]

        widgets = {

            'company_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Company name for this opportunity'
                }
            ),

            'company_email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Company email for this opportunity'
                }
            ),

            'company_image': forms.ClearableFileInput(
                attrs={
                    'class': 'form-control',
                    'accept': 'image/*'
                }
            ),

            'title': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'internship_type': forms.Select(
                attrs={'class': 'form-control'}
            ),

            'description': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4
                }
            ),

            'required_skills': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Example: Python, Django, Excel, Communication, Data analysis'
                }
            ),

            'location': forms.TextInput(
                attrs={'class': 'form-control'}
            ),

            'slots_available': forms.NumberInput(
                attrs={'class': 'form-control'}
            ),

            'deadline': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),

            'status': forms.Select(
                attrs={'class': 'form-control'}
            ),
        }

        labels = {
            'company_image': 'Company image for this opportunity',
        }

        help_texts = {
            'required_skills': (
                'Separate each required skill with a comma so students can see '
                'which skills they meet and which ones are missing.'
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_name'].required = True
        self.fields['company_email'].required = True

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')

        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError(
                'Deadline cannot be in the past.'
            )

        return deadline


class InterviewScheduleForm(forms.ModelForm):

    class Meta:

        model = Application

        fields = [
            'interview_date',
            'interview_time',
            'interview_location',
            'interview_notes',
        ]

        widgets = {

            'interview_date': forms.DateInput(
                attrs={
                    'class': 'form-control',
                    'type': 'date'
                }
            ),

            'interview_time': forms.TimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'time'
                }
            ),

            'interview_location': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Office Address or Google Meet Link'
                }
            ),

            'interview_notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Additional instructions for candidate'
                }
            ),
        }


class ApplicationMessageForm(forms.ModelForm):

    class Meta:

        model = ApplicationMessage

        fields = [
            'message',
        ]

        widgets = {
            'message': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Write a clear message about this application...'
                }
            ),
        }
