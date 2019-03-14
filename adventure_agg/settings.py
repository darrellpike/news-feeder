# Django settings for adventure_agg project.

import os

DEBUG = True

ADMINS = (
    ("dave", "dncrane@gmail.com"),
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        "NAME": "db.sqlite3",  # Or path to database file if using sqlite3.
        # The following settings are not used with sqlite3:
        "USER": "",
        "PASSWORD": "",
        "HOST": "",  # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        "PORT": "",  # Set to empty string for default.
    }
}

# EMAIL_HOST = 'smtp.sendgrid.net'
# EMAIL_HOST_USER = 'app17588645@heroku.com'
# EMAIL_HOST_PASSWORD = 'uewlclev'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

DEFAULT_FROM_EMAIL = "brenden@plantdietlife.com"  # TODO

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [".herokuapp.com", "plantdietlife.com", "www.plantdietlife.com"]  # TODO

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = "America/Chicago"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# PREPEND_WWW = True

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ""

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ""

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ""

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"

# Additional locations of static files
STATICFILES_DIRS = [os.path.join(BASE_DIR, "../posts/static/")]
STATIC_URL = "/static/"

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = "wg_j9-=0sdlf!ce_4ui1&e#unco^s9+@(^z!9@*)@bzd=6#47&"


MIDDLEWARE_CLASSES = (
    #'sslify.middleware.SSLifyMiddleware',#make sure this SSLify is the first middleware class
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)
# INTERNAL_IPS = ('127.0.0.1', )
ROOT_URLCONF = "adventure_agg.urls"

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = "adventure_agg.wsgi.application"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, '../posts/templates/')],
        #'APP_DIRS': True,
        'OPTIONS': {
            'debug': True,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'posts.custom_context_processors.config_settings'
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.eggs.Loader'
            ]
        }
    }
]


INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "posts",  # must be before admin to override password reset templates
    "django.contrib.admin",
    "registration",
    "mptt",
    #'configstore', #requires site to be defined or something? can't have this in initial migrate.
    #'south', #todo: delete this
    "sanitizer",
    "el_pagination",
    #    'debug_toolbar',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)

SESSION_COOKIE_AGE = 604800  # cookies should expire in 1 week, in seconds

DEBUG_TOOLBAR_PANELS = (
    "debug_toolbar.panels.version.VersionDebugPanel",
    "debug_toolbar.panels.timer.TimerDebugPanel",
    "debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel",
    "debug_toolbar.panels.headers.HeaderDebugPanel",
    "debug_toolbar.panels.request_vars.RequestVarsDebugPanel",
    "debug_toolbar.panels.template.TemplateDebugPanel",
    "debug_toolbar.panels.sql.SQLDebugPanel",
    "debug_toolbar.panels.signals.SignalDebugPanel",
    "debug_toolbar.panels.logger.LoggingPanel",
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"require_debug_false": {"()": "django.utils.log.RequireDebugFalse"}},
    "handlers": {
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        }
    },
}

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"

# Heroku stuff
# Parse database configuration from $DATABASE_URL
# import dj_database_url
# DATABASES['default'] =  dj_database_url.config()

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Allow all host headers
ALLOWED_HOSTS = ["*"]

# comment out the following for running locally

# Static asset configuration
# import os

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# STATIC_ROOT = "static"
# STATIC_URL = "/static/"

# STATICFILES_DIRS = (os.path.join(BASE_DIR, "../posts/static"),)

