from .base import *
import sys

ALLOWED_HOSTS = ["news.viceroy.tech"]

# Database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        "NAME": 'news_aggregator',  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        "USER": "news_aggregator_user",
        "PASSWORD": "&?6<&MUXr3#r^,",
        "HOST": "localhost",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "5432",  # Set to empty string for default.
    }
}

SOCIAL_AUTH_POSTGRES_JSONFIELD = True


SECRET_KEY = os.getenv('SECRET_KEY') or sys.exit('SECRET_KEY environment variable is not set.')

# Email settings
# We are using HubSpot as email backend
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = ''
# EMAIL_PORT = ''
# EMAIL_HOST_USER = ''
# EMAIL_HOST_PASSWORD = ''


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, '../logs/django.log'),
            'maxBytes': 1024 * 1024 * 100,  # 100 mb
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
