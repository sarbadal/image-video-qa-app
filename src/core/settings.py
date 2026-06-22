"""Django settings for core project."""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(',') if item.strip()]


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-&_x1h(12ehoyt7qyhm%hhz=77vhx#bj=@-y()3si#zj(*y-*3+',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS', ['127.0.0.1', 'localhost'])
CSRF_TRUSTED_ORIGINS = _env_list('CSRF_TRUSTED_ORIGINS', [])

AUTH_USER_MODEL = 'accounts.CustomUser'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'django_cleanup.apps.CleanupConfig',
    'import_export',
    'accounts',
    'users',
    'image',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.getenv('SQLITE_PATH', str(BASE_DIR / 'db.sqlite3')),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

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


AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'table'

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_URL = os.getenv('STATIC_URL', '/static/')

STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

USE_GCS_MEDIA = _env_bool('USE_GCS_MEDIA', False)
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', '').strip()
GS_MEDIA_PREFIX = os.getenv('GS_MEDIA_PREFIX', 'media').strip('/').strip() or 'media'

if USE_GCS_MEDIA:
    if not GS_BUCKET_NAME:
        raise RuntimeError('GS_BUCKET_NAME must be set when USE_GCS_MEDIA=True')
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
    }
    GS_LOCATION = GS_MEDIA_PREFIX
    GS_DEFAULT_ACL = None
    GS_QUERYSTRING_AUTH = _env_bool('GS_QUERYSTRING_AUTH', False)
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/{GS_MEDIA_PREFIX}/'
else:
    STORAGES['default'] = {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    }
    MEDIA_ROOT = BASE_DIR / 'media'
    MEDIA_URL = '/media/'

EXIF_PATH = Path(os.getenv('EXIF_PATH', str(BASE_DIR / 'exiftool' / 'exiftool.exe')))

# Centralized defaults for image table sliders.
IMAGE_TABLE_SLIDER_DEFAULTS = {
    'zoom': 50,
    'threshold': 150,
    'r': 250,
    'g': 250,
    'b': 250,
}