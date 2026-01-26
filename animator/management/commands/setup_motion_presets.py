"""
Management command to set up default motion presets.
Run with: python manage.py setup_motion_presets
"""
from django.core.management.base import BaseCommand
from animator.models import MotionPreset


DEFAULT_PRESETS = [
    # Transform-based presets (fast, preserves original art)
    {
        'name': 'Walk',
        'description': 'Natural walking motion with side-to-side sway and bounce. Preserves original artwork perfectly.',
        'category': 'locomotion',
        'animation_method': 'transform',
        'duration_seconds': 2.0,
        'transform_settings': {
            'rotation_amplitude': 3,
            'translation_x': 5,
            'translation_y': -8,
            'translation_y_mode': 'bounce',
            'scale_amplitude': 0,
            'frequency': 2,
        },
        'is_system': True,
    },
    {
        'name': 'Wave',
        'description': 'Friendly waving gesture with rotation oscillation. Great for greetings.',
        'category': 'gesture',
        'animation_method': 'transform',
        'duration_seconds': 2.0,
        'transform_settings': {
            'rotation_amplitude': 4,
            'translation_x': 0,
            'translation_y': 3,
            'scale_amplitude': 0,
            'frequency': 4,
        },
        'is_system': True,
    },
    {
        'name': 'Dance',
        'description': 'Energetic dance motion with larger movements and scale pulse.',
        'category': 'dance',
        'animation_method': 'transform',
        'duration_seconds': 2.0,
        'transform_settings': {
            'rotation_amplitude': 8,
            'translation_x': 10,
            'translation_y': -15,
            'translation_y_mode': 'bounce',
            'scale_amplitude': 0.02,
            'frequency': 4,
        },
        'is_system': True,
    },
    {
        'name': 'Breathe',
        'description': 'Subtle breathing animation. Great for idle characters and animals.',
        'category': 'idle',
        'animation_method': 'transform',
        'duration_seconds': 3.0,
        'transform_settings': {
            'rotation_amplitude': 1,
            'translation_x': 0,
            'translation_y': 2,
            'scale_amplitude': 0.015,
            'frequency': 2,
        },
        'is_system': True,
    },
    {
        'name': 'Robot',
        'description': 'Jerky, mechanical movement. Quantized steps for robotic feel.',
        'category': 'locomotion',
        'animation_method': 'transform',
        'duration_seconds': 2.0,
        'transform_settings': {
            'rotation_amplitude': 5,
            'translation_x': 8,
            'translation_y': 0,
            'scale_amplitude': 0,
            'frequency': 2,
            'quantize_steps': 8,
        },
        'is_system': True,
    },
    {
        'name': 'Jump',
        'description': 'Jumping motion with vertical translation.',
        'category': 'action',
        'animation_method': 'transform',
        'duration_seconds': 1.5,
        'transform_settings': {
            'rotation_amplitude': 2,
            'translation_x': 0,
            'translation_y': -20,
            'translation_y_mode': 'bounce',
            'scale_amplitude': 0.03,
            'frequency': 2,
        },
        'is_system': True,
    },
    {
        'name': 'Nod',
        'description': 'Nodding motion for agreement or acknowledgment.',
        'category': 'gesture',
        'animation_method': 'transform',
        'duration_seconds': 1.0,
        'transform_settings': {
            'rotation_amplitude': 0,
            'translation_x': 0,
            'translation_y': 5,
            'scale_amplitude': 0,
            'frequency': 4,
        },
        'is_system': True,
    },
    {
        'name': 'Shake',
        'description': 'Head shake motion for disagreement.',
        'category': 'gesture',
        'animation_method': 'transform',
        'duration_seconds': 1.0,
        'transform_settings': {
            'rotation_amplitude': 0,
            'translation_x': 8,
            'translation_y': 0,
            'scale_amplitude': 0,
            'frequency': 6,
        },
        'is_system': True,
    },
    # AI-based presets (slower, more realistic motion)
    {
        'name': 'AI Natural Motion',
        'description': 'Uses AI video generation for natural, realistic motion. Takes longer to render but produces high-quality results.',
        'category': 'custom',
        'animation_method': 'ai_video',
        'duration_seconds': 2.0,
        'ai_motion_bucket': 100,
        'ai_noise_strength': 0.02,
        'is_system': True,
    },
    {
        'name': 'AI Gentle Sway',
        'description': 'AI-generated subtle swaying motion. Good for still life and objects.',
        'category': 'idle',
        'animation_method': 'ai_video',
        'duration_seconds': 2.0,
        'ai_motion_bucket': 60,
        'ai_noise_strength': 0.01,
        'is_system': True,
    },
    {
        'name': 'AI Dynamic Action',
        'description': 'AI-generated dynamic motion with more movement. Good for characters in action.',
        'category': 'action',
        'animation_method': 'ai_video',
        'duration_seconds': 2.0,
        'ai_motion_bucket': 150,
        'ai_noise_strength': 0.03,
        'is_system': True,
    },
]


class Command(BaseCommand):
    help = 'Set up default motion presets for the animation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Update existing presets with same name',
        )

    def handle(self, *args, **options):
        force = options['force']
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for preset_data in DEFAULT_PRESETS:
            name = preset_data['name']
            existing = MotionPreset.objects.filter(name=name, is_system=True).first()

            if existing:
                if force:
                    for key, value in preset_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(self.style.WARNING(f'Updated: {name}'))
                else:
                    skipped_count += 1
                    self.stdout.write(f'Skipped (exists): {name}')
            else:
                MotionPreset.objects.create(**preset_data)
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {name}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Summary: {created_count} created, {updated_count} updated, {skipped_count} skipped'))
        self.stdout.write('')
        self.stdout.write('Motion preset types:')
        self.stdout.write('  - Transform: Fast rendering, preserves original artwork perfectly')
        self.stdout.write('  - AI Video: Slower, uses Stable Video Diffusion for realistic motion')
        self.stdout.write('  - Skeletal: Requires character rigging (advanced)')
