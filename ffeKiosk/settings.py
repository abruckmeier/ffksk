import os
import logging
from decouple import config

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=lambda v: [s.strip() for s in v.split(',')])
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SESSION_EXPIRE_AT_BROWSER_CLOSE = config('SESSION_EXPIRE_AT_BROWSER_CLOSE', default=True, cast=bool)
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', cast=lambda v: [s.strip() for s in v.split(',')])
X_FRAME_OPTIONS = "SAMEORIGIN"

# DATABASE
DATABASES = {
    'old': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'myDatabase.sqlite3'),
    },
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT'),
    },
}

# Application definition

INSTALLED_APPS = [
    'widget_tweaks',
    'jchart',
    'django_db_logger',
    'django.contrib.humanize',
    'paypal.apps.PaypalConfig',
    'kiosk.apps.KioskConfig',
    'profil.apps.ProfilConfig',
    'ffeKiosk',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'ffeKiosk.urls'

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

WSGI_APPLICATION = 'ffeKiosk.wsgi.app'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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

AUTH_USER_MODEL = 'profil.KioskUser'
LOGIN_REDIRECT_URL = '/accounts/registrationStatus/'

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = False
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(BASE_DIR, 'static', 'static'))
STATICFILES_DIRS = [os.path.abspath(os.path.join(BASE_DIR, 'static'))]

# Slack Integration
SLACK_O_AUTH_TOKEN = config('SLACK_O_AUTH_TOKEN')
SLACK_VERIFICATION_TOKEN = config('SLACK_VERIFICATION_TOKEN')
ACTIVATE_SLACK_INTERACTION = config('ACTIVATE_SLACK_INTERACTION', cast=bool)
SLACK_SETTINGS = {
    'channelToPost': config('SLACK_CHANNEL_TO_POST', default='#kiosk_bot'),
    'inventoryChannelName': config('SLACK_INVENTORY_CHANNEL', default='kiosk'),
    'MaxBankBalance': 3000,  # Cent
    'MinBankBalance': 100,  # Cent
}

BACKUP = {
    'active_local_backup': config('ACTIVATE_LOCAL_BACKUP', cast=bool, default=False),
    'active_slack_backup': config('ACTIVATE_SLACK_BACKUP', cast=bool, default=False),
    'localBackupFolder': os.path.join(os.path.dirname(os.path.abspath(BASE_DIR)), 'backup'),
    'sendWeeklyBackupToUsers': config('SLACK_BACKUP_USERS_LIST', cast=lambda v: [s.strip() for s in v.split(',')]),
    'kioskbotChannels': config('SLACK_BACKUP_KIOSKBOT_CHANNELS', cast=lambda v: [s.strip() for s in v.split(',')]),
}

CONTACT = {
    'email': config('CONTACT_EMAIL'),
}

## PayPal (E-Mail) Integration
IMAP_HOST = config('IMAP_HOST', default=None)
IMAP_USERNAME = config('IMAP_USERNAME', default=None)
IMAP_PASSWORD = config('IMAP_PASSWORD', default=None)
IMAP_SEARCH_FROM_EMAIL = config('IMAP_SEARCH_FROM_EMAIL', default=None)

# Finanzielle Konstanten -> spaeter in den KioskBot geben
FINANZ = {
    'minProduktMarge': 0.00,  # vom VK-Preis
    'gewinnEK': 0.5,  # Wird beim Einpflegen vom Verwalter gutgeschrieben
    'gewinnVW': 0.1,  # Wird bei Produktverkauf gutgeschrieben
    'gewinnBank': 0.3,  # Bleibt als Ueberschuss in der Kasse, wird nicht bewegt.
    'gewinnAdmin': 0.1,  # Wird bei Produktverkauf gutgeschrieben
    'monUmverteilungAlle': 0.5,  # anteilig der User am pers. Umsatz
    'monUmverteilungAdmin': 0.5,
    'monNegUmverteilungAdmin': 1,
}

VIEWS = {
    'itemsInKontobewegungen': 10,
}

CRON_SECRET = config('CRON_SECRET')


# Logging
class CustomFormatter(logging.Formatter):
    def format(self, record):
        s = super().format(record)
        if '\n' in s:
            s = s.replace('\n', '\n........')
        return s


file_handlers = {
    'django_file': {
        'class': 'logging.FileHandler',
        'filename': os.path.join(LOGS_DIR, 'django.log'),
        'formatter': 'verbose',
        'encoding': 'utf8',
    },
    'paypal_mail_file': {
        'class': 'logging.FileHandler',
        'filename': os.path.join(LOGS_DIR, 'paypal_mail.log'),
        'formatter': 'verbose',
        'encoding': 'utf8',
    },
}

db_handler = {
    'db_log': {
        'level': 'DEBUG',
        'class': 'django_db_logger.db_log_handler.DatabaseLogHandler',
        'formatter': 'verbose',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            '()': CustomFormatter,
            'format': '{levelname} | {asctime} | {module} | {message}',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'simple': {
            'format': '%(levelname)s %(asctime)s %(message)s'
        },
    },
    'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                    },
                } | (file_handlers if config('LOG_TO_FILE', cast=bool, default=False) else {})
                | (db_handler if config('LOG_TO_DB', cast=bool, default=False) else {}),
    'loggers': {
        'django': {
            'handlers': ['console']
                        + (['django_file'] if config('LOG_TO_FILE', cast=bool, default=False) else [])
                        + (['db_log'] if config('LOG_TO_FILE', cast=bool, default=False) else []),
            'level': 'WARNING',
        },
        'paypal.paypal_mail': {
            'handlers': ['console']
                        + (['paypal_mail_file'] if config('LOG_TO_FILE', cast=bool, default=False) else [])
                        + (['db_log'] if config('LOG_TO_FILE', cast=bool, default=False) else []),
            'level': 'INFO',
        },
    },
}

DJANGO_DB_LOGGER_ADMIN_LIST_PER_PAGE = 50
DJANGO_DB_LOGGER_ENABLE_FORMATTER = True
