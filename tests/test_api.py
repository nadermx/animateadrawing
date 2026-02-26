"""
Tests for API endpoints: APIDeduct, RateLimit, CreditsConsume, CancelSubscription.
"""
import json
from unittest import mock

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser
from finances.models.plan import Plan
from translations.models.language import Language
from translations.models.translation import Translation


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class APITestBase(TestCase):
    """Base class for API tests with Language/Translation fixtures."""

    @classmethod
    def setUpTestData(cls):
        cls.lang = Language.objects.create(name='English', en_label='English', iso='en')
        i18n_keys = {
            'missing_email': 'Email is required',
            'missing_password': 'Password is required',
            'invalid_email': 'Invalid email address',
            'email_taken': 'Email already in use',
            'site_description': 'Animate your drawings',
        }
        for code_name, text in i18n_keys.items():
            Translation.objects.create(code_name=code_name, language='en', text=text)

    def setUp(self):
        self.client = Client()


class APIDeductTest(APITestBase):
    """Test the APIDeduct endpoint used by the GPU server for credit verification."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='apiuser@example.com', password='pass1234'
        )
        self.user.api_token = 'test-api-token-abc123'
        self.user.credits = 10
        self.user.save()

    def test_deduct_success(self):
        """Valid API key with sufficient credits deducts and returns success."""
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123', 'file_count': 1},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertTrue(data['credits'])
        self.assertEqual(data['remaining_credits'], 9)
        self.assertEqual(data['deducted'], 1)

        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, 9)

    def test_deduct_multiple_credits(self):
        """Deducting multiple credits at once works."""
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123', 'file_count': 5},
            content_type='application/json',
        )
        data = response.json()
        self.assertEqual(data['remaining_credits'], 5)
        self.assertEqual(data['deducted'], 5)

        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, 5)

    def test_deduct_insufficient_credits(self):
        """Insufficient credits returns authorized=True but credits=False."""
        self.user.credits = 2
        self.user.save()
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123', 'file_count': 5},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertFalse(data['credits'])
        self.assertEqual(data['remaining_credits'], 2)

        # Credits should NOT be deducted
        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, 2)

    def test_deduct_no_api_key(self):
        """Missing API key returns 400 with authorized=False."""
        response = self.client.post(
            reverse('api-deduct'),
            {},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['authorized'])
        self.assertFalse(data['credits'])

    def test_deduct_invalid_api_key(self):
        """Invalid API key returns 400 with authorized=False."""
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'nonexistent-key'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['authorized'])

    def test_deduct_active_plan_unlimited(self):
        """User with active plan gets unlimited credits response."""
        self.user.is_plan_active = True
        self.user.save()
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123', 'file_count': 1},
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertTrue(data['credits'])
        self.assertEqual(data['remaining_credits'], 'unlimited')

        # Credits should NOT be deducted for plan users
        self.user.refresh_from_db()
        self.assertEqual(self.user.credits, 10)

    def test_deduct_default_file_count(self):
        """file_count defaults to 1 when not provided."""
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123'},
            content_type='application/json',
        )
        data = response.json()
        self.assertEqual(data['deducted'], 1)
        self.assertEqual(data['remaining_credits'], 9)

    def test_deduct_compat_url(self):
        """The compatibility URL /account/api/deduct/ also works."""
        response = self.client.post(
            reverse('api-deduct-compat'),
            {'key': 'test-api-token-abc123', 'file_count': 1},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertTrue(data['credits'])

    def test_deduct_zero_credits_left(self):
        """User with 0 credits cannot deduct."""
        self.user.credits = 0
        self.user.save()
        response = self.client.post(
            reverse('api-deduct'),
            {'key': 'test-api-token-abc123', 'file_count': 1},
            content_type='application/json',
        )
        data = response.json()
        self.assertTrue(data['authorized'])
        self.assertFalse(data['credits'])
        self.assertEqual(data['remaining_credits'], 0)


class RateLimitTest(APITestBase):
    """Test the RateLimit endpoint at /api/accounts/rate_limit/."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='ratelimit@example.com', password='pass1234'
        )
        self.url = reverse('rate-limit')

    def test_rate_limit_authenticated_with_plan(self):
        """Authenticated user with active plan always gets status=True."""
        self.user.is_plan_active = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            json.dumps({'files_data': [{'size': 1000}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])

    def test_rate_limit_authenticated_with_credits(self):
        """Authenticated user with credits gets status=True."""
        self.user.credits = 5
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            json.dumps({'files_data': [{'size': 1000}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])

    def test_rate_limit_unauthenticated_first_request(self):
        """First anonymous request within rate limit succeeds."""
        response = self.client.post(
            self.url,
            json.dumps({'files_data': [{'size': 1000}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['status'])

    @override_settings(
        CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    )
    def test_rate_limit_file_size_exceeded_no_auth(self):
        """Anonymous user exceeding file limit gets limit_exceeded error."""
        # FILES_LIMIT is 2147483648 (2GB) by default
        # Using a massive size to exceed it
        response = self.client.post(
            self.url,
            json.dumps({'files_data': [{'size': 3000000000}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertTrue(data.get('limit_exceeded'))

    def test_rate_limit_returns_ip(self):
        """RateLimit response includes the client IP."""
        response = self.client.post(
            self.url,
            json.dumps({'files_data': [{'size': 1000}]}),
            content_type='application/json',
        )
        data = response.json()
        self.assertIn('ip', data)
        self.assertIn('cache_key', data)


class CreditsConsumeTest(APITestBase):
    """Test the CreditsConsume endpoint at /api/accounts/consume/."""

    def test_consume_credits_authenticated(self):
        """Authenticated user can consume 1 credit."""
        user = CustomUser.objects.create_user(
            email='consume@example.com', password='pass1234'
        )
        user.credits = 5
        user.save()
        self.client.force_login(user)

        response = self.client.post(
            reverse('credits-consume'),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.credits, 4)

    def test_consume_credits_at_zero(self):
        """Consuming when credits are 0 keeps credits at 0."""
        user = CustomUser.objects.create_user(
            email='zero@example.com', password='pass1234'
        )
        user.credits = 0
        user.save()
        self.client.force_login(user)

        response = self.client.post(
            reverse('credits-consume'),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.credits, 0)


class CancelSubscriptionAPITest(APITestBase):
    """Test the CancelSubscription API endpoint at /api/accounts/cancel-subscription/."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='cancelsub@example.com', password='pass1234'
        )
        self.user.is_plan_active = True
        self.user.processor = 'stripe'
        self.user.payment_nonce = 'cus_test123'
        self.user.card_nonce = 'card_test123'
        self.user.next_billing_date = timezone.now() + timezone.timedelta(days=30)
        self.user.save()

    def test_cancel_subscription_api_success(self):
        """Authenticated user can cancel subscription via API."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('cancel-subscription'),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_plan_active)
        self.assertIsNone(self.user.card_nonce)
        self.assertIsNone(self.user.payment_nonce)
        self.assertIsNone(self.user.processor)
        self.assertIsNone(self.user.next_billing_date)

    def test_cancel_subscription_unauthenticated(self):
        """Unauthenticated request to cancel-subscription returns error."""
        response = self.client.post(
            reverse('cancel-subscription'),
            content_type='application/json',
        )
        # The view checks user.is_authenticated, which returns False for AnonymousUser
        self.assertEqual(response.status_code, 400)


class ResendVerificationAPITest(APITestBase):
    """Test the ResendVerificationEmail API endpoint."""

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_resend_verification_authenticated(self, mock_email):
        """Authenticated user can request verification email resend."""
        user = CustomUser.objects.create_user(
            email='resend@example.com', password='pass1234'
        )
        self.client.force_login(user)
        response = self.client.post(
            reverse('resend-verification'),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        mock_email.assert_called_once()
