from dataclasses import dataclass
from django.contrib.auth import get_user_model

UserModel = get_user_model()

PHONE_FORMATTING_CHARACTERS = {
    '\u00ad',  # soft hyphen
    '\u200b',  # zero-width space
    '\u200c',  # zero-width non-joiner
    '\u200d',  # zero-width joiner
    '\u200e',  # left-to-right mark
    '\u200f',  # right-to-left mark
    '\u202a',  # left-to-right embedding
    '\u202b',  # right-to-left embedding
    '\u202c',  # pop directional formatting
    '\u202d',  # left-to-right override
    '\u202e',  # right-to-left override
    '\u2060',  # word joiner
    '\u2066',  # left-to-right isolate
    '\u2067',  # right-to-left isolate
    '\u2068',  # first strong isolate
    '\u2069',  # pop directional isolate
    '\ufeff',  # byte order mark
}


@dataclass
class LoginResult:
    user: object | None
    reason: str


def clean_login_value(value, is_password=False):
    """
    Cleans inputs from hidden phone formatting.
    The default keeps older callers working while allowing password fields to
    opt out of whitespace trimming.
    """
    if value is None:
        return ''

    cleaned = ''.join(
        character
        for character in str(value)
        if character not in PHONE_FORMATTING_CHARACTERS
    )

    # Only remove leading/trailing spaces for the username/email field
    if not is_password:
        cleaned = cleaned.strip()

    return cleaned


def find_user_by_identifier(identifier):
    identifier = clean_login_value(identifier, is_password=False)

    if not identifier:
        return None

    # Handle case-insensitive database queries smoothly
    if '@' in identifier:
        return UserModel.objects.filter(email__iexact=identifier).first()

    return UserModel.objects.filter(username__iexact=identifier).first()


def authenticate_identifier(request, identifier, password):
    # Clean the parameters explicitly using the flags
    identifier = clean_login_value(identifier, is_password=False)
    password = clean_login_value(password, is_password=True)

    if not identifier or not password:
        return LoginResult(None, 'missing')

    user = find_user_by_identifier(identifier)

    if user is None:
        return LoginResult(None, 'not_found')

    # Directly check the password string matching bypasses case conflicts
    if user.check_password(password):
        if user.is_active:
            return LoginResult(user, 'ok')
        return LoginResult(user, 'inactive_or_unverified')

    return LoginResult(None, 'bad_password')


def has_student_profile(user):
    return hasattr(user, 'studentprofile')


def has_employer_profile(user):
    return hasattr(user, 'employerprofile')


def dashboard_redirect_name(user):
    if user.role == 'student':
        if not has_student_profile(user):
            return 'create_student_profile'
        return 'student_dashboard'

    if user.role == 'employer':
        if not has_employer_profile(user):
            return 'create_employer_profile'
        return 'employer_profile'

    return 'dashboard'
