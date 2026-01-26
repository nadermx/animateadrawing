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
