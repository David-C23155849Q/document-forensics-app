"""
Base Django settings for the Word Forensics System.

All forensic thresholds are read from environment variables so that
nothing important is hard-coded. See .env.example for the full list.
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.getenv("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
    # local apps
    "apps.accounts",
    "apps.assignments",
    "apps.submissions",
    "apps.sessions",
    "apps.snapshots",
    "apps.events",
    "apps.forensic",
    "apps.ml_analysis",
    "apps.reports",
    "apps.audit",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.AuditLogMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------
# Database. SQLite now; models avoid SQLite-specific features so migrating
# to PostgreSQL later only requires changing this dict (and running
# `migrate` against the new engine) - no application rewrite needed.
# --------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
).split(",")

# I have to remember to change this to False in production, but for now, I want to avoid CORS issues during development.
CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# --------------------------------------------------------------------------
# Forensic configuration. These are read at runtime by the forensic engine
# so thresholds are never hard-coded into detection logic (see section 56
# of the spec). Values are defaults; override via environment / admin.
# --------------------------------------------------------------------------
FORENSIC_CONFIG = {
    "SNAPSHOT_INTERVAL_SECONDS": int(os.getenv("SNAPSHOT_INTERVAL_SECONDS", 1)),
    "FULL_SNAPSHOT_INTERVAL_SECONDS": int(os.getenv("FULL_SNAPSHOT_INTERVAL_SECONDS", 30)),
    "LARGE_INSERTION_WORD_THRESHOLD": int(os.getenv("LARGE_INSERTION_WORD_THRESHOLD", 100)),
    "MEDIUM_INSERTION_WORD_THRESHOLD": int(os.getenv("MEDIUM_INSERTION_WORD_THRESHOLD", 20)),
    "IDLE_THRESHOLD_SECONDS": int(os.getenv("IDLE_THRESHOLD_SECONDS", 120)),
    "SYNC_INTERVAL_SECONDS": int(os.getenv("SYNC_INTERVAL_SECONDS", 10)),
    "MAX_BATCH_SIZE": int(os.getenv("MAX_BATCH_SIZE", 100)),
    "RETENTION_SNAPSHOTS_MONTHS": int(os.getenv("RETENTION_SNAPSHOTS_MONTHS", 12)),
    "RETENTION_EVENTS_MONTHS": int(os.getenv("RETENTION_EVENTS_MONTHS", 24)),
    "RETENTION_REPORTS_MONTHS": int(os.getenv("RETENTION_REPORTS_MONTHS", 24)),
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
