"""
Background tasks for animation processing using django-rq
"""
import django_rq
from django.conf import settings
from django.utils import timezone
import uuid
import os
import json


@django_rq.job('default')
def detect_character_rig(character_id):
    """
    Detect character pose and create rig from uploaded image.
    Uses open source pose detection models.
    """
    from .models import Character
    from .services.pose_detection import PoseDetector

    character = Character.objects.get(id=character_id)

    try:
        detector = PoseDetector()
        rig_data = detector.detect(character.original_image.path)

        character.rig_data = rig_data
        character.save()

        return {'status': 'success', 'rig': rig_data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def process_character_image(character_id):
    """
    Process uploaded character image:
    - Remove background
    - Segment character
    - Create transparency mask
    """
    from .models import Character
    from .services.image_processing import ImageProcessor

    character = Character.objects.get(id=character_id)

    try:
        processor = ImageProcessor()
        processed_path = processor.remove_background(character.original_image.path)

        # Save processed image
        from django.core.files import File
        with open(processed_path, 'rb') as f:
            character.processed_image.save(
                f'processed_{character.id}.png',
                File(f),
                save=True
            )

        return {'status': 'success'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def generate_motion_from_prompt(character_id, prompt):
    """
    Generate motion/animation from text prompt using motion diffusion models.
    """
    from .models import Character, MotionPreset
    from .services.motion_generation import MotionGenerator

    character = Character.objects.get(id=character_id)

    try:
        generator = MotionGenerator()
        motion_data = generator.generate_from_prompt(
            prompt=prompt,
            character_type=character.character_type,
            rig_data=character.rig_data
        )

        # Create a custom motion preset
        preset = MotionPreset.objects.create(
            name=f"Generated: {prompt[:50]}",
            description=f"AI-generated motion from prompt: {prompt}",
            category='custom',
            motion_data=motion_data,
            duration_seconds=motion_data.get('duration', 2.0),
            is_system=False,
            user=character.project.user,
        )

        return {'status': 'success', 'preset_id': str(preset.id), 'motion_data': motion_data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('high')
def render_export(export_id):
    """
    Render full animation export.
    """
    from .models import Export
    from .services.renderer import AnimationRenderer

    export = Export.objects.get(id=export_id)
    export.status = 'processing'
    export.started_at = timezone.now()
    export.save()

    try:
        renderer = AnimationRenderer(export.project)

        # Calculate credits needed
        duration = export.project.duration_seconds
        quality_multiplier = {'low': 1, 'medium': 2, 'high': 3, 'ultra': 5}
        credits_needed = int(duration * quality_multiplier.get(export.quality, 1))

        # Check user credits
        user = export.project.user
        if user.credits < credits_needed and not user.is_plan_active:
            export.status = 'failed'
            export.error_message = 'Insufficient credits'
            export.save()
            return {'status': 'error', 'message': 'Insufficient credits'}

        # Render
        def progress_callback(progress):
            export.progress = progress
            export.save()

        output_path = renderer.render(
            format=export.format,
            quality=export.quality,
            include_audio=export.include_audio,
            transparent=export.transparent_background,
            progress_callback=progress_callback
        )

        # Save output file
        from django.core.files import File
        with open(output_path, 'rb') as f:
            export.output_file.save(
                f'{export.project.name}_{export.id}.{export.format}',
                File(f),
                save=False
            )

        export.file_size = os.path.getsize(output_path)
        export.status = 'completed'
        export.completed_at = timezone.now()
        export.credits_used = credits_needed
        export.progress = 100
        export.save()

        # Deduct credits
        if not user.is_plan_active:
            user.credits -= credits_needed
            user.save()

        # Cleanup temp file
        os.remove(output_path)

        return {'status': 'success', 'export_id': str(export.id)}

    except Exception as e:
        export.status = 'failed'
        export.error_message = str(e)
        export.save()
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def render_preview_frame(scene_id, frame_number):
    """
    Render a single frame for preview.
    """
    from .models import Scene
    from .services.renderer import AnimationRenderer

    scene = Scene.objects.get(id=scene_id)

    try:
        renderer = AnimationRenderer(scene.project)
        frame_path = renderer.render_frame(scene, frame_number)

        return {'status': 'success', 'frame_path': frame_path}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def generate_background(user_id, prompt):
    """
    Generate background image using AI (Stable Diffusion).
    """
    from .models import Background
    from .services.image_generation import ImageGenerator
    from accounts.models import CustomUser

    user = CustomUser.objects.get(id=user_id)

    try:
        generator = ImageGenerator()
        image_path = generator.generate_background(prompt)

        # Create background record
        from django.core.files import File
        background = Background(
            user=user,
            name=f"AI: {prompt[:50]}",
            prompt=prompt,
            is_ai_generated=True,
        )

        with open(image_path, 'rb') as f:
            background.image.save(
                f'ai_bg_{uuid.uuid4()}.png',
                File(f),
                save=True
            )

        # Cleanup
        os.remove(image_path)

        return {'status': 'success', 'background_id': str(background.id)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def synthesize_voice(project_id, text, voice):
    """
    Synthesize voice from text using TTS models.
    """
    from .models import Project, AudioTrack
    from .services.voice_synthesis import VoiceSynthesizer

    project = Project.objects.get(id=project_id)

    try:
        synthesizer = VoiceSynthesizer()
        audio_path = synthesizer.synthesize(text, voice)

        # Create audio track
        from django.core.files import File
        audio_track = AudioTrack(
            project=project,
            name=f"Voice: {text[:30]}...",
            audio_type='voice',
            voice_text=text,
            voice_character=voice,
        )

        with open(audio_path, 'rb') as f:
            audio_track.audio_file.save(
                f'voice_{uuid.uuid4()}.wav',
                File(f),
                save=True
            )

        # Cleanup
        os.remove(audio_path)

        return {'status': 'success', 'audio_track_id': str(audio_track.id)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('default')
def generate_lipsync_data(audio_track_id, scene_character_id):
    """
    Generate lip sync data from audio.
    """
    from .models import AudioTrack, SceneCharacter, LipSyncData
    from .services.lipsync import LipSyncGenerator

    audio_track = AudioTrack.objects.get(id=audio_track_id)
    scene_character = SceneCharacter.objects.get(id=scene_character_id)

    try:
        generator = LipSyncGenerator()
        phoneme_data = generator.generate(audio_track.audio_file.path)

        # Create lip sync data
        lipsync = LipSyncData.objects.create(
            scene_character=scene_character,
            audio_track=audio_track,
            phoneme_data=phoneme_data,
            mouth_shapes=generator.get_mouth_shape_mapping(),
        )

        return {'status': 'success', 'lipsync_id': str(lipsync.id)}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@django_rq.job('low')
def cleanup_old_exports():
    """
    Cleanup old export files to save storage.
    """
    from .models import Export
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(days=7)

    old_exports = Export.objects.filter(
        created_at__lt=cutoff,
        status='completed'
    )

    for export in old_exports:
        if export.output_file:
            export.output_file.delete()
        export.delete()

    return {'status': 'success', 'deleted': old_exports.count()}
