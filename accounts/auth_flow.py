from dataclasses import dataclass

from django.contrib.auth import authenticate, get_user_model


UserModel = get_user_model()


@dataclass
class LoginResult:
    user: object | None
    reason: str


def clean_login_value(value):
    if value is None:
        return ''

    return (
        str(value)
        .strip()
        .replace('\u200b', '')
        .replace('\u200c', '')
        .replace('\u200d', '')
        .replace('\ufeff', '')
    )


def find_user_by_identifier(identifier):
    identifier = clean_login_value(identifier)

    if not identifier:
        return None

    if '@' in identifier:
        return UserModel.objects.filter(email__iexact=identifier).first()

    return UserModel.objects.filter(username__iexact=identifier).first()


def authenticate_identifier(request, identifier, password):
    identifier = clean_login_value(identifier)
    password = clean_login_value(password)

    if not identifier or not password:
        return LoginResult(None, 'missing')

    user = find_user_by_identifier(identifier)

    if user is None:
        return LoginResult(None, 'not_found')

    active_user = authenticate(
        request,
        username=user.get_username(),
        password=password,
    )

    if active_user is not None:
        return LoginResult(active_user, 'ok')

    if user.check_password(password):
        return LoginResult(user, 'inactive_or_unverified')

    return LoginResult(None, 'bad_password')


def dashboard_redirect_name(user):
    if user.role == 'student':
        if not hasattr(user, 'student_profile'):
            return 'create_student_profile'
        return 'student_dashboard'

    if user.role == 'employer':
        if not hasattr(user, 'employer_profile'):
            return 'create_employer_profile'
        return 'employer_profile'

    return 'dashboard'
