"""
Django settings for precatorios project.

Multi-environment configuration supporting:
- Local (Windows development with SQLite)
- Test (EC2 with PostgreSQL) 
- Production (EC2 with PostgreSQL and S3)
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Environment Configuration
ENVIRONMENT = config('ENVIRONMENT', default='local')

# Environment-specific configuration
if ENVIRONMENT == 'local':
    # Local development (Windows) - Hardcoded values
    SECRET_KEY = '_-j533-d^w2s#0z6!6n&0_oxntro6rl=m2xca$kppy8l8*hxi5'
    DEBUG = True
    ALLOWED_HOSTS = ["*"]
else:
    # Test and Production environments - Use environment variables
    SECRET_KEY = config('SECRET_KEY')
    DEBUG = config('DEBUG', default=False, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'precapp',
]

# Add storages for S3 in non-local environments
if ENVIRONMENT in ['test', 'production']:
    INSTALLED_APPS.append('storages')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'precapp.middleware.UserTrackingMiddleware',
]

ROOT_URLCONF = 'precatorios.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'precapp' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'precatorios.wsgi.application'


# Database Configuration
# Environment-specific database settings
if ENVIRONMENT == 'local':
    # Local development (Windows) - SQLite with hardcoded values
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Test and Production - PostgreSQL with environment variables
    DATABASES = {
        'default': {
            'ENGINE': config('DATABASE_ENGINE'),
            'NAME': config('DATABASE_NAME'),
            'USER': config('DATABASE_USER'),
            'PASSWORD': config('DATABASE_PASSWORD'),
            'HOST': config('DATABASE_HOST'),
            'PORT': config('DATABASE_PORT', cast=int),
            'OPTIONS': {
                'connect_timeout': 60,
            }
        }
    }


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Date format settings for Brazilian localization
DATE_FORMAT = 'd/m/Y'
DATETIME_FORMAT = 'd/m/Y H:i'
SHORT_DATE_FORMAT = 'd/m/Y'
SHORT_DATETIME_FORMAT = 'd/m/Y H:i'

DATE_INPUT_FORMATS = [
    '%d/%m/%Y',     # Brazilian format: 31/12/2023
    '%d-%m-%Y',     # Alternative: 31-12-2023
    '%Y-%m-%d',     # ISO format: 2023-12-31 (fallback)
]

DATETIME_INPUT_FORMATS = [
    '%d/%m/%Y %H:%M:%S',    # 31/12/2023 14:30:00
    '%d/%m/%Y %H:%M',       # 31/12/2023 14:30
    '%d-%m-%Y %H:%M:%S',    # 31-12-2023 14:30:00
    '%d-%m-%Y %H:%M',       # 31-12-2023 14:30
    '%Y-%m-%d %H:%M:%S',    # ISO fallback
    '%Y-%m-%d %H:%M',       # ISO fallback
]


# Static files configuration
STATIC_URL = '/static/'

# Environment-specific static files settings
if ENVIRONMENT == 'local':
    # Local development (Windows) - Hardcoded paths
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    STATICFILES_DIRS = [
        BASE_DIR / 'precapp' / 'static',
    ]
else:
    # Test and Production on EC2 - Use environment variables
    STATIC_ROOT = config('STATIC_ROOT_PATH', default='/var/www/precatorios/static')
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, config('STATICFILES_DIRS_PATH', default='static')),
    ]

# Media files configuration
MEDIA_URL = '/media/'

# Environment-specific media storage
if ENVIRONMENT == 'local':
    # Local development (Windows) - Local filesystem with hardcoded path
    MEDIA_ROOT = BASE_DIR / 'media'
    USE_S3 = False
elif ENVIRONMENT in ['test', 'production']:
    # Test and Production environments
    USE_S3 = config('USE_S3', default=False, cast=bool)
    
    if USE_S3:
        # S3 Configuration for test/production
        AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
        AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
        AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
        AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
        
        # S3 Media files configuration
        # Use environment-specific folder structure in S3
        if ENVIRONMENT == 'test':
            AWS_LOCATION = 'media/test'
        else:
            AWS_LOCATION = 'media/production'
        
        AWS_DEFAULT_ACL = 'private'
        AWS_S3_FILE_OVERWRITE = False
        AWS_S3_OBJECT_PARAMETERS = {
            'CacheControl': 'max-age=86400',
        }
        
        # Use S3 for media files
        DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'
    else:
        # Fallback to local filesystem for test/production
        MEDIA_ROOT = config('MEDIA_ROOT_PATH', default='/var/www/precatorios/media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB in bytes
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB in bytes
FILE_UPLOAD_PERMISSIONS = 0o644

# Authentication settings
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Security Settings for Production
if ENVIRONMENT == 'production':
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
    SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
    SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
    SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
    SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)

# Logging Configuration
if ENVIRONMENT == 'local':
    # Local development (Windows) - Simple logging
    LOG_LEVEL = 'DEBUG'
else:
    # Test and Production - Environment-based logging
    LOG_LEVEL = config('LOG_LEVEL', default='INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log' if ENVIRONMENT == 'local' else '/var/log/precatorios/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': LOG_LEVEL,
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if ENVIRONMENT != 'local' else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'precapp': {
            'handlers': ['console', 'file'] if ENVIRONMENT != 'local' else ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# Environment-specific settings summary
print(f"🚀 Django starting in {ENVIRONMENT.upper()} environment")
if DEBUG:
    print(f"⚠️  DEBUG mode is ON")
else:
    print(f"🔒 DEBUG mode is OFF")
print(f"📊 Database: {DATABASES['default']['ENGINE'].split('.')[-1].upper()}")
if USE_S3:
    print(f"☁️  Media storage: AWS S3")
else:
    print(f"💾 Media storage: Local filesystem")
