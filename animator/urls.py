from django.urls import path
from . import views

app_name = 'animator'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Projects
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<uuid:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<uuid:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<uuid:project_id>/delete/', views.project_delete, name='project_delete'),

    # Quick Animation (single page workflow)
    path('quick/', views.quick_animate, name='quick_animate'),
    path('quick/result/<uuid:export_id>/', views.quick_result, name='quick_result'),

    # Characters
    path('projects/<uuid:project_id>/characters/', views.character_list, name='character_list'),
    path('projects/<uuid:project_id>/characters/upload/', views.character_upload, name='character_upload'),
    path('characters/<uuid:character_id>/', views.character_detail, name='character_detail'),
    path('characters/<uuid:character_id>/rig/', views.character_rig_editor, name='character_rig_editor'),
    path('characters/<uuid:character_id>/delete/', views.character_delete, name='character_delete'),

    # Scenes
    path('projects/<uuid:project_id>/scenes/', views.scene_list, name='scene_list'),
    path('projects/<uuid:project_id>/scenes/create/', views.scene_create, name='scene_create'),
    path('scenes/<uuid:scene_id>/', views.scene_editor, name='scene_editor'),
    path('scenes/<uuid:scene_id>/delete/', views.scene_delete, name='scene_delete'),

    # Timeline editor (for full projects)
    path('projects/<uuid:project_id>/timeline/', views.timeline_editor, name='timeline_editor'),

    # Storyboard
    path('projects/<uuid:project_id>/storyboard/', views.storyboard_editor, name='storyboard_editor'),

    # Export
    path('projects/<uuid:project_id>/export/', views.export_project, name='export_project'),
    path('exports/<uuid:export_id>/', views.export_status, name='export_status'),
    path('exports/<uuid:export_id>/download/', views.export_download, name='export_download'),

    # Motion presets
    path('motion-presets/', views.motion_preset_list, name='motion_preset_list'),
    path('motion-presets/<uuid:preset_id>/preview/', views.motion_preset_preview, name='motion_preset_preview'),

    # Backgrounds
    path('backgrounds/', views.background_library, name='background_library'),
    path('backgrounds/upload/', views.background_upload, name='background_upload'),
    path('backgrounds/generate/', views.background_generate, name='background_generate'),

    # Character templates
    path('templates/', views.template_library, name='template_library'),

    # Collaboration
    path('projects/<uuid:project_id>/collaborators/', views.collaborator_list, name='collaborator_list'),
    path('projects/<uuid:project_id>/collaborators/invite/', views.collaborator_invite, name='collaborator_invite'),

    # API endpoints for AJAX
    path('api/projects/<uuid:project_id>/data/', views.api_project_data, name='api_project_data'),
    path('api/characters/<uuid:character_id>/detect/', views.api_detect_character, name='api_detect_character'),
    path('api/characters/<uuid:character_id>/rig/', views.api_save_rig, name='api_save_rig'),
    path('api/scenes/<uuid:scene_id>/data/', views.api_scene_data, name='api_scene_data'),
    path('api/scenes/<uuid:scene_id>/save/', views.api_save_scene, name='api_save_scene'),
    path('api/animations/generate/', views.api_generate_animation, name='api_generate_animation'),
    path('api/render/preview/', views.api_render_preview, name='api_render_preview'),
    path('api/export/<uuid:export_id>/status/', views.api_export_status, name='api_export_status'),
    path('api/voice/synthesize/', views.api_synthesize_voice, name='api_synthesize_voice'),
    path('api/lipsync/generate/', views.api_generate_lipsync, name='api_generate_lipsync'),
]
