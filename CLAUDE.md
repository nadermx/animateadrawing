# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Animate a Drawing** (animateadrawing.com) is a Django-based web application that allows users to animate their drawings using AI. Users upload drawings, auto-detect character poses via MediaPipe, apply motion presets or AI-generated animations, and export to video formats (MP4, WebM, GIF).

## Common Commands

```bash
# Setup
cp config_example.py config.py  # Configure before first run
pip install -r requirements.txt
python manage.py migrate
python manage.py set_languages  # Initialize translation languages
python manage.py runserver

# Background workers (for animation processing)
python manage.py rqworker default high low

# Translations
python manage.py run_translation  # Auto-translate TextBase entries (needs Google API key)

# Collect static files (for production)
python manage.py collectstatic --noinput
```

## Deployment

**Production:** 140.82.28.166 (Vultr, Ubuntu 24.04) - https://animateadrawing.com

Always use Ansible for server operations. **IMPORTANT:** Run from `/home/john/animateadrawing/ansible` directory.

```bash
# FULL DEPLOY (always use this - includes collectstatic)
ansible -i servers all -m shell -a "cd /home/www/animateadrawing && git pull && /home/www/animateadrawing/venv/bin/python manage.py collectstatic --noinput" --become --become-user=animateadrawing && ansible -i servers all -m shell -a "supervisorctl restart animateadrawing" --become

# Individual commands if needed:

# Deploy code only
ansible -i servers all -m shell -a "cd /home/www/animateadrawing && git pull" --become --become-user=animateadrawing

# Collect static files (REQUIRED after adding images, CSS, JS)
ansible -i servers all -m shell -a "/home/www/animateadrawing/venv/bin/python /home/www/animateadrawing/manage.py collectstatic --noinput" --become --become-user=animateadrawing

# Restart app
ansible -i servers all -m shell -a "supervisorctl restart animateadrawing" --become

# Run migrations
ansible -i servers all -m shell -a "/home/www/animateadrawing/venv/bin/python /home/www/animateadrawing/manage.py migrate" --become --become-user=animateadrawing

# Check logs
ansible -i servers all -m shell -a "tail -50 /var/log/animateadrawing/animateadrawing.err.log" --become

# Full initial deployment
ansible-playbook -i servers djangodeployubuntu20.yml
```

**NOTE:** If you add or modify static files (images, CSS, JS), `collectstatic` MUST be run or they won't appear on production.

**Server paths:**
- App: `/home/www/animateadrawing`
- Logs: `/var/log/animateadrawing/`
- Nginx: `/etc/nginx/sites-available/animateadrawing.conf`
- Supervisor: `/etc/supervisor/conf.d/animateadrawing.conf`

## Architecture

### Apps
- `animator/` - Main animation functionality (models, views, AI services)
- `accounts/` - Custom user model (email-based), credits system, authentication
- `core/` - Homepage and static pages (about, pricing, FAQ, examples, etc.)
- `finances/` - Payment processing (Stripe, Square, PayPal), plans, subscriptions
- `translations/` - Database-driven translation system (not Django i18n)
- `contact_messages/` - Contact form handling

### Animator App Services
```
animator/services/
├── pose_detection.py    # MediaPipe pose detection
├── image_processing.py  # Background removal (rembg/U2-Net)
├── motion_generation.py # Motion presets and AI generation
├── renderer.py          # Animation rendering to video (FFmpeg)
├── voice_synthesis.py   # TTS using gTTS
├── lipsync.py           # Lip sync from audio
└── image_generation.py  # AI background generation (Stable Diffusion)
```

### Key Models
- `Project` - Container for animation projects (quick, short, medium, full-length)
- `Character` - Uploaded drawing with rig/pose data
- `Scene` - Individual scene with background and camera settings
- `Animation` - Animation applied to character (preset or custom keyframes)
- `MotionPreset` - Pre-made or user motion presets
- `Export` - Rendered animation output

### Configuration
Settings split between `app/settings.py` (Django defaults) and `config.py` (secrets/env-specific).

### API Endpoints
Animator API endpoints prefixed with `/animator/api/`:
- `POST /api/characters/<id>/detect/` - Auto-detect character pose
- `POST /api/characters/<id>/rig/` - Save character rig
- `GET /api/scenes/<id>/data/` - Get scene data as JSON
- `POST /api/scenes/<id>/save/` - Save scene data
- `POST /api/animations/generate/` - Generate motion from text prompt
- `GET /api/export/<id>/status/` - Check export progress

### Background Tasks (django-rq)
- `detect_character_rig` - AI pose detection
- `process_character_image` - Background removal
- `generate_motion_from_prompt` - AI motion generation
- `render_export` - Video rendering
- `generate_background` - AI background generation
- `synthesize_voice` - Text-to-speech
- `generate_lipsync_data` - Lip sync from audio

### View Pattern
All views use `GlobalVars.get_globals(request)` from `accounts/views.py` which returns:
- `i18n` dict - translations for current language
- `user` - current user
- Other global settings

Templates receive this as `g` context variable: `{{ g.i18n.code_name }}`

### Translation System
Uses custom database-driven translations (not Django i18n):
1. Add `TextBase` entries in admin with `code_name` and English `text`
2. Run `python manage.py run_translation` to auto-translate
3. Use in templates: `{{ g.i18n.your_code_name }}`

## Dependencies

### Required
- Django 5.x, PostgreSQL, Redis, FFmpeg

### AI/ML (install based on features)
- `opencv-python-headless` - Image processing
- `mediapipe` - Pose detection
- `rembg` - Background removal
- `gTTS` - Voice synthesis
- `diffusers` + `torch` - Stable Diffusion (optional, GPU required)

## Frontend
- Bootstrap 5 (CDN)
- Custom JavaScript for canvas-based rig editor, drag-drop upload, animation preview, timeline editor

## User & Payment System
Custom user model `accounts.CustomUser`:
- Email as username
- Credits system for usage-based billing
- Subscription tracking (`is_plan_active`, `next_billing_date`, `plan_subscribed`)

Payment processors in `finances/`: Stripe, Square, PayPal. Plans defined in admin.

## Email System

Self-hosted transactional email using Postfix + OpenDKIM on `mail.animateadrawing.com`.

### Configuration
- **Sending domain:** `mail.animateadrawing.com` (NOT the main domain)
- **From address:** `Animate a Drawing <no-reply@mail.animateadrawing.com>`
- **Server:** Postfix with OpenDKIM for DKIM signing
- **Django backend:** `django.core.mail.backends.smtp.EmailBackend` via localhost:25

### DNS Records (DigitalOcean)
```
A     mail.animateadrawing.com           → 140.82.28.166
TXT   mail.animateadrawing.com           → v=spf1 ip4:140.82.28.166 a ~all
TXT   _dmarc.mail.animateadrawing.com    → v=DMARC1; p=none; rua=mailto:postmaster@mail.animateadrawing.com; fo=1
TXT   mail._domainkey.mail.animateadrawing.com → v=DKIM1; k=rsa; p=...
```

### Sending Email
Use `app/utils.py` `Utils.send_email()`:
```python
from app.utils import Utils
Utils.send_email(
    recipients=['user@example.com'],
    subject='Welcome!',
    template='email-verification',  # templates/mailing/email-verification.html
    data={'code': '123456', 'user': user}
)
```

### Monitoring
```bash
# Check mail logs
ansible -i servers all -m shell -a "tail -50 /var/log/mail.log" --become

# Check DKIM signing
ansible -i servers all -m shell -a "grep DKIM /var/log/mail.log | tail -10" --become

# Check mail queue
ansible -i servers all -m shell -a "mailq" --become

# Test DKIM key
ansible -i servers all -m shell -a "opendkim-testkey -d mail.animateadrawing.com -s mail -vvv" --become
```

### Troubleshooting
- **DKIM not signing:** Check `/etc/opendkim/SigningTable` has `*@mail.animateadrawing.com`
- **Email going to spam:** Verify SPF/DKIM/DMARC records with mail-tester.com
- **Loops back error:** Don't send to `@mail.animateadrawing.com` addresses (no inbox configured)

### Email Forwarding
- `hello@animateadrawing.com` → forwards to `john@nader.mx`
- Virtual aliases configured in `/etc/postfix/virtual`

## API Architecture

### GPU API Backend
External GPU processing at `api.animateadrawing.com` (38.248.6.142):
- `/v1/animate/` - Submit animation job (POST with image + motion preset)
- `/v1/animate/results/` - Poll for job status/results

The main site proxies `/api/v1/*` to the GPU backend via nginx.

### Internal API Endpoints
- `/api/accounts/api/deduct/` - Credit verification/deduction for GPU API
- `/account/api/deduct/` - Compatibility alias (GPU backend calls this path)
- `/api/accounts/rate_limit/` - Rate limit checking
- `/animator/api/*` - Animation editor APIs (characters, scenes, etc.)

### Related Projects
- `/home/john/drawinganimator/` - Simpler animation site using the same GPU backend
- `/home/john/texttospeechai/` - TTS processing using same GPU server
- `/home/john/PycharmProjects/api.imageeditor.ai/` - The GPU API server itself

## GPU Infrastructure

This project uses the shared GPU server for heavy processing tasks.

### GPU Server Details
- **Server**: 38.248.6.142 (api.imageeditor.ai = api.animateadrawing.com)
- **Hardware**: 4x Tesla P40 (24GB VRAM each, 96GB total)
- **API Endpoint**: https://api.animateadrawing.com/v1/* (alias to api.imageeditor.ai)

### Central Documentation
For complete GPU infrastructure documentation, see:
- `/home/john/ai/CLAUDE.md` - Central GPU infrastructure docs
- `/home/john/PycharmProjects/api.imageeditor.ai/CLAUDE.md` - API server docs

### Local GPU Processing

This project also does local GPU processing for:
- **MediaPipe**: Pose detection from drawings
- **rembg (U2-Net)**: Background removal
- **Coqui TTS**: Voice synthesis (optional)
- **Stable Diffusion**: AI background generation (optional, GPU required)

These run on the web server's local GPU (if available) or CPU fallback.

### Error Handling

The GPU API now supports OOM detection and automatic retry:
- If GPU runs out of memory, job retries on a different GPU
- GPU health tracking temporarily blacklists problematic GPUs
- Pre-flight memory checks prevent jobs from starting on low-memory GPUs

### Monitoring

```bash
# Check GPU status on API server
cd /home/john/PycharmProjects/api.imageeditor.ai/ansible
ansible -i servers server -m shell -a "nvidia-smi" --become

# GPU status dashboard
# Visit: https://api.imageeditor.ai/gpu/

# Check local worker logs
ansible -i servers all -m shell -a "tail -50 /var/log/animateadrawing/animateadrawing.err.log" --become
```

## Testing

```bash
# Run API endpoint test suite (40 tests)
python scripts/test_api_endpoints.py --live --verbose

# Test against localhost (default)
python scripts/test_api_endpoints.py

# Django management command wrapper
python manage.py test_api [--live] [--verbose]
```

Tests cover: public pages, auth, protected pages, API proxy, GPU backend, accounts API, animator API, static files, SSL redirects.

## Analytics

- **Clicky** analytics with anti-adblock proxy
- Script tag in `templates/base.html`
- Nginx proxy endpoints: `/32fd4eea88e4.js` and `/b1be3608b208`
