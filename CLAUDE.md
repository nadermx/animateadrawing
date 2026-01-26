# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DjangoBase is a reusable Django 5.x project template with built-in user authentication, credits-based billing, multi-processor payments, and a custom database-driven translation system.

## Common Commands

```bash
# Setup
cp config_example.py config.py  # Configure before first run
pip install -r requirements.txt
python manage.py migrate
python manage.py set_languages  # Initialize available languages
python manage.py runserver

# Translations
python manage.py run_translation  # Translate untranslated TextBase entries via Google Translate API

# PayPal Setup (if using subscriptions)
python manage.py create_paypal_product
python manage.py create_paypal_plans
```

## Architecture

### Configuration
Settings split between `app/settings.py` (Django defaults) and `config.py` (secrets/env-specific). The `config.py` is gitignored - copy from `config_example.py`.

Key config values:
- `PROJECT_NAME` - Used in templates and emails
- `PROJECT_DOMAIN` - Your domain for email sending
- `EMAIL_*` - SMTP settings (uses native Postfix, not third-party services)

### Custom Translation System
**Not Django's built-in i18n.** Uses three models in `translations/`:
- `Language` - available languages (populated via `set_languages` command from JSON)
- `TextBase` - source text entries with `code_name` identifier and `translated` flag
- `Translation` - translated text per language

Usage in views: `Translation.get_text_by_lang('en')` returns dict of `{code_name: text}`. Add new text via admin at `Translations > Text bases`, then run `python manage.py run_translation`.

### User & Authentication
Custom user model `accounts.CustomUser` with:
- Email as username
- Credits system for usage-based billing
- Subscription tracking (`is_plan_active`, `next_billing_date`, `plan_subscribed`)
- Payment processor tokens stored per user

### Email System
Uses Django's native SMTP backend with local Postfix. See `EMAIL_SETUP.md` for:
- Postfix configuration
- DKIM/SPF/DMARC DNS setup
- Testing deliverability

For development, set in config.py:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Payment Processing
`finances/` supports Stripe, Square, PayPal. Plans defined in admin with `is_subscription` flag.

### View Pattern
Views use `GlobalVars.get_globals(request)` from `accounts/views.py` to get translation dict (`i18n`) and other settings. All templates receive this as `g` context variable.

### Frontend
- Bootstrap 5 (loaded via CDN)
- Custom styles in `static/css/styles.css`

### Infrastructure
- PostgreSQL database
- Redis for caching (`django-redis`) and job queues (`django-rq`)

## Project Structure

```
├── app/              # Django settings, URLs, utilities
├── accounts/         # Custom user model, authentication
├── core/             # Main views (index, auth pages, account)
├── contact_messages/ # Contact form
├── finances/         # Payment processing, plans
├── translations/     # Database translation system
├── templates/        # HTML templates (Bootstrap 5)
├── static/           # CSS, JS
└── ansible/          # Server deployment playbooks
```

## Creating a New Project from This Base

1. Clone the repository
2. Update `config.py` with your PROJECT_NAME, PROJECT_DOMAIN, and credentials
3. Update `DEFAULT_FROM_EMAIL` in config.py
4. Customize templates in `templates/`
5. Add your translation TextBase entries
6. Set up email DNS records (see EMAIL_SETUP.md)
