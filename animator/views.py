from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
import json
import os

from .models import (
    Project, Character, Background, MotionPreset, Scene, SceneCharacter,
    Animation, AudioTrack, TextOverlay, Export, CharacterTemplate,
    Storyboard, StoryboardPanel, LipSyncData, CollaborationInvite, ProjectCollaborator
)
from accounts.views import GlobalVars


def get_project_or_404(user, project_id):
    """Get project if user owns it or is a collaborator"""
    project = get_object_or_404(Project, id=project_id)
    if project.user == user:
        return project
    if ProjectCollaborator.objects.filter(project=project, user=user).exists():
        return project
    raise Http404("Project not found")


# Dashboard
@login_required
def dashboard(request):
    """Main animator dashboard"""
    g = GlobalVars.get_globals(request)

    # Get user's recent projects
    projects = Project.objects.filter(
        Q(user=request.user) | Q(collaborators__user=request.user)
    ).distinct().order_by('-updated_at')[:6]

    # Get recent exports
    exports = Export.objects.filter(
        project__user=request.user,
        status='completed'
    ).order_by('-completed_at')[:5]

    # Get motion presets for quick access
    presets = MotionPreset.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    ).order_by('category', 'name')[:12]

    context = {
        'g': g,
        'projects': projects,
        'exports': exports,
        'presets': presets,
    }
    return render(request, 'animator/dashboard.html', context)


# Projects
@login_required
def project_list(request):
    """List all user's projects"""
    g = GlobalVars.get_globals(request)

    projects = Project.objects.filter(
        Q(user=request.user) | Q(collaborators__user=request.user)
    ).distinct().order_by('-updated_at')

    # Filter by type
    project_type = request.GET.get('type')
    if project_type:
        projects = projects.filter(project_type=project_type)

    # Filter by status
    status = request.GET.get('status')
    if status:
        projects = projects.filter(status=status)

    paginator = Paginator(projects, 12)
    page = request.GET.get('page', 1)
    projects = paginator.get_page(page)

    context = {
        'g': g,
        'projects': projects,
        'project_types': Project.PROJECT_TYPE_CHOICES,
        'status_choices': Project.STATUS_CHOICES,
    }
    return render(request, 'animator/project_list.html', context)


@login_required
def project_create(request):
    """Create a new project"""
    g = GlobalVars.get_globals(request)

    if request.method == 'POST':
        project = Project.objects.create(
            user=request.user,
            name=request.POST.get('name', 'Untitled Project'),
            description=request.POST.get('description', ''),
            project_type=request.POST.get('project_type', 'quick'),
            width=int(request.POST.get('width', 1920)),
            height=int(request.POST.get('height', 1080)),
            fps=int(request.POST.get('fps', 30)),
        )

        # Create initial scene
        Scene.objects.create(
            project=project,
            name='Scene 1',
            order=0,
        )

        return redirect('animator:project_detail', project_id=project.id)

    context = {
        'g': g,
        'project_types': Project.PROJECT_TYPE_CHOICES,
    }
    return render(request, 'animator/project_create.html', context)


@login_required
def project_detail(request, project_id):
    """Project overview page"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    context = {
        'g': g,
        'project': project,
        'characters': project.characters.all(),
        'scenes': project.scenes.all(),
        'exports': project.exports.order_by('-created_at')[:5],
    }
    return render(request, 'animator/project_detail.html', context)


@login_required
def project_edit(request, project_id):
    """Edit project settings"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST':
        project.name = request.POST.get('name', project.name)
        project.description = request.POST.get('description', '')
        project.width = int(request.POST.get('width', project.width))
        project.height = int(request.POST.get('height', project.height))
        project.fps = int(request.POST.get('fps', project.fps))
        project.save()
        return redirect('animator:project_detail', project_id=project.id)

    context = {
        'g': g,
        'project': project,
    }
    return render(request, 'animator/project_edit.html', context)


@login_required
def project_delete(request, project_id):
    """Delete a project"""
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST':
        if project.user == request.user:  # Only owner can delete
            project.delete()
            return redirect('animator:project_list')

    return redirect('animator:project_detail', project_id=project.id)


# Quick Animation (simplified single-page workflow)
@login_required
def quick_animate(request):
    """Quick animation - upload and animate in one page"""
    g = GlobalVars.get_globals(request)

    presets = MotionPreset.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    ).order_by('category', 'name')

    context = {
        'g': g,
        'presets': presets,
        'preset_categories': MotionPreset.CATEGORY_CHOICES,
    }
    return render(request, 'animator/quick_animate.html', context)


@login_required
def quick_result(request, export_id):
    """View quick animation result"""
    g = GlobalVars.get_globals(request)
    export = get_object_or_404(Export, id=export_id, project__user=request.user)

    context = {
        'g': g,
        'export': export,
    }
    return render(request, 'animator/quick_result.html', context)


# Characters
@login_required
def character_list(request, project_id):
    """List characters in a project"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    context = {
        'g': g,
        'project': project,
        'characters': project.characters.all(),
    }
    return render(request, 'animator/character_list.html', context)


@login_required
def character_upload(request, project_id):
    """Upload a new character drawing"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            character = Character.objects.create(
                project=project,
                name=request.POST.get('name', 'Character'),
                character_type=request.POST.get('character_type', 'humanoid'),
                original_image=image,
            )
            return redirect('animator:character_rig_editor', character_id=character.id)

    context = {
        'g': g,
        'project': project,
        'character_types': Character.CHARACTER_TYPE_CHOICES,
        'templates': CharacterTemplate.objects.all(),
    }
    return render(request, 'animator/character_upload.html', context)


@login_required
def character_detail(request, character_id):
    """View character details"""
    g = GlobalVars.get_globals(request)
    character = get_object_or_404(Character, id=character_id)
    get_project_or_404(request.user, character.project.id)

    context = {
        'g': g,
        'character': character,
        'project': character.project,
    }
    return render(request, 'animator/character_detail.html', context)


@login_required
def character_rig_editor(request, character_id):
    """Interactive rig editor for character"""
    g = GlobalVars.get_globals(request)
    character = get_object_or_404(Character, id=character_id)
    get_project_or_404(request.user, character.project.id)

    context = {
        'g': g,
        'character': character,
        'project': character.project,
    }
    return render(request, 'animator/character_rig_editor.html', context)


@login_required
def character_delete(request, character_id):
    """Delete a character"""
    character = get_object_or_404(Character, id=character_id)
    project = get_project_or_404(request.user, character.project.id)

    if request.method == 'POST':
        character.delete()
        return redirect('animator:character_list', project_id=project.id)

    return redirect('animator:character_detail', character_id=character.id)


# Scenes
@login_required
def scene_list(request, project_id):
    """List scenes in a project"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    context = {
        'g': g,
        'project': project,
        'scenes': project.scenes.all(),
    }
    return render(request, 'animator/scene_list.html', context)


@login_required
def scene_create(request, project_id):
    """Create a new scene"""
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST':
        # Get the next order number
        max_order = project.scenes.order_by('-order').first()
        next_order = (max_order.order + 1) if max_order else 0

        scene = Scene.objects.create(
            project=project,
            name=request.POST.get('name', f'Scene {next_order + 1}'),
            order=next_order,
            duration=float(request.POST.get('duration', 5.0)),
        )
        return redirect('animator:scene_editor', scene_id=scene.id)

    return redirect('animator:scene_list', project_id=project.id)


@login_required
def scene_editor(request, scene_id):
    """Scene composition editor"""
    g = GlobalVars.get_globals(request)
    scene = get_object_or_404(Scene, id=scene_id)
    project = get_project_or_404(request.user, scene.project.id)

    presets = MotionPreset.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    ).order_by('category', 'name')

    backgrounds = Background.objects.filter(user=request.user)

    context = {
        'g': g,
        'scene': scene,
        'project': project,
        'characters': project.characters.filter(is_rig_confirmed=True),
        'scene_characters': scene.scene_characters.all(),
        'presets': presets,
        'backgrounds': backgrounds,
    }
    return render(request, 'animator/scene_editor.html', context)


@login_required
def scene_delete(request, scene_id):
    """Delete a scene"""
    scene = get_object_or_404(Scene, id=scene_id)
    project = get_project_or_404(request.user, scene.project.id)

    if request.method == 'POST':
        scene.delete()
        return redirect('animator:scene_list', project_id=project.id)

    return redirect('animator:scene_editor', scene_id=scene.id)


# Timeline Editor
@login_required
def timeline_editor(request, project_id):
    """Full timeline editor for complex projects"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    context = {
        'g': g,
        'project': project,
        'scenes': project.scenes.all(),
        'audio_tracks': project.audio_tracks.all(),
    }
    return render(request, 'animator/timeline_editor.html', context)


# Storyboard
@login_required
def storyboard_editor(request, project_id):
    """Storyboard planning view"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    storyboard, created = Storyboard.objects.get_or_create(project=project)

    context = {
        'g': g,
        'project': project,
        'storyboard': storyboard,
        'panels': storyboard.panels.all(),
    }
    return render(request, 'animator/storyboard_editor.html', context)


# Export
@login_required
def export_project(request, project_id):
    """Export project settings page"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST':
        export = Export.objects.create(
            project=project,
            format=request.POST.get('format', 'mp4'),
            quality=request.POST.get('quality', 'high'),
            include_audio=request.POST.get('include_audio') == 'on',
            transparent_background=request.POST.get('transparent_background') == 'on',
        )

        # Queue export job
        from .tasks import render_export
        render_export.delay(str(export.id))

        return redirect('animator:export_status', export_id=export.id)

    context = {
        'g': g,
        'project': project,
        'format_choices': Export.FORMAT_CHOICES,
        'quality_choices': Export.QUALITY_CHOICES,
    }
    return render(request, 'animator/export_project.html', context)


@login_required
def export_status(request, export_id):
    """View export status"""
    g = GlobalVars.get_globals(request)
    export = get_object_or_404(Export, id=export_id, project__user=request.user)

    context = {
        'g': g,
        'export': export,
    }
    return render(request, 'animator/export_status.html', context)


@login_required
def export_download(request, export_id):
    """Download exported file"""
    export = get_object_or_404(Export, id=export_id, project__user=request.user)

    if export.status != 'completed' or not export.output_file:
        raise Http404("Export not ready")

    return FileResponse(
        export.output_file.open('rb'),
        as_attachment=True,
        filename=f"{export.project.name}.{export.format}"
    )


# Motion Presets
@login_required
def motion_preset_list(request):
    """Browse motion presets"""
    g = GlobalVars.get_globals(request)

    presets = MotionPreset.objects.filter(
        Q(is_system=True) | Q(user=request.user)
    ).order_by('category', 'name')

    category = request.GET.get('category')
    if category:
        presets = presets.filter(category=category)

    context = {
        'g': g,
        'presets': presets,
        'categories': MotionPreset.CATEGORY_CHOICES,
    }
    return render(request, 'animator/motion_preset_list.html', context)


@login_required
def motion_preset_preview(request, preset_id):
    """Preview a motion preset"""
    preset = get_object_or_404(MotionPreset, id=preset_id)

    if preset.preview_gif:
        try:
            if preset.preview_gif.storage.exists(preset.preview_gif.name):
                return FileResponse(preset.preview_gif.open('rb'))
        except Exception:
            pass

    raise Http404("No preview available")


# Backgrounds
@login_required
def background_library(request):
    """Browse and manage backgrounds"""
    g = GlobalVars.get_globals(request)

    backgrounds = Background.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'g': g,
        'backgrounds': backgrounds,
    }
    return render(request, 'animator/background_library.html', context)


@login_required
def background_upload(request):
    """Upload a background image"""
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            Background.objects.create(
                user=request.user,
                name=request.POST.get('name', 'Background'),
                image=image,
            )
    return redirect('animator:background_library')


@login_required
def background_generate(request):
    """Generate background with AI"""
    g = GlobalVars.get_globals(request)

    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        if prompt:
            # Queue AI generation
            from .tasks import generate_background
            generate_background.delay(request.user.id, prompt)
            return JsonResponse({'status': 'queued'})

    context = {
        'g': g,
    }
    return render(request, 'animator/background_generate.html', context)


# Templates
@login_required
def template_library(request):
    """Browse character templates"""
    g = GlobalVars.get_globals(request)

    templates = CharacterTemplate.objects.all()

    # Filter for free users
    if not request.user.is_plan_active:
        templates = templates.filter(is_premium=False)

    context = {
        'g': g,
        'templates': templates,
    }
    return render(request, 'animator/template_library.html', context)


# Collaboration
@login_required
def collaborator_list(request, project_id):
    """View and manage project collaborators"""
    g = GlobalVars.get_globals(request)
    project = get_project_or_404(request.user, project_id)

    context = {
        'g': g,
        'project': project,
        'collaborators': project.collaborators.all(),
        'invites': project.collaboration_invites.filter(accepted=False),
    }
    return render(request, 'animator/collaborator_list.html', context)


@login_required
def collaborator_invite(request, project_id):
    """Invite a collaborator"""
    project = get_project_or_404(request.user, project_id)

    if request.method == 'POST' and project.user == request.user:
        email = request.POST.get('email')
        permission = request.POST.get('permission', 'edit')

        if email:
            invite = CollaborationInvite.objects.create(
                project=project,
                invited_by=request.user,
                invited_email=email,
                permission=permission,
            )
            # Send email invitation
            from app.utils import Utils
            from accounts.views import GlobalVars
            g = GlobalVars.get_globals(request)
            Utils.send_email(
                recipients=[email],
                subject=f"You've been invited to collaborate on \"{project.name}\"",
                template='collaboration-invite',
                data={
                    'project': project,
                    'invite': invite,
                    'invited_by': request.user,
                    'i18n': g.get('i18n'),
                }
            )

    return redirect('animator:collaborator_list', project_id=project.id)


# API Endpoints
@login_required
@require_http_methods(["GET"])
def api_project_data(request, project_id):
    """Get full project data as JSON"""
    project = get_project_or_404(request.user, project_id)

    data = {
        'id': str(project.id),
        'name': project.name,
        'width': project.width,
        'height': project.height,
        'fps': project.fps,
        'duration': project.duration_seconds,
        'scenes': [],
        'characters': [],
    }

    for character in project.characters.all():
        data['characters'].append({
            'id': str(character.id),
            'name': character.name,
            'type': character.character_type,
            'image': character.processed_image.url if character.processed_image else character.original_image.url,
            'rig': character.rig_data,
        })

    for scene in project.scenes.all():
        scene_data = {
            'id': str(scene.id),
            'name': scene.name,
            'order': scene.order,
            'duration': scene.duration,
            'background_color': scene.background_color,
            'background_image': scene.background.image.url if scene.background else None,
            'camera': {
                'zoom': scene.camera_zoom,
                'x': scene.camera_x,
                'y': scene.camera_y,
            },
            'characters': [],
        }

        for sc in scene.scene_characters.all():
            sc_data = {
                'id': str(sc.id),
                'character_id': str(sc.character.id),
                'position': {'x': sc.position_x, 'y': sc.position_y},
                'scale': sc.scale,
                'rotation': sc.rotation,
                'z_index': sc.z_index,
                'flip': sc.flip_horizontal,
                'animations': [],
            }

            for anim in sc.animations.all():
                sc_data['animations'].append({
                    'id': str(anim.id),
                    'preset_id': str(anim.motion_preset.id) if anim.motion_preset else None,
                    'keyframes': anim.keyframes,
                    'start_time': anim.start_time,
                    'duration': anim.duration,
                    'speed': anim.speed_multiplier,
                    'loop': anim.loop,
                    'easing': anim.easing,
                })

            scene_data['characters'].append(sc_data)

        data['scenes'].append(scene_data)

    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def api_detect_character(request, character_id):
    """Auto-detect character pose/rig from image"""
    character = get_object_or_404(Character, id=character_id)
    get_project_or_404(request.user, character.project.id)

    # Queue detection job
    from .tasks import detect_character_rig
    detect_character_rig.delay(str(character.id))

    return JsonResponse({'status': 'processing'})


@login_required
@require_http_methods(["POST"])
def api_save_rig(request, character_id):
    """Save character rig data"""
    character = get_object_or_404(Character, id=character_id)
    get_project_or_404(request.user, character.project.id)

    try:
        data = json.loads(request.body)
        character.rig_data = data.get('rig', {})
        character.is_rig_confirmed = True
        character.save()
        return JsonResponse({'status': 'saved'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@require_http_methods(["GET"])
def api_scene_data(request, scene_id):
    """Get scene data as JSON"""
    scene = get_object_or_404(Scene, id=scene_id)
    get_project_or_404(request.user, scene.project.id)

    data = {
        'id': str(scene.id),
        'name': scene.name,
        'duration': scene.duration,
        'background_color': scene.background_color,
        'characters': [],
        'text_overlays': [],
    }

    for sc in scene.scene_characters.all():
        data['characters'].append({
            'id': str(sc.id),
            'character_id': str(sc.character.id),
            'name': sc.character.name,
            'image': sc.character.processed_image.url if sc.character.processed_image else sc.character.original_image.url,
            'position': {'x': sc.position_x, 'y': sc.position_y},
            'scale': sc.scale,
            'rotation': sc.rotation,
            'z_index': sc.z_index,
            'flip': sc.flip_horizontal,
        })

    for overlay in scene.text_overlays.all():
        data['text_overlays'].append({
            'id': str(overlay.id),
            'text': overlay.text,
            'position': {'x': overlay.position_x, 'y': overlay.position_y},
            'font_size': overlay.font_size,
            'color': overlay.color,
            'animation': overlay.animation,
            'start_time': overlay.start_time,
            'duration': overlay.duration,
        })

    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def api_save_scene(request, scene_id):
    """Save scene data"""
    scene = get_object_or_404(Scene, id=scene_id)
    get_project_or_404(request.user, scene.project.id)

    try:
        data = json.loads(request.body)

        scene.duration = data.get('duration', scene.duration)
        scene.background_color = data.get('background_color', scene.background_color)
        scene.camera_zoom = data.get('camera', {}).get('zoom', scene.camera_zoom)
        scene.camera_x = data.get('camera', {}).get('x', scene.camera_x)
        scene.camera_y = data.get('camera', {}).get('y', scene.camera_y)
        scene.save()

        # Update scene characters
        for char_data in data.get('characters', []):
            if 'id' in char_data:
                sc = SceneCharacter.objects.filter(id=char_data['id']).first()
                if sc:
                    sc.position_x = char_data.get('position', {}).get('x', sc.position_x)
                    sc.position_y = char_data.get('position', {}).get('y', sc.position_y)
                    sc.scale = char_data.get('scale', sc.scale)
                    sc.rotation = char_data.get('rotation', sc.rotation)
                    sc.z_index = char_data.get('z_index', sc.z_index)
                    sc.flip_horizontal = char_data.get('flip', sc.flip_horizontal)
                    sc.save()

        return JsonResponse({'status': 'saved'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@require_http_methods(["POST"])
def api_generate_animation(request):
    """Generate animation from text prompt"""
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt')
        character_id = data.get('character_id')

        if not prompt or not character_id:
            return JsonResponse({'error': 'Missing prompt or character_id'}, status=400)

        character = get_object_or_404(Character, id=character_id)
        get_project_or_404(request.user, character.project.id)

        # Queue animation generation
        from .tasks import generate_motion_from_prompt
        task_id = generate_motion_from_prompt.delay(str(character.id), prompt)

        return JsonResponse({'status': 'processing', 'task_id': str(task_id)})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@require_http_methods(["POST"])
def api_render_preview(request):
    """Render a preview frame/clip"""
    try:
        data = json.loads(request.body)
        scene_id = data.get('scene_id')
        frame = data.get('frame', 0)

        scene = get_object_or_404(Scene, id=scene_id)
        get_project_or_404(request.user, scene.project.id)

        # Queue preview render
        from .tasks import render_preview_frame
        result = render_preview_frame.delay(str(scene.id), frame)

        return JsonResponse({'status': 'processing', 'task_id': str(result.id)})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@require_http_methods(["GET"])
def api_export_status(request, export_id):
    """Get export status"""
    export = get_object_or_404(Export, id=export_id, project__user=request.user)

    data = {
        'status': export.status,
        'progress': export.progress,
        'error': export.error_message,
    }

    if export.status == 'completed' and export.output_file:
        data['download_url'] = f'/animator/exports/{export.id}/download/'

    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def api_synthesize_voice(request):
    """Synthesize voice from text"""
    try:
        data = json.loads(request.body)
        text = data.get('text')
        voice = data.get('voice', 'default')
        project_id = data.get('project_id')

        if not text or not project_id:
            return JsonResponse({'error': 'Missing text or project_id'}, status=400)

        project = get_project_or_404(request.user, project_id)

        # Queue voice synthesis
        from .tasks import synthesize_voice
        task_id = synthesize_voice.delay(str(project.id), text, voice)

        return JsonResponse({'status': 'processing', 'task_id': str(task_id)})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)


@login_required
@require_http_methods(["POST"])
def api_generate_lipsync(request):
    """Generate lip sync data for audio"""
    try:
        data = json.loads(request.body)
        audio_track_id = data.get('audio_track_id')
        scene_character_id = data.get('scene_character_id')

        if not audio_track_id or not scene_character_id:
            return JsonResponse({'error': 'Missing audio_track_id or scene_character_id'}, status=400)

        audio_track = get_object_or_404(AudioTrack, id=audio_track_id)
        scene_character = get_object_or_404(SceneCharacter, id=scene_character_id)

        get_project_or_404(request.user, audio_track.project.id)

        # Queue lip sync generation
        from .tasks import generate_lipsync_data
        task_id = generate_lipsync_data.delay(str(audio_track.id), str(scene_character.id))

        return JsonResponse({'status': 'processing', 'task_id': str(task_id)})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
