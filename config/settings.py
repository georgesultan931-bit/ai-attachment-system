"""
Django settings for config project.
"""

import os

import certifi

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

os.environ.setdefault(
    'SSL_CERT_FILE',
    certifi.where()
)

os.environ.setdefault(
    'REQUESTS_CA_BUNDLE',
    certifi.where()
)


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-s5vx9(pkiy-&g3fcvkf226tv&1y&pxs%=dwn%b8g83pzjvgch$'
)

DEBUG = os.environ.get(
    'DJANGO_DEBUG',
    'True'
).lower() == 'true'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'DJANGO_ALLOWED_HOSTS',
        '*'
    ).split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        'DJANGO_CSRF_TRUSTED_ORIGINS',
        ''
    ).split(',')
    if origin.strip()
]

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '3600'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        'False'
    ).lower() == 'true'
    SECURE_HSTS_PRELOAD = os.environ.get(
        'SECURE_HSTS_PRELOAD',
        'False'
    ).lower() == 'true'


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'accounts',
    'students',
    'employers',
    'internships',
    'matching',
    'notifications',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

try:
    import whitenoise
except ImportError:
    whitenoise = None

if whitenoise is not None:
    MIDDLEWARE.insert(
        1,
        'whitenoise.middleware.WhiteNoiseMiddleware'
    )


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.notification_count',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

if os.environ.get('DATABASE_URL'):
    import dj_database_url

    DATABASES['default'] = dj_database_url.parse(
        os.environ['DATABASE_URL'],
        conn_max_age=600
    )


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },

    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

if whitenoise is not None:
    STORAGES = {
        'default': {
            'BACKEND': 'django.core.files.storage.FileSystemStorage',
        },
        'staticfiles': {
            'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
        },
    }


MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


AUTH_USER_MODEL = 'accounts.User'


LOGIN_URL = 'login'

LOGIN_REDIRECT_URL = 'dashboard'

LOGOUT_REDIRECT_URL = 'login'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Email Configuration - Development
# OTP emails will appear in the terminal while testing.

EMAIL_BACKEND = 'notifications.email_backend.LocalSmtpEmailBackend'

# Local development workaround for networks/antivirus tools that intercept
# smtp.gmail.com with a self-signed certificate. Disable this in production.
EMAIL_ALLOW_INSECURE_SMTP_SSL = os.environ.get(
    'EMAIL_ALLOW_INSECURE_SMTP_SSL',
    str(DEBUG)
).lower() == 'true'

DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL',
    'noreply@aiinternship.local'
)
