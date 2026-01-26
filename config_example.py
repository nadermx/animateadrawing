# Project Settings
PROJECT_NAME = 'MyProject'
PROJECT_DOMAIN = 'example.com'  # Your domain (e.g., myproject.com)
ROOT_DOMAIN = 'http://localhost:8000'
DEBUG = True

# Google Translate API (for translations)
GOOGLE_API = ''

# Email Configuration (Native SMTP)
# For production, set up Postfix on your server with DKIM/SPF/DMARC
# See DNS_RECORDS_FOR_EMAIL.md for DNS setup
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'  # Use localhost for local Postfix
EMAIL_PORT = 25  # Standard SMTP port (or 587 for TLS relay)
EMAIL_USE_TLS = False  # Set True if using external relay
EMAIL_HOST_USER = ''  # Leave empty for local Postfix
EMAIL_HOST_PASSWORD = ''  # Leave empty for local Postfix
DEFAULT_FROM_EMAIL = 'MyProject <no-reply@example.com>'  # Update with your domain
SERVER_EMAIL = 'server@example.com'  # For error emails

# For development, use console backend to see emails in terminal:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Database
DATABASE = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'myproject',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Payment Processors (enable the ones you need)
PROCESSORS = [
    'stripe',
    # 'squareup',
    # 'paypal',
    # 'coinbase',
]

# Stripe
STRIPE = {
    'pk': 'pk_test_xxx',
    'sk': 'sk_test_xxx',
}

# Square
SQUARE_UP = {
    'env': 'sandbox',
    'id': 'sandbox-xxx',
    'secret': 'xxx',
}

# PayPal
PAYPAL_KEYS = {
    'id': 'your-paypal-client-id',
    'secret': 'your-paypal-secret',
    'api': 'https://api.sandbox.paypal.com',
    'env': 'sandbox',
}

# Rate Limiting
RATE_LIMIT = 10
FILES_LIMIT = 2147483648  # 2GB

# Script Version (for cache busting)
SCRIPT_VERSION = '1.0.0'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'error.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
