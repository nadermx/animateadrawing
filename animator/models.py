from django.db import models
from django.conf import settings
import uuid
import os


def upload_drawing_path(instance, filename):
    """Generate path for uploaded drawings"""
    ext = filename.split('.')[-1]
    return f'drawings/{instance.project.user.id}/{instance.project.id}/{uuid.uuid4()}.{ext}'


def upload_background_path(instance, filename):
    """Generate path for uploaded backgrounds"""
    ext = filename.split('.')[-1]
    return f'backgrounds/{instance.user.id}/{uuid.uuid4()}.{ext}'


def upload_audio_path(instance, filename):
    """Generate path for uploaded audio"""
    ext = filename.split('.')[-1]
    return f'audio/{instance.project.user.id}/{instance.project.id}/{uuid.uuid4()}.{ext}'


def export_path(instance, filename):
    """Generate path for exported animations"""
    ext = filename.split('.')[-1]
    return f'exports/{instance.project.user.id}/{instance.project.id}/{uuid.uuid4()}.{ext}'


class Project(models.Model):
    """Main project container for animation work"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('rendering', 'Rendering'),
        ('completed', 'Completed'),
    ]

    PROJECT_TYPE_CHOICES = [
        ('quick', 'Quick Animation (GIF/Short Clip)'),
        ('short', 'Short Form (15-60 seconds)'),
        ('medium', 'Medium Length (1-5 minutes)'),
        ('full', 'Full Length Animation'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='animation_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES, default='quick')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    # Project settings
    width = models.IntegerField(default=1920)
    height = models.IntegerField(default=1080)
    fps = models.IntegerField(default=30)
    duration_seconds = models.FloatField(default=10.0)

    # Thumbnail
    thumbnail = models.ImageField(upload_to='project_thumbnails/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Character(models.Model):
    """A character created from a drawing"""
    CHARACTER_TYPE_CHOICES = [
        ('humanoid', 'Humanoid'),
        ('quadruped', 'Four-Legged Animal'),
        ('bird', 'Bird'),
        ('custom', 'Custom Rig'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='characters')
    name = models.CharField(max_length=100)
    character_type = models.CharField(max_length=20, choices=CHARACTER_TYPE_CHOICES, default='humanoid')

    # Original uploaded drawing
    original_image = models.ImageField(upload_to=upload_drawing_path)

    # Processed/masked character image (transparent background)
    processed_image = models.ImageField(upload_to=upload_drawing_path, null=True, blank=True)

    # Character rig data (JSON with joint positions, skeleton, etc.)
    rig_data = models.JSONField(default=dict, blank=True)

    # Bounding box in original image
    bbox_x = models.IntegerField(default=0)
    bbox_y = models.IntegerField(default=0)
    bbox_width = models.IntegerField(default=0)
    bbox_height = models.IntegerField(default=0)

    # Auto-detected or manually adjusted
    is_rig_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class Background(models.Model):
    """Reusable backgrounds for scenes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backgrounds', null=True, blank=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to=upload_background_path)

    # For AI-generated backgrounds
    prompt = models.TextField(blank=True)
    is_ai_generated = models.BooleanField(default=False)

    # System backgrounds are shown to all users
    is_system = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class MotionPreset(models.Model):
    """Preset animations that can be applied to characters"""
    CATEGORY_CHOICES = [
        ('locomotion', 'Locomotion'),
        ('gesture', 'Gesture'),
        ('dance', 'Dance'),
        ('action', 'Action'),
        ('emotion', 'Emotion'),
        ('idle', 'Idle'),
        ('custom', 'Custom'),
    ]

    ANIMATION_METHOD_CHOICES = [
        ('transform', 'Transform-Based (Fast, preserves original art perfectly)'),
        ('ai_video', 'AI Video Generation (Slower, adds realistic motion)'),
        ('skeletal', 'Skeletal Animation (Requires rigged character)'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    animation_method = models.CharField(
        max_length=20,
        choices=ANIMATION_METHOD_CHOICES,
        default='transform',
        help_text='Transform: applies rotation/translation/scale. AI Video: uses Stable Video Diffusion. Skeletal: uses character rig.'
    )

    # Motion data (BVH or custom format for skeletal animation)
    motion_data = models.JSONField(default=dict)

    # Transform animation settings (used when animation_method='transform')
    # These define how the image moves during animation
    transform_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text='Settings for transform animation: rotation_amplitude, translation_x, translation_y, scale_amplitude, etc.'
    )

    # AI video settings (used when animation_method='ai_video')
    ai_motion_bucket = models.IntegerField(
        default=100,
        help_text='Motion bucket ID for Stable Video Diffusion (1-255, higher=more motion)'
    )
    ai_noise_strength = models.FloatField(
        default=0.02,
        help_text='Noise augmentation strength for SVD (0-1, lower=preserves original better)'
    )

    # Duration of the motion
    duration_seconds = models.FloatField(default=2.0)

    # Is this a system preset or user-created?
    is_system = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='motion_presets')

    # Preview GIF
    preview_gif = models.FileField(upload_to='motion_previews/', null=True, blank=True)

    # Thumbnail
    thumbnail = models.ImageField(upload_to='motion_thumbnails/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Scene(models.Model):
    """A scene in the animation project"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scenes')
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    # Scene timing
    start_time = models.FloatField(default=0.0)
    duration = models.FloatField(default=5.0)

    # Background for this scene
    background = models.ForeignKey(Background, on_delete=models.SET_NULL, null=True, blank=True)
    background_color = models.CharField(max_length=7, default='#FFFFFF')  # Hex color

    # Camera settings
    camera_zoom = models.FloatField(default=1.0)
    camera_x = models.FloatField(default=0.0)
    camera_y = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name} - {self.project.name}"


class SceneCharacter(models.Model):
    """A character placed in a scene with its animation"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='scene_characters')
    character = models.ForeignKey(Character, on_delete=models.CASCADE)

    # Position in scene
    position_x = models.FloatField(default=0.0)
    position_y = models.FloatField(default=0.0)
    scale = models.FloatField(default=1.0)
    rotation = models.FloatField(default=0.0)
    z_index = models.IntegerField(default=0)

    # Flip horizontally
    flip_horizontal = models.BooleanField(default=False)

    # Timing within scene
    enter_time = models.FloatField(default=0.0)
    exit_time = models.FloatField(null=True, blank=True)  # null = stays until scene ends

    class Meta:
        ordering = ['z_index']


class Animation(models.Model):
    """An animation applied to a character in a scene"""
    EASING_CHOICES = [
        ('linear', 'Linear'),
        ('ease-in', 'Ease In'),
        ('ease-out', 'Ease Out'),
        ('ease-in-out', 'Ease In Out'),
        ('bounce', 'Bounce'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scene_character = models.ForeignKey(SceneCharacter, on_delete=models.CASCADE, related_name='animations')

    # Either a preset or custom animation
    motion_preset = models.ForeignKey(MotionPreset, on_delete=models.SET_NULL, null=True, blank=True)

    # Custom keyframe data (if not using preset)
    keyframes = models.JSONField(default=list, blank=True)

    # Timing
    start_time = models.FloatField(default=0.0)
    duration = models.FloatField(default=2.0)
    speed_multiplier = models.FloatField(default=1.0)

    # Loop settings
    loop = models.BooleanField(default=False)
    loop_count = models.IntegerField(default=1)  # 0 = infinite

    # Easing
    easing = models.CharField(max_length=20, choices=EASING_CHOICES, default='linear')

    # AI motion generation prompt (if generated)
    motion_prompt = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_time']


class AudioTrack(models.Model):
    """Audio tracks for the project"""
    AUDIO_TYPE_CHOICES = [
        ('music', 'Background Music'),
        ('sfx', 'Sound Effect'),
        ('voice', 'Voice/Dialogue'),
        ('generated', 'AI Generated'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='audio_tracks')
    name = models.CharField(max_length=100)
    audio_type = models.CharField(max_length=20, choices=AUDIO_TYPE_CHOICES)

    # Audio file
    audio_file = models.FileField(upload_to=upload_audio_path)

    # Timing
    start_time = models.FloatField(default=0.0)
    duration = models.FloatField(null=True, blank=True)  # null = full length

    # Volume
    volume = models.FloatField(default=1.0)

    # For voice synthesis
    voice_text = models.TextField(blank=True)
    voice_character = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


class TextOverlay(models.Model):
    """Text/subtitle overlays"""
    ANIMATION_CHOICES = [
        ('none', 'None'),
        ('fade', 'Fade In/Out'),
        ('typewriter', 'Typewriter'),
        ('slide-up', 'Slide Up'),
        ('slide-down', 'Slide Down'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='text_overlays')

    text = models.TextField()

    # Position and style
    position_x = models.FloatField(default=50.0)  # percentage
    position_y = models.FloatField(default=90.0)  # percentage
    font_size = models.IntegerField(default=24)
    font_family = models.CharField(max_length=100, default='Arial')
    color = models.CharField(max_length=7, default='#FFFFFF')
    background_color = models.CharField(max_length=9, default='#00000080')  # with alpha

    # Animation
    animation = models.CharField(max_length=20, choices=ANIMATION_CHOICES, default='fade')

    # Timing
    start_time = models.FloatField(default=0.0)
    duration = models.FloatField(default=3.0)

    created_at = models.DateTimeField(auto_now_add=True)


class Export(models.Model):
    """Exported/rendered animations"""
    FORMAT_CHOICES = [
        ('mp4', 'MP4 Video'),
        ('webm', 'WebM Video'),
        ('gif', 'Animated GIF'),
        ('png_sequence', 'PNG Sequence'),
        ('mov', 'MOV (ProRes)'),
    ]

    QUALITY_CHOICES = [
        ('low', 'Low (480p)'),
        ('medium', 'Medium (720p)'),
        ('high', 'High (1080p)'),
        ('ultra', 'Ultra (4K)'),
    ]

    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='exports')

    format = models.CharField(max_length=20, choices=FORMAT_CHOICES)
    quality = models.CharField(max_length=20, choices=QUALITY_CHOICES, default='high')

    # Export settings
    include_audio = models.BooleanField(default=True)
    transparent_background = models.BooleanField(default=False)

    # Export file
    output_file = models.FileField(upload_to=export_path, null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True)

    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Credits used for this export
    credits_used = models.IntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project.name} - {self.format} ({self.status})"


class CharacterTemplate(models.Model):
    """Pre-made character templates users can start from"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50)

    # Template image
    image = models.ImageField(upload_to='character_templates/')

    # Pre-configured rig
    rig_data = models.JSONField(default=dict)
    character_type = models.CharField(max_length=20, default='humanoid')

    # Is premium?
    is_premium = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class Storyboard(models.Model):
    """Storyboard for planning longer animations"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='storyboards')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StoryboardPanel(models.Model):
    """Individual panels in a storyboard"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storyboard = models.ForeignKey(Storyboard, on_delete=models.CASCADE, related_name='panels')

    order = models.IntegerField(default=0)

    # Panel content
    image = models.ImageField(upload_to='storyboard_panels/', null=True, blank=True)
    sketch_data = models.JSONField(default=dict, blank=True)  # For in-browser sketching

    # Notes
    description = models.TextField(blank=True)
    dialogue = models.TextField(blank=True)
    action_notes = models.TextField(blank=True)

    # Timing
    estimated_duration = models.FloatField(default=3.0)

    # Link to scene (after scene is created from panel)
    scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['order']


class LipSyncData(models.Model):
    """Lip sync data for character dialogue"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scene_character = models.ForeignKey(SceneCharacter, on_delete=models.CASCADE, related_name='lip_sync_data')
    audio_track = models.ForeignKey(AudioTrack, on_delete=models.CASCADE)

    # Phoneme timing data
    phoneme_data = models.JSONField(default=list)

    # Mouth shape mappings
    mouth_shapes = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)


class CollaborationInvite(models.Model):
    """Collaboration invites for projects"""
    PERMISSION_CHOICES = [
        ('view', 'View Only'),
        ('edit', 'Can Edit'),
        ('admin', 'Admin'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaboration_invites')
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invites')
    invited_email = models.EmailField()
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='received_invites')

    permission = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='edit')

    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)


class ProjectCollaborator(models.Model):
    """Active collaborators on a project"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaborating_projects')
    permission = models.CharField(max_length=20, default='edit')

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']
