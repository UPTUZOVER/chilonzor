import os
import sys
import importlib.util
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


def env_int(name, default=0):
    value = os.getenv(name)
    if value is None or not str(value).strip():
        return default
    return int(value)


def env_str(name, default=""):
    value = os.getenv(name)
    if value is None or not str(value).strip():
        return default
    return str(value).strip()


def module_available(module_name):
    return importlib.util.find_spec(module_name) is not None


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-8(o0sv574nay#9mi(g3do!!qjwu4k4g5cll6m-rz!*+kn19tv*",
)
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "*") or ["*"]

SESSION_COOKIE_AGE = 1800

# Foydalanuvchi brauzerni yopishi bilan uning akkauntdagi sessiyasi avtomatik tugatiladi
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "app",
    "apk",
]

HAS_WHITENOISE = module_available("whitenoise")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "app.middleware.UiLanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apk.middleware.ApkOnlyAccessMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if HAS_WHITENOISE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "chilonzor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "app.context_processors.ui_i18n",
                "apk.context_processors.apk_nav",
                        ],
        },
    },
]

WSGI_APPLICATION = "chilonzor.wsgi.application"


# Baza tanlash:
#   - Docker ichida       -> PostgreSQL (avvalgi sozlamalar bilan bir xil)
#   - Lokal kompyuterda   -> sqlite (chilonzor_db.sqlite3), hech qanday sozlash kerak emas
# Istalgan holatda DB_ENGINE / POSTGRES_* / SQLITE_NAME env orqali bekor qilish mumkin.
RUNNING_IN_DOCKER = Path("/.dockerenv").exists() or env_bool("RUNNING_IN_DOCKER", False)
DB_ENGINE = env_str("DB_ENGINE", "postgresql" if RUNNING_IN_DOCKER else "sqlite").lower()

if DB_ENGINE.startswith("postgres"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_str("POSTGRES_DB", "chilonzor_db"),
            "USER": env_str("POSTGRES_USER", "postgres"),
            "PASSWORD": env_str("POSTGRES_PASSWORD", "postgres123"),
            "HOST": env_str("POSTGRES_HOST", "chilonzor_postgres"),
            "PORT": env_str("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 0),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(env_str("SQLITE_NAME", str(BASE_DIR / "chilonzor_db.sqlite3"))),
        }
    }
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
USE_MANIFEST_STATIC_FILES = env_bool(
    "USE_MANIFEST_STATIC_FILES",
    (not DEBUG) and ("test" not in sys.argv),
)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            (
                "whitenoise.storage.CompressedManifestStaticFilesStorage"
                if USE_MANIFEST_STATIC_FILES
                else "whitenoise.storage.CompressedStaticFilesStorage"
            )
            if HAS_WHITENOISE
            else "django.contrib.staticfiles.storage.StaticFilesStorage"
        ),
    },
}


DEFAULT_CSRF_TRUSTED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "https://localhost",
    "https://127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = list(
    dict.fromkeys(
        DEFAULT_CSRF_TRUSTED_ORIGINS + env_list("CSRF_TRUSTED_ORIGINS")
    )
)

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
LOGIN_FAILURE_LIMIT = env_int("LOGIN_FAILURE_LIMIT", 7)
LOGIN_LOCKOUT_HOURS = env_int("LOGIN_LOCKOUT_HOURS", 1)
TRUST_X_FORWARDED_FOR = env_bool("TRUST_X_FORWARDED_FOR", False)
TRUSTED_PROXY_HOPS = env_int("TRUSTED_PROXY_HOPS", 1)
TRUSTED_PROXY_IPS = env_list("TRUSTED_PROXY_IPS")

SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if env_bool("USE_X_FORWARDED_PROTO", True)
    else None
)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", not DEBUG)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Botdan keladigan APK fayl uchun eng katta hajm (MB). Veb-server (nginx va h.k.)
# ham shu hajmdagi so'rovni o'tkazishi kerak.
APK_MAX_UPLOAD_MB = env_int("APK_MAX_UPLOAD_MB", 200)
