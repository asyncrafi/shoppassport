from .base import *
import dj_database_url

print("🔧 Running in DEVELOPMENT mode")

DEBUG = True

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS_DEV")

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True

# Database for development

if env('DATABASE_URL'):
    # Production: Use DATABASE_URL from Render
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Local Development: Use individual vars
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env("POSTGRES_PORT"),
        }
    }

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": env("POSTGRES_DB"),
#         "USER": env("POSTGRES_USER"),
#         "PASSWORD": env("POSTGRES_PASSWORD"),
#         "HOST": env("POSTGRES_HOST"),
#         "PORT": env("POSTGRES_PORT"),
#     }
# }

EMAIL_HOST = env.str('EMAIL_HOST_DEV', default='smtp4dev')  # For string values
EMAIL_PORT = env.int('EMAIL_PORT_DEV', default=25)          # For integer values
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS_DEV', default=False)  # For boolean values
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER_DEV', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD_DEV', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL_DEV', default='no-reply@example.com')

# BREVO_API_KEY = env.str('BREVO_API_KEY')
# BREVO_FROM_EMAIL = env.str('BREVO_FROM_EMAIL')
# BREVO_FROM_NAME = env.str('BREVO_FROM_NAME')

# MAILGUN_API_KEY = env.str("MAILGUN_API_KEY")
# MAILGUN_DOMAIN = env.str("MAILGUN_DOMAIN")
# MAILGUN_FROM_EMAIL = env.str("MAILGUN_FROM_EMAIL")
# MAILGUN_FROM_NAME = env.str("MAILGUN_FROM_NAME")

# Development logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


