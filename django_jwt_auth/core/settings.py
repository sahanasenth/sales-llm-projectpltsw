# =============================================================
#  core/settings.py
#  Central configuration file for the Django JWT Auth project.
#  All environment-specific settings should be moved to a .env
#  file in production (see python-decouple usage below).
# =============================================================

from pathlib import Path
from datetime import timedelta
from decouple import config   # reads values from .env / environment

# ─── Base directory ──────────────────────────────────────────
# Build paths like BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ─── Security ────────────────────────────────────────────────
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*']   # Restrict to your domain in production


# ─── Application definition ──────────────────────────────────
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',                    # Django REST Framework
    'rest_framework_simplejwt',          # JWT authentication library
    'rest_framework_simplejwt.token_blacklist',  # Enables token blacklisting on logout

    # Our custom apps
    'authentication',                    # Handles login, profile, etc.
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'


# ─── Database ────────────────────────────────────────────────
# Using SQLite for development. Switch to PostgreSQL in production.
# Example PostgreSQL config is commented out below.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (production) example:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME'),
#         'USER': config('DB_USER'),
#         'PASSWORD': config('DB_PASSWORD'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }


# ─── Password validation ─────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─── Internationalization ────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ─── Static files ────────────────────────────────────────────
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─── Django REST Framework Configuration ─────────────────────
# This block controls how DRF handles authentication, permissions,
# and response rendering across ALL API views by default.
REST_FRAMEWORK = {
    # Use JWT tokens for authenticating every API request
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    # By default, require authentication for all views.
    # Views that should be public must explicitly set:
    #   permission_classes = [AllowAny]
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    # Return clean JSON responses (no HTML browsable API in production)
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}


# ─── Simple JWT Configuration ─────────────────────────────────
# Fine-grained control over JWT token behaviour.
SIMPLE_JWT = {
    # ── Token Lifetimes ──────────────────────────────────────
    # Access token: short-lived (15 min) for security
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    # Refresh token: longer-lived (1 day) — used to get new access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),

    # ── Rotation & Blacklisting ──────────────────────────────
    # Issue a NEW refresh token each time /api/token/refresh/ is called.
    # The old one gets blacklisted automatically (requires token_blacklist app).
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,

    # ── Token Signing ────────────────────────────────────────
    'ALGORITHM': 'HS256',             # HMAC-SHA256 signing algorithm
    'SIGNING_KEY': SECRET_KEY,        # Uses Django's SECRET_KEY to sign tokens

    # ── Header settings ──────────────────────────────────────
    # Clients must send:  Authorization: Bearer <access_token>
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',

    # ── Token payload fields ─────────────────────────────────
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',

    # ── Token classes ────────────────────────────────────────
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}
