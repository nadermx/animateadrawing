from django.contrib import admin
from .models import (
    Project, Character, Background, MotionPreset, Scene, SceneCharacter,
    Animation, AudioTrack, TextOverlay, Export, CharacterTemplate,
    Storyboard, StoryboardPanel, LipSyncData, CollaborationInvite, ProjectCollaborator
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'project_type', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'project_type', 'created_at']
    search_fields = ['name', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'character_type', 'is_rig_confirmed', 'created_at']
    list_filter = ['character_type', 'is_rig_confirmed']
    search_fields = ['name', 'project__name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Background)
class BackgroundAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_ai_generated', 'created_at']
    list_filter = ['is_ai_generated', 'created_at']
    search_fields = ['name', 'user__email']


@admin.register(MotionPreset)
class MotionPresetAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_system', 'duration_seconds', 'created_at']
    list_filter = ['category', 'is_system']
    search_fields = ['name', 'description']


@admin.register(Scene)
class SceneAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'order', 'duration', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'project__name']


@admin.register(SceneCharacter)
class SceneCharacterAdmin(admin.ModelAdmin):
    list_display = ['character', 'scene', 'position_x', 'position_y', 'z_index']
    list_filter = ['flip_horizontal']


@admin.register(Animation)
class AnimationAdmin(admin.ModelAdmin):
    list_display = ['scene_character', 'motion_preset', 'start_time', 'duration', 'loop']
    list_filter = ['loop', 'easing']


@admin.register(AudioTrack)
class AudioTrackAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'audio_type', 'start_time', 'volume']
    list_filter = ['audio_type']
    search_fields = ['name', 'project__name']


@admin.register(TextOverlay)
class TextOverlayAdmin(admin.ModelAdmin):
    list_display = ['text', 'scene', 'animation', 'start_time', 'duration']
    list_filter = ['animation']


@admin.register(Export)
class ExportAdmin(admin.ModelAdmin):
    list_display = ['project', 'format', 'quality', 'status', 'progress', 'created_at']
    list_filter = ['format', 'quality', 'status']
    search_fields = ['project__name']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at']


@admin.register(CharacterTemplate)
class CharacterTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'character_type', 'is_premium', 'created_at']
    list_filter = ['category', 'character_type', 'is_premium']
    search_fields = ['name', 'description']


@admin.register(Storyboard)
class StoryboardAdmin(admin.ModelAdmin):
    list_display = ['project', 'created_at', 'updated_at']


@admin.register(StoryboardPanel)
class StoryboardPanelAdmin(admin.ModelAdmin):
    list_display = ['storyboard', 'order', 'estimated_duration']
    list_filter = ['storyboard']


@admin.register(LipSyncData)
class LipSyncDataAdmin(admin.ModelAdmin):
    list_display = ['scene_character', 'audio_track', 'created_at']


@admin.register(CollaborationInvite)
class CollaborationInviteAdmin(admin.ModelAdmin):
    list_display = ['project', 'invited_email', 'permission', 'accepted', 'created_at']
    list_filter = ['permission', 'accepted']


@admin.register(ProjectCollaborator)
class ProjectCollaboratorAdmin(admin.ModelAdmin):
    list_display = ['project', 'user', 'permission', 'joined_at']
    list_filter = ['permission']
