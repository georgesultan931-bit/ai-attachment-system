import re

from django import forms

from .models import (
    StudentProfile,
    AcademicQualification,
    WorkExperience,
    Referee
)


COUNTY_CHOICES = [
    ('', 'Select County'),
    ('Baringo', 'Baringo'),
    ('Kisumu', 'Kisumu'),
    ('Nairobi', 'Nairobi'),
    ('Nakuru', 'Nakuru'),
    ('Mombasa', 'Mombasa'),
    ('Uasin Gishu', 'Uasin Gishu'),
    ('Kakamega', 'Kakamega'),
    ('Kiambu', 'Kiambu'),
    ('Machakos', 'Machakos'),
    ('Meru', 'Meru'),
]

CONSTITUENCY_CHOICES = [
    ('', 'Select Constituency'),
    ('Baringo Central', 'Baringo Central'),
    ('Baringo North', 'Baringo North'),
    ('Kisumu Central', 'Kisumu Central'),
    ('Kisumu East', 'Kisumu East'),
    ('Westlands', 'Westlands'),
    ('Langata', 'Langata'),
    ('Nakuru Town East', 'Nakuru Town East'),
    ('Nakuru Town West', 'Nakuru Town West'),
    ('Nyali', 'Nyali'),
    ('Likoni', 'Likoni'),
]

SUB_COUNTY_CHOICES = [
    ('', 'Select Sub County'),
    ('Baringo Central', 'Baringo Central'),
    ('Baringo North', 'Baringo North'),
    ('Kisumu Central', 'Kisumu Central'),
    ('Kisumu East', 'Kisumu East'),
    ('Westlands', 'Westlands'),
    ('Langata', 'Langata'),
    ('Nakuru Town East', 'Nakuru Town East'),
    ('Nakuru Town West', 'Nakuru Town West'),
    ('Nyali', 'Nyali'),
    ('Likoni', 'Likoni'),
]

WARD_CHOICES = [
    ('', 'Select Ward'),
    ('Kabarnet', 'Kabarnet'),
    ('Sacho', 'Sacho'),
    ('Tenges', 'Tenges'),
    ('Kondele', 'Kondele'),
    ('Nyalenda', 'Nyalenda'),
    ('Kitisuru', 'Kitisuru'),
    ('Karen', 'Karen'),
    ('Biashara', 'Biashara'),
    ('Mkomani', 'Mkomani'),
    ('Likoni', 'Likoni'),
]

ETHNICITY_CHOICES = [
    ('', 'Select Ethnicity'),
    ('Kikuyu', 'Kikuyu'),
    ('Luhya', 'Luhya'),
    ('Kalenjin', 'Kalenjin'),
    ('Luo', 'Luo'),
    ('Kamba', 'Kamba'),
    ('Kisii', 'Kisii'),
    ('Meru', 'Meru'),
    ('Maasai', 'Maasai'),
    ('Turkana', 'Turkana'),
    ('Mijikenda', 'Mijikenda'),
]

TOWN_CHOICES = [
    ('', 'Select Town'),
    ('Kabarnet', 'Kabarnet'),
    ('Kisumu', 'Kisumu'),
    ('Nairobi', 'Nairobi'),
    ('Nakuru', 'Nakuru'),
    ('Mombasa', 'Mombasa'),
    ('Eldoret', 'Eldoret'),
    ('Kakamega', 'Kakamega'),
    ('Kericho', 'Kericho'),
    ('Naivasha', 'Naivasha'),
    ('Bungoma', 'Bungoma'),
]

INSTITUTION_CHOICES = [
    ('', 'Select Institution'),
    ('Baringo National Polytechnic', 'Baringo National Polytechnic'),
    ('Maseno University', 'Maseno University'),
    ('University of Nairobi', 'University of Nairobi'),
    ('Kenyatta University', 'Kenyatta University'),
    ('Moi University', 'Moi University'),
    ('Egerton University', 'Egerton University'),
    ('Kabarak University', 'Kabarak University'),
    ('Mount Kenya University', 'Mount Kenya University'),
    ('Kisumu National Polytechnic', 'Kisumu National Polytechnic'),
    ('Technical University of Kenya', 'Technical University of Kenya'),
]


KENYA_DIGIT_ERROR = 'this digit doesnt exit please enter valid digits'
KENYA_ID_PATTERN = re.compile(r'^\d{7,8}$')
HUDUMA_NUMBER_PATTERN = re.compile(r'^\d{8,14}$')
KRA_PIN_PATTERN = re.compile(r'^[A-Z]\d{9}[A-Z]$')


class StudentProfileForm(forms.ModelForm):

    class Meta:

        model = StudentProfile

        fields = [
            'salutation',
            'id_number',
            'huduma_number',
            'surname',
            'first_name',
            'other_names',
            'date_of_birth',
            'gender',
            'kra_pin',
            'nationality',
            'ethnicity',
            'disability',
            'home_county',
            'home_constituency',
            'sub_county',
            'home_ward',
            'postal_address',
            'postal_code',
            'town',
            'phone_number',
            'location',
            'alternative_contact_name',
            'alternative_contact_phone',
            'course',
            'institution',
            'skills',
            'bio',
            'github',
            'linkedin',
            'portfolio',
            'profile_picture',
            'cv',
        ]

        widgets = {
            'salutation': forms.Select(attrs={'class': 'form-select'}),
            'id_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Kenyan ID number',
                'inputmode': 'numeric',
                'pattern': '[0-9]{7,8}',
                'title': 'Enter 7 or 8 digits',
            }),
            'huduma_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional',
                'inputmode': 'numeric',
                'pattern': '[0-9]{8,14}',
                'title': 'Enter 8 to 14 digits',
            }),
            'surname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter surname'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'other_names': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter other names'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'kra_pin': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: A123456789B',
                'maxlength': '11',
                'style': 'text-transform: uppercase;',
            }),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter nationality'}),
            'ethnicity': forms.TextInput(attrs={'class': 'form-control', 'list': 'ethnicityList', 'placeholder': 'Select or type ethnicity'}),
            'disability': forms.Select(attrs={'class': 'form-select'}),
            'home_county': forms.TextInput(attrs={'class': 'form-control', 'list': 'countyList', 'placeholder': 'Select or type county'}),
            'home_constituency': forms.TextInput(attrs={'class': 'form-control', 'list': 'constituencyList', 'placeholder': 'Select or type constituency'}),
            'sub_county': forms.TextInput(attrs={'class': 'form-control', 'list': 'subCountyList', 'placeholder': 'Select or type sub county'}),
            'home_ward': forms.TextInput(attrs={'class': 'form-control', 'list': 'wardList', 'placeholder': 'Select or type ward'}),
            'postal_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal address'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal code'}),
            'town': forms.TextInput(attrs={'class': 'form-control', 'list': 'townList', 'placeholder': 'Select or type town'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter current location'}),
            'alternative_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternative contact name'}),
            'alternative_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter alternative contact phone'}),
            'course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Diploma in Computer Science'}),
            'institution': forms.TextInput(attrs={'class': 'form-control', 'list': 'institutionList', 'placeholder': 'Select or type institution'}),
            'skills': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Example: Python, Django, HTML, CSS, SQL'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Briefly describe yourself'}),
            'github': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'portfolio': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'cv': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        required_fields = [
            'salutation',
            'id_number',
            'surname',
            'first_name',
            'other_names',
            'date_of_birth',
            'gender',
            'kra_pin',
            'nationality',
            'ethnicity',
            'disability',
            'home_county',
            'home_constituency',
            'sub_county',
            'home_ward',
            'postal_address',
            'postal_code',
            'town',
            'phone_number',
            'location',
            'alternative_contact_name',
            'alternative_contact_phone',
            'course',
            'institution',
            'skills',
            'bio',
            'profile_picture',
            'cv',
        ]

        optional_fields = [
            'huduma_number',
            'github',
            'linkedin',
            'portfolio',
        ]

        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True

        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False

    def clean_id_number(self):

        id_number = (self.cleaned_data.get('id_number') or '').strip()
        normalized_id = re.sub(r'\s+', '', id_number)

        if not KENYA_ID_PATTERN.fullmatch(normalized_id):
            raise forms.ValidationError(KENYA_DIGIT_ERROR)

        return normalized_id

    def clean_huduma_number(self):

        huduma_number = (self.cleaned_data.get('huduma_number') or '').strip()

        if not huduma_number:
            return ''

        normalized_huduma = re.sub(r'\s+', '', huduma_number)

        if not HUDUMA_NUMBER_PATTERN.fullmatch(normalized_huduma):
            raise forms.ValidationError(KENYA_DIGIT_ERROR)

        return normalized_huduma

    def clean_kra_pin(self):

        kra_pin = (self.cleaned_data.get('kra_pin') or '').strip().upper()
        normalized_pin = re.sub(r'\s+', '', kra_pin)

        if not KRA_PIN_PATTERN.fullmatch(normalized_pin):
            raise forms.ValidationError(KENYA_DIGIT_ERROR)

        return normalized_pin

    def clean(self):

        cleaned_data = super().clean()
        salutation = cleaned_data.get('salutation')
        gender = cleaned_data.get('gender')

        salutation_gender_rules = {
            'Mr': 'male',
            'Mrs': 'female',
            'Miss': 'female',
        }

        expected_gender = salutation_gender_rules.get(salutation)

        if expected_gender and gender and gender != expected_gender:
            message = (
                'Salutation and gender do not match. Please start again from '
                'the Salutation field and enter correct personal details.'
            )
            self.add_error('salutation', message)
            self.add_error('gender', message)

        return cleaned_data


class AcademicQualificationForm(forms.ModelForm):

    class Meta:

        model = AcademicQualification

        fields = [
            'institution_name',
            'qualification',
            'course_name',
            'grade',
            'start_year',
            'end_year',
        ]

        widgets = {
            'institution_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Baringo National Polytechnic'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Diploma, Degree, Certificate'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Computer Science'}),
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Credit, Distinction, Second Upper'}),
            'start_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Example: 2022'}),
            'end_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Example: 2025'}),
        }


class WorkExperienceForm(forms.ModelForm):

    class Meta:

        model = WorkExperience

        fields = [
            'organization',
            'position',
            'start_date',
            'end_date',
            'responsibilities',
        ]

        widgets = {
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Maseno University'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: ICT Attachment Student'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsibilities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your responsibilities'}),
        }


class RefereeForm(forms.ModelForm):

    class Meta:

        model = Referee

        fields = [
            'full_name',
            'organization',
            'position',
            'phone_number',
            'email',
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Referee full name'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organization'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Position'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}),
        }
