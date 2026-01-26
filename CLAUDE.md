# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Animate a Drawing** (animateadrawing.com) is a Django-based web application that allows users to animate their drawings using AI and open source models. Users can upload drawings, auto-detect character poses, apply motion presets or AI-generated animations, and export to video formats.

### Key Features
- Quick animation: Upload a drawing and get an animated GIF/video in seconds
- AI pose detection using MediaPipe for automatic character rigging
- Motion preset library (walk, run, dance, jump, wave, etc.)
- AI motion generation from text prompts
- Multi-scene project editor with timeline
- Background removal using rembg (U2-Net)
- Voice synthesis and lip-sync support
- Multiple export formats (MP4, WebM, GIF, PNG sequence)
- Storyboard planning for full-length animations
- Collaboration features

## Common Commands

```bash
# Setup
cp config_example.py config.py  # Configure before first run
pip install -r requirements.txt
python manage.py migrate
python manage.py set_languages  # Initialize available languages
python manage.py runserver

# Background workers (for animation processing)
python manage.py rqworker default high low

# Translations
python manage.py run_translation  # Translate untranslated TextBase entries
```

## Architecture

### Apps
- `animator/` - Main animation functionality (models, views, AI services)
- `accounts/` - Custom user model, authentication, credits system
- `core/` - Homepage and static pages
- `finances/` - Payment processing, plans, subscriptions
- `translations/` - Database-driven translation system
- `contact_messages/` - Contact form

### Animator App Structure
```
animator/
├── models.py          # Project, Character, Scene, Animation, Export models
├── views.py           # All animator views and API endpoints
├── urls.py            # URL routing
├── admin.py           # Django admin configuration
├── tasks.py           # Background tasks (django-rq)
└── services/          # AI processing services
    ├── pose_detection.py    # MediaPipe pose detection
    ├── image_processing.py  # Background removal (rembg)
    ├── motion_generation.py # Motion presets and AI generation
    ├── renderer.py          # Animation rendering to video
    ├── voice_synthesis.py   # TTS using Coqui TTS
    ├── lipsync.py           # Lip sync from audio
    └── image_generation.py  # AI background generation (Stable Diffusion)
```

### Key Models
- `Project` - Container for animation projects (quick, short, medium, full-length)
- `Character` - Character from uploaded drawing with rig data
- `Scene` - Individual scene with background and camera settings
- `SceneCharacter` - Character placement in a scene
- `Animation` - Animation applied to character (preset or custom keyframes)
- `MotionPreset` - Pre-made or user motion presets
- `Export` - Rendered animation output

### Configuration
Settings split between `app/settings.py` (Django defaults) and `config.py` (secrets/env-specific).

Key config values:
- `PROJECT_NAME` - "Animate a Drawing"
- `PROJECT_DOMAIN` - animateadrawing.com
- `EMAIL_*` - SMTP settings (uses native Postfix)

### API Endpoints
All animator API endpoints are prefixed with `/animator/api/`:
- `POST /api/characters/<id>/detect/` - Auto-detect character pose
- `POST /api/characters/<id>/rig/` - Save character rig
- `GET /api/scenes/<id>/data/` - Get scene data as JSON
- `POST /api/scenes/<id>/save/` - Save scene data
- `POST /api/animations/generate/` - Generate motion from text prompt
- `GET /api/export/<id>/status/` - Check export progress

### Background Tasks
Uses django-rq for processing:
- `detect_character_rig` - AI pose detection
- `process_character_image` - Background removal
- `generate_motion_from_prompt` - AI motion generation
- `render_export` - Video rendering
- `generate_background` - AI background generation
- `synthesize_voice` - Text-to-speech
- `generate_lipsync_data` - Lip sync from audio

## Dependencies

### Required
- Django 5.x
- PostgreSQL
- Redis (for caching and task queue)
- FFmpeg (for video encoding)

### AI/ML (install based on features needed)
- `opencv-python` - Image processing
- `mediapipe` - Pose detection
- `rembg` - Background removal
- `TTS` (Coqui) - Voice synthesis (optional)
- `diffusers` - Stable Diffusion for backgrounds (optional)

## Frontend
- Bootstrap 5 (CDN)
- Custom JavaScript for:
  - Canvas-based rig editor
  - Drag-and-drop upload
  - Animation preview
  - Timeline editor

## Deployment
Uses Ansible playbooks in `ansible/` directory:
- `djangodeployubuntu20.yml` - Full deployment
- `gitpull.yml` - Update from git

Configure `ansible/group_vars/all` with server credentials.

### User & Authentication
Custom user model `accounts.CustomUser` with:
- Email as username
- Credits system for usage-based billing
- Subscription tracking (`is_plan_active`, `next_billing_date`, `plan_subscribed`)
- Payment processor tokens stored per user

### Payment Processing
`finances/` supports Stripe, Square, PayPal. Plans defined in admin with `is_subscription` flag.

### View Pattern
Views use `GlobalVars.get_globals(request)` from `accounts/views.py` to get translation dict (`i18n`) and other settings. All templates receive this as `g` context variable.
