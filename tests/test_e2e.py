"""
End-to-end tests: signup -> verify -> upload drawing -> animate -> view result.
Tests the full user journey through the animateadrawing platform.
"""
import json
import struct
import uuid
import zlib
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from animator.models import (
    Project, Character, Scene, SceneCharacter, Export,
    MotionPreset, Animation, Background, Storyboard,
    CollaborationInvite, ProjectCollaborator,
)
from finances.models.plan import Plan
from translations.models.language import Language
from translations.models.translation import Translation


def _create_png():
    """Create a minimal valid 1x1 PNG image."""
    signature = b'\x89PNG\r\n\x1a\n'

    def _chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + c + crc

    ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0)
    raw_data = b'\x00\xff\x00\x00'
    compressed = zlib.compress(raw_data)
    return signature + _chunk(b'IHDR', ihdr_data) + _chunk(b'IDAT', compressed) + _chunk(b'IEND', b'')


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
    MEDIA_ROOT='/tmp/animateadrawing_test_media/',
)
class E2ETestBase(TestCase):
    """Base class for end-to-end tests with fixture setup."""

    @classmethod
    def setUpTestData(cls):
        cls.lang = Language.objects.create(name='English', en_label='English', iso='en')
        i18n_keys = {
            'missing_email': 'Email is required',
            'missing_password': 'Password is required',
            'invalid_email': 'Invalid email address',
            'email_taken': 'Email already in use',
            'weak_password': 'Password is too weak',
            'wrong_credentials': 'Wrong email or password',
            'missing_code': 'Verification code is required',
            'invalid_code': 'Invalid verification code',
            'forgot_password_email_sent': 'Password reset email sent',
            'site_description': 'Animate your drawings',
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
        }
        for code_name, text in i18n_keys.items():
            Translation.objects.create(code_name=code_name, language='en', text=text)

    def setUp(self):
        self.client = Client()


class FullUserJourneyTest(E2ETestBase):
    """
    Complete end-to-end flow:
    1. User visits homepage
    2. Signs up
    3. Verifies email
    4. Creates a project
    5. Uploads a drawing (character)
    6. Applies animation
    7. Exports and views result
    """

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_signup_verify_animate_export(self, mock_email):
        # -----------------------------------------------------------------
        # Step 1: Visit homepage
        # -----------------------------------------------------------------
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

        # -----------------------------------------------------------------
        # Step 2: Sign up
        # -----------------------------------------------------------------
        response = self.client.post(reverse('register'), {
            'email': 'e2e@example.com',
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 302)
        # User is created and logged in
        user = CustomUser.objects.get(email='e2e@example.com')
        self.assertFalse(user.is_confirm)
        mock_email.assert_called_once()

        # Following the redirect goes to /account/ which redirects to /verify/
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)  # Redirects to verify

        # -----------------------------------------------------------------
        # Step 3: Verify email with code
        # -----------------------------------------------------------------
        verification_code = user.verification_code
        response = self.client.post(reverse('verify'), {
            'code': verification_code,
        })
        self.assertEqual(response.status_code, 302)  # Redirects to account
        user.refresh_from_db()
        self.assertTrue(user.is_confirm)

        # Now account page is accessible
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)

        # -----------------------------------------------------------------
        # Step 4: Create a project
        # -----------------------------------------------------------------
        response = self.client.post(reverse('animator:project_create'), {
            'name': 'My Drawing',
            'project_type': 'quick',
            'width': 1920,
            'height': 1080,
            'fps': 30,
        })
        self.assertEqual(response.status_code, 302)
        project = Project.objects.get(user=user, name='My Drawing')
        self.assertEqual(project.project_type, 'quick')
        # An initial scene should be created
        self.assertEqual(project.scenes.count(), 1)

        # View project detail
        response = self.client.get(
            reverse('animator:project_detail', kwargs={'project_id': project.id})
        )
        self.assertEqual(response.status_code, 200)

        # -----------------------------------------------------------------
        # Step 5: Upload a character drawing
        # -----------------------------------------------------------------
        image_data = _create_png()
        image_file = SimpleUploadedFile('my_drawing.png', image_data, content_type='image/png')

        response = self.client.post(
            reverse('animator:character_upload', kwargs={'project_id': project.id}),
            {'name': 'Stick Figure', 'character_type': 'humanoid', 'image': image_file}
        )
        self.assertEqual(response.status_code, 302)
        character = Character.objects.get(project=project, name='Stick Figure')
        self.assertEqual(character.character_type, 'humanoid')
        self.assertTrue(character.original_image)

        # -----------------------------------------------------------------
        # Step 6: Auto-detect rig (mocked)
        # -----------------------------------------------------------------
        with mock.patch('animator.tasks.detect_character_rig.delay') as mock_detect:
            response = self.client.post(
                reverse('animator:api_detect_character', kwargs={'character_id': character.id})
            )
            self.assertEqual(response.status_code, 200)
            mock_detect.assert_called_once_with(str(character.id))

        # Simulate rig detection completing
        character.rig_data = {
            'joints': [
                {'name': 'head', 'x': 100, 'y': 50},
                {'name': 'torso', 'x': 100, 'y': 150},
                {'name': 'left_arm', 'x': 60, 'y': 120},
                {'name': 'right_arm', 'x': 140, 'y': 120},
            ]
        }
        character.is_rig_confirmed = False
        character.save()

        # Confirm the rig via API
        response = self.client.post(
            reverse('animator:api_save_rig', kwargs={'character_id': character.id}),
            data=json.dumps({'rig': character.rig_data}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        character.refresh_from_db()
        self.assertTrue(character.is_rig_confirmed)

        # -----------------------------------------------------------------
        # Step 7: Set up a scene with the character
        # -----------------------------------------------------------------
        scene = project.scenes.first()
        scene_char = SceneCharacter.objects.create(
            scene=scene,
            character=character,
            position_x=500.0,
            position_y=300.0,
            scale=1.0,
        )

        # Create a motion preset
        preset = MotionPreset.objects.create(
            name='Walk',
            category='locomotion',
            animation_method='transform',
            motion_data={'type': 'walk', 'speed': 1.0},
            duration_seconds=2.0,
            is_system=True,
        )

        # Apply animation to the character
        anim = Animation.objects.create(
            scene_character=scene_char,
            motion_preset=preset,
            start_time=0.0,
            duration=2.0,
            loop=True,
            easing='ease-in-out',
        )

        # Save scene via API
        response = self.client.post(
            reverse('animator:api_save_scene', kwargs={'scene_id': scene.id}),
            data=json.dumps({
                'duration': 5.0,
                'background_color': '#87CEEB',
                'camera': {'zoom': 1.0, 'x': 0.0, 'y': 0.0},
                'characters': [{
                    'id': str(scene_char.id),
                    'position': {'x': 500.0, 'y': 300.0},
                    'scale': 1.0,
                    'rotation': 0.0,
                    'z_index': 0,
                    'flip': False,
                }],
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

        # -----------------------------------------------------------------
        # Step 8: Export the animation
        # -----------------------------------------------------------------
        with mock.patch('animator.tasks.render_export.delay') as mock_render:
            response = self.client.post(
                reverse('animator:export_project', kwargs={'project_id': project.id}),
                {
                    'format': 'gif',
                    'quality': 'medium',
                    'include_audio': '',  # unchecked
                }
            )
            self.assertEqual(response.status_code, 302)
            mock_render.assert_called_once()

        export = Export.objects.get(project=project, format='gif')
        self.assertEqual(export.quality, 'medium')
        self.assertFalse(export.include_audio)
        self.assertEqual(export.status, 'queued')

        # Check export status via API
        response = self.client.get(
            reverse('animator:api_export_status', kwargs={'export_id': export.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')

        # Simulate export completion
        export.status = 'completed'
        export.progress = 100
        export.completed_at = timezone.now()
        export.save()

        # -----------------------------------------------------------------
        # Step 9: View the result
        # -----------------------------------------------------------------
        response = self.client.get(
            reverse('animator:export_status', kwargs={'export_id': export.id})
        )
        self.assertEqual(response.status_code, 200)

        # Verify via API that the export shows completed
        response = self.client.get(
            reverse('animator:api_export_status', kwargs={'export_id': export.id})
        )
        data = response.json()
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['progress'], 100)

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_quick_animate_flow(self, mock_email):
        """
        Simplified quick animate flow:
        1. Sign up and verify
        2. Use the quick animate page
        3. Upload drawing directly
        4. View result
        """
        # Sign up
        self.client.post(reverse('register'), {
            'email': 'quick@example.com',
            'password': 'testpass1234',
        })
        user = CustomUser.objects.get(email='quick@example.com')

        # Verify
        self.client.post(reverse('verify'), {'code': user.verification_code})
        user.refresh_from_db()
        self.assertTrue(user.is_confirm)

        # Visit quick animate page
        response = self.client.get(reverse('animator:quick_animate'))
        self.assertEqual(response.status_code, 200)

        # For the quick flow, creating a project and character is typically
        # handled client-side via AJAX. We simulate that here.
        project = Project.objects.create(
            user=user, name='Quick Animation', project_type='quick'
        )
        scene = Scene.objects.create(project=project, name='Scene 1', order=0)

        image_data = _create_png()
        character = Character.objects.create(
            project=project,
            name='Quick Drawing',
            character_type='humanoid',
            original_image=SimpleUploadedFile('quick.png', image_data, content_type='image/png'),
            is_rig_confirmed=True,
            rig_data={'joints': [{'name': 'head', 'x': 50, 'y': 50}]},
        )

        # Create export
        export = Export.objects.create(
            project=project,
            format='gif',
            quality='medium',
            status='completed',
            progress=100,
            completed_at=timezone.now(),
        )

        # View quick result
        response = self.client.get(
            reverse('animator:quick_result', kwargs={'export_id': export.id})
        )
        self.assertEqual(response.status_code, 200)


class PurchaseCreditsJourneyTest(E2ETestBase):
    """
    Test the credits purchase flow:
    1. Sign up and verify
    2. Visit pricing page
    3. Attempt to use API with no credits
    4. Upgrade account (mock payment)
    5. Successfully use API with credits
    """

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_purchase_and_use_credits(self, mock_email):
        # Sign up and verify
        self.client.post(reverse('register'), {
            'email': 'buyer@example.com',
            'password': 'testpass1234',
        })
        user = CustomUser.objects.get(email='buyer@example.com')
        self.client.post(reverse('verify'), {'code': user.verification_code})

        # View pricing
        plan = Plan.objects.create(
            name='Creator', code_name='creator', price=19, credits=100,
            days=30, is_subscription=False, is_active=True
        )
        response = self.client.get(reverse('pricing'))
        self.assertEqual(response.status_code, 200)

        # Try API deduct with no credits
        user.api_token = 'buyer-token-123'
        user.save()
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'buyer-token-123', 'file_count': 1},
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertFalse(data['credits'])  # No credits

        # Simulate successful payment (mock the payment processor)
        user.credits = 100
        user.plan_subscribed = 'creator'
        user.save()

        # Now API deduct works
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'buyer-token-123', 'file_count': 1},
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['credits'])
        self.assertEqual(data['remaining_credits'], 99)


class CollaborationFlowTest(E2ETestBase):
    """
    Test collaboration workflow:
    1. User A creates a project
    2. User A invites User B
    3. User B becomes a collaborator
    4. User B can access the project
    """

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_collaboration_invite_flow(self, mock_email):
        # Create two users
        user_a = CustomUser.objects.create_user(email='alice@example.com', password='pass1234')
        user_a.is_confirm = True
        user_a.save()

        user_b = CustomUser.objects.create_user(email='bob@example.com', password='pass1234')
        user_b.is_confirm = True
        user_b.save()

        # User A creates a project
        self.client.force_login(user_a)
        self.client.post(reverse('animator:project_create'), {
            'name': 'Collab Project',
            'project_type': 'short',
        })
        project = Project.objects.get(user=user_a, name='Collab Project')

        # User A invites User B
        response = self.client.post(
            reverse('animator:collaborator_invite', kwargs={'project_id': project.id}),
            {'email': 'bob@example.com', 'permission': 'edit'}
        )
        self.assertEqual(response.status_code, 302)

        # Verify invite was created
        invite = CollaborationInvite.objects.get(
            project=project, invited_email='bob@example.com'
        )
        self.assertFalse(invite.accepted)
        mock_email.assert_called()

        # Simulate accept: create collaborator record
        ProjectCollaborator.objects.create(
            project=project, user=user_b, permission='edit'
        )
        invite.accepted = True
        invite.accepted_at = timezone.now()
        invite.save()

        # User B can now access the project
        self.client.force_login(user_b)
        response = self.client.get(
            reverse('animator:project_detail', kwargs={'project_id': project.id})
        )
        self.assertEqual(response.status_code, 200)

        # User B can view scenes
        scene = project.scenes.first()
        if scene:
            response = self.client.get(
                reverse('animator:scene_editor', kwargs={'scene_id': scene.id})
            )
            self.assertEqual(response.status_code, 200)

        # User B cannot delete the project (only owner can)
        response = self.client.post(
            reverse('animator:project_delete', kwargs={'project_id': project.id})
        )
        # Redirects because the delete check fails (project.user != user_b)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(id=project.id).exists())


class MultiProjectManagementTest(E2ETestBase):
    """
    Test managing multiple projects:
    1. Create several projects
    2. Edit, delete, and filter projects
    3. Verify correct project counts
    """

    def test_multi_project_lifecycle(self):
        user = CustomUser.objects.create_user(email='multi@example.com', password='pass1234')
        user.is_confirm = True
        user.save()
        self.client.force_login(user)

        # Create 3 projects
        for name in ['Project A', 'Project B', 'Project C']:
            self.client.post(reverse('animator:project_create'), {
                'name': name, 'project_type': 'quick',
            })
        self.assertEqual(Project.objects.filter(user=user).count(), 3)

        # Edit project B
        proj_b = Project.objects.get(user=user, name='Project B')
        self.client.post(
            reverse('animator:project_edit', kwargs={'project_id': proj_b.id}),
            {'name': 'Project B (Edited)', 'description': 'Updated', 'width': 1280, 'height': 720, 'fps': 24}
        )
        proj_b.refresh_from_db()
        self.assertEqual(proj_b.name, 'Project B (Edited)')

        # Delete project C
        proj_c = Project.objects.get(user=user, name='Project C')
        self.client.post(
            reverse('animator:project_delete', kwargs={'project_id': proj_c.id})
        )
        self.assertEqual(Project.objects.filter(user=user).count(), 2)

        # Project list shows remaining 2 projects
        response = self.client.get(reverse('animator:project_list'))
        self.assertEqual(response.status_code, 200)


class AIAnimationGenerationTest(E2ETestBase):
    """
    Test the AI animation generation flow:
    1. Upload character
    2. Generate animation from text prompt
    3. Apply generated animation to scene
    """

    @mock.patch('animator.tasks.generate_motion_from_prompt.delay')
    def test_generate_animation_from_prompt(self, mock_gen):
        """Full flow: upload character, generate AI animation, apply to scene."""
        user = CustomUser.objects.create_user(email='aigen@example.com', password='pass1234')
        user.is_confirm = True
        user.credits = 50
        user.save()
        self.client.force_login(user)

        # Create project
        project = Project.objects.create(user=user, name='AI Animation Test')
        scene = Scene.objects.create(project=project, name='Scene 1', order=0)

        # Upload character
        image_data = _create_png()
        character = Character.objects.create(
            project=project,
            name='AI Char',
            character_type='humanoid',
            original_image=SimpleUploadedFile('ai.png', image_data, content_type='image/png'),
            is_rig_confirmed=True,
            rig_data={'joints': [{'name': 'head', 'x': 50, 'y': 50}]},
        )

        # Generate animation from prompt
        mock_gen.return_value = mock.Mock(id='gen-task-456')
        response = self.client.post(
            reverse('animator:api_generate_animation'),
            data=json.dumps({
                'prompt': 'make the character dance happily',
                'character_id': str(character.id),
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')
        mock_gen.assert_called_once_with(str(character.id), 'make the character dance happily')

        # Simulate the task completing: a custom preset is created
        preset = MotionPreset.objects.create(
            name='Generated: make the character dance happily',
            category='custom',
            motion_data={'keyframes': [1, 2, 3]},
            duration_seconds=3.0,
            user=user,
            is_system=False,
        )

        # Place character in scene with the generated animation
        scene_char = SceneCharacter.objects.create(
            scene=scene, character=character,
            position_x=400.0, position_y=300.0
        )
        animation = Animation.objects.create(
            scene_character=scene_char,
            motion_preset=preset,
            duration=3.0,
            loop=True,
        )

        # Verify via project data API
        response = self.client.get(
            reverse('animator:api_project_data', kwargs={'project_id': project.id})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['scenes']), 1)
        self.assertEqual(len(data['scenes'][0]['characters']), 1)
        self.assertEqual(len(data['scenes'][0]['characters'][0]['animations']), 1)


class PasswordResetE2ETest(E2ETestBase):
    """
    End-to-end password reset flow:
    1. User requests lost password email
    2. User uses token to set new password
    3. User logs in with new password
    """

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_full_password_reset_flow(self, mock_email):
        # Create user
        user = CustomUser.objects.create_user(email='reset@example.com', password='oldpass')

        # Step 1: Request password reset
        response = self.client.post(reverse('lost-password'), {
            'email': 'reset@example.com',
        })
        self.assertEqual(response.status_code, 200)
        mock_email.assert_called_once()
        user.refresh_from_db()
        token = user.restore_password_token
        self.assertIsNotNone(token)

        # Step 2: Visit restore password page
        response = self.client.get(reverse('restore-password'), {'token': token})
        self.assertEqual(response.status_code, 200)

        # Step 3: Set new password
        response = self.client.post(reverse('restore-password'), {
            'token': token,
            'password': 'newpass5678',
            'confirm_password': 'newpass5678',
        })
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass5678'))

        # Step 4: Login with new password
        response = self.client.post(reverse('login'), {
            'email': 'reset@example.com',
            'password': 'newpass5678',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account'), fetch_redirect_response=False)


class BackgroundManagementE2ETest(E2ETestBase):
    """Test background upload and AI generation flow."""

    def test_upload_background(self):
        """User can upload a custom background."""
        user = CustomUser.objects.create_user(email='bg@example.com', password='pass1234')
        user.is_confirm = True
        user.save()
        self.client.force_login(user)

        image_data = _create_png()
        response = self.client.post(
            reverse('animator:background_upload'),
            {
                'name': 'My Background',
                'image': SimpleUploadedFile('bg.png', image_data, content_type='image/png'),
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Background.objects.filter(user=user, name='My Background').exists())

    @mock.patch('animator.tasks.generate_background.delay')
    def test_generate_background_ai(self, mock_gen):
        """Authenticated user can generate AI background."""
        user = CustomUser.objects.create_user(email='aibg@example.com', password='pass1234')
        user.is_confirm = True
        user.save()
        self.client.force_login(user)

        response = self.client.post(
            reverse('animator:background_generate'),
            {'prompt': 'a beautiful sunset over mountains'},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'queued')
        mock_gen.assert_called_once_with(user.id, 'a beautiful sunset over mountains')

    def test_generate_background_unauthenticated(self):
        """Unauthenticated user cannot generate backgrounds."""
        response = self.client.post(
            reverse('animator:background_generate'),
            {'prompt': 'a forest'},
        )
        self.assertEqual(response.status_code, 401)


class VoiceSynthesisE2ETest(E2ETestBase):
    """Test voice synthesis and lip sync generation flow."""

    @mock.patch('animator.tasks.synthesize_voice.delay')
    def test_synthesize_voice(self, mock_synth):
        """Authenticated user can synthesize voice."""
        user = CustomUser.objects.create_user(email='voice@example.com', password='pass1234')
        user.is_confirm = True
        user.save()
        self.client.force_login(user)

        project = Project.objects.create(user=user, name='Voice Project')
        mock_synth.return_value = mock.Mock(id='synth-123')

        response = self.client.post(
            reverse('animator:api_synthesize_voice'),
            data=json.dumps({
                'text': 'Hello world, this is a test',
                'voice': 'default',
                'project_id': str(project.id),
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'processing')
        mock_synth.assert_called_once_with(str(project.id), 'Hello world, this is a test', 'default')

    def test_synthesize_voice_missing_fields(self):
        """Missing required fields returns 400."""
        user = CustomUser.objects.create_user(email='voice2@example.com', password='pass1234')
        self.client.force_login(user)

        response = self.client.post(
            reverse('animator:api_synthesize_voice'),
            data=json.dumps({'text': 'Hello'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)


class CreditDeductionDuringExportTest(E2ETestBase):
    """
    Test that the export flow correctly checks credit requirements
    and the API deduct endpoint works in conjunction.
    """

    def test_export_deducts_credits_via_task(self):
        """
        Verify the export flow and credit deduction pathway.
        The actual credit deduction happens in the render_export task.
        Here we test the API deduct endpoint separately and verify
        the export model records credit usage.
        """
        user = CustomUser.objects.create_user(email='export@example.com', password='pass1234')
        user.is_confirm = True
        user.credits = 50
        user.api_token = 'export-token'
        user.save()
        self.client.force_login(user)

        project = Project.objects.create(
            user=user, name='Export Credit Test', duration_seconds=10.0
        )
        Scene.objects.create(project=project, name='S1', order=0)

        # Queue export (mocked task)
        with mock.patch('animator.tasks.render_export.delay') as mock_render:
            response = self.client.post(
                reverse('animator:export_project', kwargs={'project_id': project.id}),
                {'format': 'mp4', 'quality': 'high'}
            )
            self.assertEqual(response.status_code, 302)
            mock_render.assert_called_once()

        export = Export.objects.get(project=project)
        self.assertEqual(export.status, 'queued')

        # Simulate the task completing and recording credit usage
        export.status = 'completed'
        export.credits_used = 30  # 10s * 3 (high quality multiplier)
        export.completed_at = timezone.now()
        export.save()

        # API deduct should also work independently
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'export-token', 'file_count': 5},
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['credits'])
        self.assertEqual(data['deducted'], 5)

        user.refresh_from_db()
        self.assertEqual(user.credits, 45)
