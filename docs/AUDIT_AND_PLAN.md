# AnimateADrawing.com - Audit & Expansion Plan

## Project Overview

AnimateADrawing.com is a character animation platform that lets users bring hand-drawn characters to life. Users upload drawings, the system detects character pose via MediaPipe, provides a rig editor for joint placement, and applies motion presets or AI-generated animations. The platform supports lip sync, TTS voice synthesis, storyboarding, multi-scene timelines, collaboration, and export in MP4/WebM/GIF/MOV/PNG-sequence formats.

**Server**: 140.82.28.166 (shared with drawinganimator)
**Local Path**: /home/john/animateadrawing
**Server Path**: /home/www/animateadrawing
**API**: api.animateadrawing.com (CNAME to GPU server 38.248.6.142)

---

## Current State

### Architecture
- Django-based frontend with `animator` app as the primary content module
- 14 models: Project, Character, Background, MotionPreset, Scene, SceneCharacter, Animation, AudioTrack, TextOverlay, Export, CharacterTemplate, Storyboard, StoryboardPanel, LipSyncData, CollaborationInvite, ProjectCollaborator
- UUID primary keys across all models (good practice)
- Full project-based workflow: Project > Scenes > Characters > Animations > Export
- Quick Animation mode for simplified single-page workflow
- Collaboration system with invite-by-email and permission levels (view/edit/admin)
- Background generation via AI prompts
- Voice synthesis integration for dialogue
- Lip sync data generation from audio tracks (phoneme timing)

### Monetization
- Credits-based system via CustomUser.credits
- Premium CharacterTemplates (is_premium flag)
- Pro plan gates premium motion presets
- Export quality tiers (480p-4K)
- Stripe, Square, PayPal payment processors
- Subscription with auto-rebill via management command

### Missing Features (vs. Other Projects)
- NO view tracking (no view_count, download_count, last_viewed on any model)
- NO smart retention / smart_expire management command
- NO sitemap for SEO (no public gallery pages are indexed)
- NO bot detection (no BOT_SIGNATURES, no _is_bot method)
- NO expired status on any model
- Rate limiting uses only cache-based payment_ratelimited, not per-operation credits

---

## Bugs & Issues

### Critical
1. **No view tracking on exports or projects** -- Unlike 9 other projects with `increment_view()`, this project has zero analytics on what content is being viewed. No way to measure engagement or value of generated content.
2. **No content expiration** -- Exports accumulate indefinitely. No `delete_expired` or `smart_expire` command exists. Server disk will grow unbounded.
3. **Collaboration invite email sends without error handling** -- `collaborator_invite` view calls `Utils.send_email` inside the POST handler with no try/except. A mail server failure will 500 the entire request.
4. **Export task import at request time** -- `from .tasks import render_export` is imported inside the view function. If the tasks module has import errors, users see a 500 only when they try to export.

### Medium
5. **No CSRF protection on callback endpoint** -- While not a security risk per se (no session auth), the `animation_callback` pattern from drawinganimator (which shares the server) lacks secret validation. GPU credit callbacks should use `GPU_SHARED_SECRET`.
6. **Rate limiting unclear** -- `payment_ratelimited` on CustomUser limits payment attempts (3 per hour), but there is no clear rate limit on animation generation itself. The `consume_credits` method only deducts 1 credit regardless of operation cost (quick GIF vs. 4K MOV export should differ).
7. **Character rig detection has no feedback** -- `api_detect_character` queues a job and returns `{'status': 'processing'}` but there is no polling endpoint or WebSocket to check detection status. Users must reload the page.
8. **No file size validation on character uploads** -- `character_upload` accepts any image file via `request.FILES.get('image')` with no size limit check. Could accept arbitrarily large uploads.
9. **Bare except clauses in accounts/models.py** -- Multiple `except:` (bare) clauses catch all exceptions including SystemExit and KeyboardInterrupt. Should be `except Exception:` at minimum.

### Low
10. **Storyboard always get_or_create** -- `storyboard_editor` always creates a storyboard if none exists. No way to have a project without a storyboard, even if the user only wants quick animation.
11. **No pagination on motion presets** -- `motion_preset_list` returns all presets without pagination. Could become slow with many user-created presets.

---

## Test Suite

All tests should be placed in `/home/john/animateadrawing/animator/tests.py` and standard Django test locations.

### Model Tests
```
test_project_creation_with_defaults
test_project_uuid_is_unique
test_character_upload_path_generation
test_character_rig_data_json_default
test_motion_preset_categories
test_motion_preset_animation_methods
test_scene_ordering_by_order_field
test_scene_character_z_index_ordering
test_animation_easing_choices
test_export_format_choices
test_export_quality_choices
test_export_status_lifecycle
test_audio_track_types
test_text_overlay_animation_choices
test_lip_sync_data_phoneme_storage
test_collaboration_invite_permission_choices
test_project_collaborator_unique_together
test_storyboard_panel_ordering
test_character_template_premium_flag
test_background_ai_generation_flag
```

### View Tests
```
test_dashboard_requires_login
test_dashboard_shows_recent_projects
test_project_list_pagination
test_project_list_filter_by_type
test_project_list_filter_by_status
test_project_create_post_creates_initial_scene
test_project_detail_collaborator_access
test_project_detail_non_collaborator_404
test_project_edit_updates_settings
test_project_delete_owner_only
test_quick_animate_shows_presets
test_quick_result_requires_owner
test_character_upload_creates_character
test_character_rig_editor_requires_project_access
test_character_delete_redirects_to_list
test_scene_create_increments_order
test_scene_editor_shows_confirmed_characters_only
test_scene_delete_redirects_to_list
test_timeline_editor_shows_all_scenes
test_storyboard_editor_creates_if_missing
test_export_project_queues_render_task
test_export_status_shows_progress
test_export_download_requires_completed_status
test_motion_preset_list_public_access
test_motion_preset_list_filter_by_category
test_motion_preset_preview_returns_file
test_background_library_public_access
test_background_upload_requires_login
test_background_generate_requires_login_for_post
test_template_library_marks_premium
test_collaborator_list_shows_invites
test_collaborator_invite_sends_email
test_collaborator_invite_owner_only
```

### API Tests
```
test_api_project_data_returns_full_json
test_api_project_data_includes_characters_and_scenes
test_api_detect_character_queues_job
test_api_save_rig_sets_confirmed
test_api_save_rig_invalid_json_returns_400
test_api_scene_data_includes_text_overlays
test_api_save_scene_updates_character_positions
test_api_save_scene_invalid_json_returns_400
test_api_generate_animation_missing_params_returns_400
test_api_render_preview_queues_job
test_api_export_status_returns_download_url_when_complete
test_api_synthesize_voice_queues_job
test_api_generate_lipsync_queues_job
```

### Security Tests
```
test_project_access_denied_for_non_owner_non_collaborator
test_character_access_denied_cross_project
test_export_download_denied_for_other_user
test_api_endpoints_require_authentication
test_collaboration_invite_only_by_owner
```

---

## Monetization Fixes

### Tiered Credit Costs
Currently `consume_credits` always deducts 1 credit. Implement tiered pricing:

| Operation | Credit Cost |
|-----------|------------|
| Quick GIF (480p) | 1 |
| Quick MP4 (720p) | 2 |
| Scene render (1080p) | 5 |
| Full project export (1080p) | 10 |
| 4K export | 25 |
| AI motion generation | 3 |
| Voice synthesis | 2 |
| Lip sync generation | 2 |
| Background AI generation | 3 |
| Character rig auto-detect | 1 |

### Premium Feature Gating
- Character templates with `is_premium=True` should require Pro plan
- Motion presets already check `is_premium` -- good
- Transparent background export should be Pro-only
- MOV (ProRes) format should be Pro-only
- Collaboration (inviting others) should be Pro-only or limited to 1 collaborator for free

### Usage Analytics
- Add `view_count` and `download_count` to Export model
- Track which motion presets are most popular to inform content creation
- Track character template usage to prioritize new template creation

---

## Feature Expansion

### Phase 1: Social Media Animations (Priority: HIGH)
- **Platform-specific export presets**: Instagram Reels (1080x1920, 15/30/60s), TikTok (1080x1920), YouTube Shorts (1080x1920), Twitter/X GIF (max 15MB), Facebook Story
- **Auto-resize and reformat**: One animation, export to all platforms with proper dimensions
- **Trending motion library**: Curated motion presets matching viral animation trends
- **Direct sharing**: Post to social platforms via API (Instagram Graph API, TikTok, YouTube Data API)
- **Watermark customization**: Custom watermark placement/opacity for free tier, removable for Pro

### Phase 2: Education & Children's Content (Priority: HIGH)
- **Storybook mode**: Guided workflow for creating animated children's stories
- **Educational templates**: Science concepts, math visualizations, history scenes
- **Read-along sync**: Text highlights synced to narration audio
- **Character library for kids**: Age-appropriate pre-rigged characters (animals, people, fantasy)
- **Classroom dashboard**: Teacher accounts that manage student projects
- **Export to presentation**: PowerPoint/Google Slides compatible output

### Phase 3: Brand Mascots & Marketing (Priority: MEDIUM)
- **Brand kit integration**: Upload brand colors, fonts, logos that persist across projects
- **Mascot creation wizard**: Step-by-step guide for creating animated brand mascots
- **Ad format exports**: Standard ad sizes (300x250, 728x90, 160x600) as animated banners
- **Email GIF generator**: Optimized GIF output for email marketing (compressed, looping)
- **Landing page embed code**: Generated embed snippets for animated mascots on websites
- **A/B testing support**: Export multiple variations of same animation

### Phase 4: Game Sprites & VTuber Avatars (Priority: MEDIUM)
- **Sprite sheet export**: Export animation frames as sprite sheets (PNG grid) for game engines
- **Unity/Godot plugin**: Import animated characters directly into game engines
- **VTuber avatar mode**: Real-time face tracking to drive character rig via webcam
- **Live2D-compatible export**: Export rigged characters in Live2D format
- **Expression library**: Pre-built facial expression sets for VTuber avatars
- **OBS integration**: Browser source for real-time avatar in streaming software

### Phase 5: Custom Motion Training (Priority: MEDIUM)
- **Motion capture upload**: Accept BVH, FBX motion capture files as custom presets
- **Video-to-motion**: Record yourself doing a motion, AI extracts pose keyframes
- **Motion style transfer**: Apply the style of one motion to another
- **Physics simulation**: Simple cloth/hair physics on animated characters
- **Procedural animation**: Walk cycles, breathing, blinking auto-generated from parameters

### Phase 6: NFT & Digital Art (Priority: LOW)
- **NFT-ready export**: Optimized formats for OpenSea, Rarible
- **Collection generator**: Create variations of animated characters (color, accessories)
- **Provenance tracking**: Blockchain-verified creation timestamps
- **Animated PFP creator**: Profile picture animation for social media

### Phase 7: Music Video Sync (Priority: LOW)
- **Beat detection**: Auto-sync character movements to music beats
- **Lyric overlay**: Karaoke-style text sync with audio
- **Multi-track timeline**: Separate audio tracks for music, SFX, dialogue
- **Music visualizer backgrounds**: AI-generated backgrounds that react to audio

### Phase 8: Enterprise Brand Animation API (Priority: LOW)
- **REST API**: Programmatic animation creation for enterprise clients
- **Batch processing**: Upload hundreds of images, apply same animation to all
- **Custom branding**: White-label animation player
- **SLA guarantees**: Priority GPU queue for enterprise accounts
- **Usage analytics dashboard**: Track API usage, costs, popular animations
- **Webhook callbacks**: Notify external systems when animations complete

---

## Infrastructure Notes

### Shared Server (140.82.28.166)
This server is shared with drawinganimator. Both projects run under the same nginx. Ensure:
- Supervisor configs are properly namespaced
- Log files are separated (/var/log/animateadrawing/ vs /var/log/drawinganimator/)
- Database names are distinct

### Content Cleanup Needed
- No `smart_expire` or `delete_expired` command exists
- Need to implement cleanup for: exports, uploaded drawings, processed images, audio files
- Consider: keep completed exports for 30 days, delete failed exports after 24 hours
- Pro users' content should be exempt from cleanup

### SEO Opportunity
- Public motion preset gallery could be indexed
- Public background library could be indexed
- Neither has a sitemap currently
- Adding view tracking would enable smart retention later
