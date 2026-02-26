"""
Tests for all page loads: public pages, authenticated pages, and animator pages.
Ensures every URL returns the expected status code.
"""
import uuid
from io import BytesIO
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from animator.models import (
    Project, Character, Scene, SceneCharacter, Export,
    MotionPreset, Background, CharacterTemplate, Storyboard,
    StoryboardPanel, AudioTrack, Animation,
)
from finances.models.plan import Plan
from translations.models.language import Language
from translations.models.translation import Translation


def _small_image():
    """Create a minimal valid PNG image for file uploads."""
    # Minimal 1x1 red PNG
    import struct
    import zlib

    def _create_png():
        signature = b'\x89PNG\r\n\x1a\n'

        def _chunk(chunk_type, data):
            c = chunk_type + data
            crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
            return struct.pack('>I', len(data)) + c + crc

        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
        raw_data = b'\x00\xff\x00\x00'
        compressed = zlib.compress(raw_data)

        return signature + _chunk(b'IHDR', ihdr_data) + _chunk(b'IDAT', compressed) + _chunk(b'IEND', b'')

    return _create_png()


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
    MEDIA_ROOT='/tmp/animateadrawing_test_media/',
)
class PageTestBase(TestCase):
    """Base class for page load tests with common fixtures."""

    @classmethod
    def setUpTestData(cls):
        cls.lang = Language.objects.create(name='English', en_label='English', iso='en')
        i18n_keys = {
            'site_description': 'Animate your drawings',
            'contact': 'Contact',
            'contact_meta_description': 'Contact us',
            'about_us': 'About Us',
            'about_us_meta_description': 'About us',
            'terms_of_service': 'Terms of Service',
            'privacy_policy': 'Privacy Policy',
            'login': 'Login',
            'sign_up': 'Sign Up',
            'lost_password': 'Lost Password',
            'restore_your_password': 'Restore Password',
            'verify_email': 'Verify Email',
            'account_label': 'Account',
            'pricing': 'Pricing',
            'checkout': 'Checkout',
            'success': 'Success',
            'refund': 'Refund',
            'cancel': 'Cancel',
            'delete': 'Delete Account',
            'deleted': 'Account Deleted',
        }
        for code_name, text in i18n_keys.items():
            Translation.objects.create(code_name=code_name, language='en', text=text)

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='pagetest@example.com', password='pass1234'
        )
        self.user.is_confirm = True
        self.user.save()


class PublicPageLoadTest(PageTestBase):
    """Test all public pages return 200."""

    def test_index_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    def test_terms_page(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)

    def test_privacy_page(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    def test_how_it_works_page(self):
        response = self.client.get(reverse('how-it-works'))
        self.assertEqual(response.status_code, 200)

    def test_examples_page(self):
        response = self.client.get(reverse('examples'))
        self.assertEqual(response.status_code, 200)

    def test_tutorials_page(self):
        response = self.client.get(reverse('tutorials'))
        self.assertEqual(response.status_code, 200)

    def test_faq_page(self):
        response = self.client.get(reverse('faq'))
        self.assertEqual(response.status_code, 200)

    def test_pricing_page(self):
        response = self.client.get(reverse('pricing'))
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_register_page(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_lost_password_page(self):
        response = self.client.get(reverse('lost-password'))
        self.assertEqual(response.status_code, 200)

    def test_success_page(self):
        response = self.client.get(reverse('success'))
        self.assertEqual(response.status_code, 200)

    def test_refund_page(self):
        response = self.client.get(reverse('refund'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page(self):
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)

    def test_sitemap_xml(self):
        response = self.client.get(reverse('sitemap'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')
        self.assertIn(b'<urlset', response.content)

    def test_robots_txt(self):
        response = self.client.get(reverse('robots'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertIn(b'User-agent', response.content)

    def test_api_docs_page(self):
        response = self.client.get(reverse('api-docs'))
        self.assertEqual(response.status_code, 200)


class UseCaseLandingPageTest(PageTestBase):
    """Test SEO use-case landing pages."""

    def test_content_creators_page(self):
        response = self.client.get(reverse('usecase-content-creators'))
        self.assertEqual(response.status_code, 200)

    def test_educators_page(self):
        response = self.client.get(reverse('usecase-educators'))
        self.assertEqual(response.status_code, 200)

    def test_game_dev_page(self):
        response = self.client.get(reverse('usecase-gamedev'))
        self.assertEqual(response.status_code, 200)

    def test_artists_page(self):
        response = self.client.get(reverse('usecase-artists'))
        self.assertEqual(response.status_code, 200)


class FeaturePageTest(PageTestBase):
    """Test SEO feature pages."""

    def test_pose_detection_page(self):
        response = self.client.get(reverse('feature-pose-detection'))
        self.assertEqual(response.status_code, 200)

    def test_motion_presets_page(self):
        response = self.client.get(reverse('feature-motion-presets'))
        self.assertEqual(response.status_code, 200)

    def test_export_formats_page(self):
        response = self.client.get(reverse('feature-export-formats'))
        self.assertEqual(response.status_code, 200)


class AuthenticatedPageLoadTest(PageTestBase):
    """Test pages that require authentication."""

    def test_account_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)

    def test_verify_page_unverified(self):
        """Unverified user sees the verify page."""
        self.user.is_confirm = False
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse('verify'))
        self.assertEqual(response.status_code, 200)

    def test_cancel_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cancel'))
        self.assertEqual(response.status_code, 200)

    def test_delete_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('delete'))
        self.assertEqual(response.status_code, 200)

    def test_checkout_page_with_plan(self):
        """Checkout page loads when plan exists."""
        plan = Plan.objects.create(
            name='Starter', code_name='starter', price=9, credits=100, days=30
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse('checkout'), {'plan': 'starter'})
        self.assertEqual(response.status_code, 200)

    def test_checkout_page_no_plan(self):
        """Checkout page without plan param redirects to pricing."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)

    def test_checkout_redirects_unauthenticated(self):
        """Unauthenticated user at checkout is redirected to register."""
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)


class AuthRedirectTest(PageTestBase):
    """Test that auth-required pages redirect unauthenticated users."""

    def test_account_redirects(self):
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)

    def test_cancel_redirects(self):
        response = self.client.get(reverse('cancel'))
        self.assertEqual(response.status_code, 302)

    def test_delete_redirects(self):
        response = self.client.get(reverse('delete'))
        self.assertEqual(response.status_code, 302)


class AnimatorPageLoadTest(PageTestBase):
    """Test animator pages that require authentication."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.project = Project.objects.create(
            user=self.user,
            name='Test Project',
            project_type='quick',
        )
        # Create a character with a real image file
        image_content = _small_image()
        self.character = Character.objects.create(
            project=self.project,
            name='Test Character',
            character_type='humanoid',
            original_image=SimpleUploadedFile('test.png', image_content, content_type='image/png'),
        )
        self.scene = Scene.objects.create(
            project=self.project,
            name='Scene 1',
            order=0,
        )
        self.export = Export.objects.create(
            project=self.project,
            format='mp4',
            quality='high',
            status='queued',
        )

    def test_dashboard(self):
        response = self.client.get(reverse('animator:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_project_list(self):
        response = self.client.get(reverse('animator:project_list'))
        self.assertEqual(response.status_code, 200)

    def test_project_create_get(self):
        response = self.client.get(reverse('animator:project_create'))
        self.assertEqual(response.status_code, 200)

    @mock.patch('animator.views.Scene.objects.create')
    def test_project_create_post(self, mock_scene_create):
        """POST to project_create creates a project and redirects."""
        mock_scene_create.return_value = Scene(
            project=self.project, name='Scene 1', order=0
        )
        response = self.client.post(reverse('animator:project_create'), {
            'name': 'New Project',
            'project_type': 'quick',
            'width': 1920,
            'height': 1080,
            'fps': 30,
        })
        self.assertEqual(response.status_code, 302)

    def test_project_detail(self):
        response = self.client.get(
            reverse('animator:project_detail', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_project_edit_get(self):
        response = self.client.get(
            reverse('animator:project_edit', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_project_edit_post(self):
        response = self.client.post(
            reverse('animator:project_edit', kwargs={'project_id': self.project.id}),
            {'name': 'Renamed', 'description': 'New desc', 'width': 1280, 'height': 720, 'fps': 24}
        )
        self.assertEqual(response.status_code, 302)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Renamed')

    def test_project_delete_post(self):
        """POST to project_delete removes the project."""
        project_id = self.project.id
        response = self.client.post(
            reverse('animator:project_delete', kwargs={'project_id': project_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(id=project_id).exists())

    def test_project_delete_get_redirects(self):
        """GET to project_delete redirects back to detail."""
        response = self.client.get(
            reverse('animator:project_delete', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 302)

    def test_quick_animate(self):
        response = self.client.get(reverse('animator:quick_animate'))
        self.assertEqual(response.status_code, 200)

    def test_quick_result(self):
        self.export.status = 'completed'
        self.export.save()
        response = self.client.get(
            reverse('animator:quick_result', kwargs={'export_id': self.export.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_character_list(self):
        response = self.client.get(
            reverse('animator:character_list', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_character_upload_get(self):
        response = self.client.get(
            reverse('animator:character_upload', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_character_detail(self):
        response = self.client.get(
            reverse('animator:character_detail', kwargs={'character_id': self.character.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_character_rig_editor(self):
        response = self.client.get(
            reverse('animator:character_rig_editor', kwargs={'character_id': self.character.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_character_delete_post(self):
        char_id = self.character.id
        response = self.client.post(
            reverse('animator:character_delete', kwargs={'character_id': char_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Character.objects.filter(id=char_id).exists())

    def test_scene_list(self):
        response = self.client.get(
            reverse('animator:scene_list', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_scene_create_post(self):
        """POST to scene_create creates a scene and redirects to editor."""
        response = self.client.post(
            reverse('animator:scene_create', kwargs={'project_id': self.project.id}),
            {'name': 'Scene 2', 'duration': 5.0}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.project.scenes.count(), 2)

    def test_scene_editor(self):
        response = self.client.get(
            reverse('animator:scene_editor', kwargs={'scene_id': self.scene.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_scene_delete_post(self):
        scene_id = self.scene.id
        response = self.client.post(
            reverse('animator:scene_delete', kwargs={'scene_id': scene_id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Scene.objects.filter(id=scene_id).exists())

    def test_timeline_editor(self):
        response = self.client.get(
            reverse('animator:timeline_editor', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_storyboard_editor(self):
        response = self.client.get(
            reverse('animator:storyboard_editor', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    @mock.patch('animator.tasks.render_export.delay')
    def test_export_project_get(self, mock_task):
        response = self.client.get(
            reverse('animator:export_project', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_export_status(self):
        response = self.client.get(
            reverse('animator:export_status', kwargs={'export_id': self.export.id})
        )
        self.assertEqual(response.status_code, 200)

    def test_motion_preset_list_public(self):
        """Motion preset list is publicly accessible."""
        self.client.logout()
        response = self.client.get(reverse('animator:motion_preset_list'))
        self.assertEqual(response.status_code, 200)

    def test_motion_preset_list_authenticated(self):
        response = self.client.get(reverse('animator:motion_preset_list'))
        self.assertEqual(response.status_code, 200)

    def test_background_library_public(self):
        """Background library is publicly accessible."""
        self.client.logout()
        response = self.client.get(reverse('animator:background_library'))
        self.assertEqual(response.status_code, 200)

    def test_background_generate_get(self):
        """Background generate page is publicly accessible."""
        response = self.client.get(reverse('animator:background_generate'))
        self.assertEqual(response.status_code, 200)

    def test_template_library_public(self):
        """Template library is publicly accessible."""
        self.client.logout()
        response = self.client.get(reverse('animator:template_library'))
        self.assertEqual(response.status_code, 200)

    def test_collaborator_list(self):
        response = self.client.get(
            reverse('animator:collaborator_list', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)


class AnimatorLoginRequiredTest(PageTestBase):
    """Test that animator pages requiring login redirect unauthenticated users."""

    def setUp(self):
        super().setUp()
        # Create project as the user, but don't log in
        self.project = Project.objects.create(
            user=self.user, name='Private Project'
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('animator:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_project_list_requires_login(self):
        response = self.client.get(reverse('animator:project_list'))
        self.assertEqual(response.status_code, 302)

    def test_project_create_requires_login(self):
        response = self.client.get(reverse('animator:project_create'))
        self.assertEqual(response.status_code, 302)

    def test_quick_animate_requires_login(self):
        response = self.client.get(reverse('animator:quick_animate'))
        self.assertEqual(response.status_code, 302)


class AnimatorAccessControlTest(PageTestBase):
    """Test that users cannot access other users' projects."""

    def setUp(self):
        super().setUp()
        self.other_user = CustomUser.objects.create_user(
            email='other@example.com', password='pass1234'
        )
        self.other_project = Project.objects.create(
            user=self.other_user, name='Other Project'
        )
        self.client.force_login(self.user)

    def test_cannot_view_other_project(self):
        """User gets 404 when accessing another user's project."""
        response = self.client.get(
            reverse('animator:project_detail', kwargs={'project_id': self.other_project.id})
        )
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_other_project(self):
        """User cannot delete another user's project."""
        response = self.client.post(
            reverse('animator:project_delete', kwargs={'project_id': self.other_project.id})
        )
        self.assertEqual(response.status_code, 404)


class AnimatorAPIEndpointTest(PageTestBase):
    """Test animator JSON API endpoints."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.project = Project.objects.create(
            user=self.user, name='API Test Project'
        )
        image_content = _small_image()
        self.character = Character.objects.create(
            project=self.project,
            name='API Char',
            character_type='humanoid',
            original_image=SimpleUploadedFile('test.png', image_content, content_type='image/png'),
        )
        self.scene = Scene.objects.create(
            project=self.project, name='Scene 1', order=0
        )
        self.export = Export.objects.create(
            project=self.project, format='mp4', status='completed',
        )

    def test_api_project_data(self):
        """GET project data returns JSON with project info."""
        response = self.client.get(
            reverse('animator:api_project_data', kwargs={'project_id': self.project.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'API Test Project')
        self.assertIn('scenes', data)
        self.assertIn('characters', data)

    def test_api_scene_data(self):
        """GET scene data returns JSON with scene info."""
        response = self.client.get(
            reverse('animator:api_scene_data', kwargs={'scene_id': self.scene.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Scene 1')

    @mock.patch('animator.tasks.detect_character_rig.delay')
    def test_api_detect_character(self, mock_task):
        """POST to detect character queues the task."""
        response = self.client.post(
            reverse('animator:api_detect_character', kwargs={'character_id': self.character.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')
        mock_task.assert_called_once_with(str(self.character.id))

    def test_api_save_rig(self):
        """POST to save rig updates character rig data."""
        rig_data = {'joints': [{'name': 'head', 'x': 100, 'y': 50}]}
        response = self.client.post(
            reverse('animator:api_save_rig', kwargs={'character_id': self.character.id}),
            data=json.dumps({'rig': rig_data}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.character.refresh_from_db()
        self.assertEqual(self.character.rig_data, rig_data)
        self.assertTrue(self.character.is_rig_confirmed)

    def test_api_save_rig_invalid_json(self):
        """POST with invalid JSON returns 400."""
        response = self.client.post(
            reverse('animator:api_save_rig', kwargs={'character_id': self.character.id}),
            data='not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_api_save_scene(self):
        """POST to save scene updates scene data."""
        response = self.client.post(
            reverse('animator:api_save_scene', kwargs={'scene_id': self.scene.id}),
            data=json.dumps({
                'duration': 10.0,
                'background_color': '#FF0000',
                'camera': {'zoom': 1.5, 'x': 10.0, 'y': 20.0},
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.scene.refresh_from_db()
        self.assertEqual(self.scene.duration, 10.0)
        self.assertEqual(self.scene.background_color, '#FF0000')
        self.assertAlmostEqual(self.scene.camera_zoom, 1.5)

    @mock.patch('animator.tasks.generate_motion_from_prompt.delay')
    def test_api_generate_animation(self, mock_task):
        """POST to generate animation queues the task."""
        mock_task.return_value = mock.Mock(id='task-123')
        response = self.client.post(
            reverse('animator:api_generate_animation'),
            data=json.dumps({
                'prompt': 'walk forward',
                'character_id': str(self.character.id),
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')

    def test_api_generate_animation_missing_fields(self):
        """Missing prompt or character_id returns 400."""
        response = self.client.post(
            reverse('animator:api_generate_animation'),
            data=json.dumps({'prompt': 'walk'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_api_export_status(self):
        """GET export status returns JSON with status info."""
        response = self.client.get(
            reverse('animator:api_export_status', kwargs={'export_id': self.export.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'completed')

    @mock.patch('animator.tasks.render_preview_frame.delay')
    def test_api_render_preview(self, mock_task):
        """POST to render preview queues the task."""
        mock_task.return_value = mock.Mock(id='preview-123')
        response = self.client.post(
            reverse('animator:api_render_preview'),
            data=json.dumps({
                'scene_id': str(self.scene.id),
                'frame': 0,
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')


class PaginationAndFilterTest(PageTestBase):
    """Test pagination and filtering on project list."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        # Create multiple projects
        for i in range(15):
            Project.objects.create(
                user=self.user,
                name=f'Project {i}',
                project_type='quick' if i % 2 == 0 else 'short',
                status='draft' if i % 3 == 0 else 'completed',
            )

    def test_project_list_pagination(self):
        """Project list supports pagination."""
        response = self.client.get(reverse('animator:project_list'), {'page': 1})
        self.assertEqual(response.status_code, 200)

        response2 = self.client.get(reverse('animator:project_list'), {'page': 2})
        self.assertEqual(response2.status_code, 200)

    def test_project_list_filter_type(self):
        """Project list can filter by type."""
        response = self.client.get(reverse('animator:project_list'), {'type': 'quick'})
        self.assertEqual(response.status_code, 200)

    def test_project_list_filter_status(self):
        """Project list can filter by status."""
        response = self.client.get(reverse('animator:project_list'), {'status': 'draft'})
        self.assertEqual(response.status_code, 200)

    def test_motion_preset_list_filter_category(self):
        """Motion preset list can filter by category."""
        MotionPreset.objects.create(
            name='Walk', category='locomotion', is_system=True
        )
        response = self.client.get(
            reverse('animator:motion_preset_list'), {'category': 'locomotion'}
        )
        self.assertEqual(response.status_code, 200)
