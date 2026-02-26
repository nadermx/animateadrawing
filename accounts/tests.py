"""
Tests for accounts app: user registration, login, logout, password reset, email verification.
"""
from unittest import mock

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser, EmailAddress
from translations.models.language import Language
from translations.models.translation import Translation


@override_settings(
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    SESSION_ENGINE='django.contrib.sessions.backends.db',
)
class AccountTestBase(TestCase):
    """Base class that sets up Language and Translation fixtures required by GlobalVars."""

    @classmethod
    def setUpTestData(cls):
        cls.lang = Language.objects.create(name='English', en_label='English', iso='en')
        # Minimal i18n keys used by accounts model methods and views
        i18n_keys = {
            'missing_email': 'Email is required',
            'missing_password': 'Password is required',
            'invalid_email': 'Invalid email address',
            'email_taken': 'Email already in use',
            'weak_password': 'Password is too weak',
            'wrong_credentials': 'Wrong email or password',
            'missing_current_password': 'Current password is required',
            'missing_new_password': 'New password is required',
            'missing_confirm_new_password': 'Confirm new password is required',
            'passwords_dont_match': 'Passwords do not match',
            'wrong_current_password': 'Wrong current password',
            'password_changed': 'Password changed',
            'missing_code': 'Verification code is required',
            'invalid_code': 'Invalid verification code',
            'forgot_password_email_sent': 'Password reset email sent',
            'email_sent_wait': 'Email already sent, please wait',
            'missing_restore_token': 'Missing restore token',
            'missing_confirm_password': 'Confirm password is required',
            'invalid_restore_token': 'Invalid restore token',
            'login': 'Login',
            'sign_up': 'Sign Up',
            'lost_password': 'Lost Password',
            'restore_your_password': 'Restore Password',
            'verify_email': 'Verify Email',
            'account_label': 'Account',
            'site_description': 'Animate your drawings',
        }
        for code_name, text in i18n_keys.items():
            Translation.objects.create(code_name=code_name, language='en', text=text)

    def setUp(self):
        self.client = Client()


class UserRegistrationTest(AccountTestBase):
    """Test user signup flow via POST to /signup/."""

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_register_success(self, mock_email):
        """Successful registration creates a user, logs in, and redirects to account."""
        response = self.client.post(reverse('register'), {
            'email': 'newuser@example.com',
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account'), fetch_redirect_response=False)

        user = CustomUser.objects.get(email='newuser@example.com')
        self.assertFalse(user.is_confirm)
        self.assertIsNotNone(user.verification_code)
        self.assertEqual(user.credits, 0)
        mock_email.assert_called_once()

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_register_duplicate_email(self, mock_email):
        """Registering with an existing email shows an error."""
        CustomUser.objects.create_user(email='taken@example.com', password='pass1234')
        response = self.client.post(reverse('register'), {
            'email': 'taken@example.com',
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email already in use')

    def test_register_missing_email(self):
        """Registration without email shows validation error."""
        response = self.client.post(reverse('register'), {
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email is required')

    def test_register_missing_password(self):
        """Registration without password shows validation error."""
        response = self.client.post(reverse('register'), {
            'email': 'user@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password is required')

    def test_register_weak_password(self):
        """Registration with short password shows weak password error."""
        response = self.client.post(reverse('register'), {
            'email': 'user@example.com',
            'password': 'ab',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password is too weak')

    def test_register_invalid_email(self):
        """Registration with invalid email format shows error."""
        response = self.client.post(reverse('register'), {
            'email': 'not-an-email',
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email')

    def test_register_page_get(self):
        """GET /signup/ returns 200 with register form."""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_register_page_redirects_authenticated_user(self):
        """Authenticated user visiting /signup/ is redirected to account."""
        user = CustomUser.objects.create_user(email='existing@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 302)

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_register_normalizes_email(self, mock_email):
        """Email addresses are lowercased during registration."""
        self.client.post(reverse('register'), {
            'email': 'TestUser@Example.COM',
            'password': 'testpass1234',
        })
        self.assertTrue(CustomUser.objects.filter(email='testuser@example.com').exists())


class UserLoginTest(AccountTestBase):
    """Test user login flow via POST to /login/."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='loginuser@example.com', password='correctpass'
        )

    def test_login_success(self):
        """Valid credentials log the user in and redirect."""
        response = self.client.post(reverse('login'), {
            'email': 'loginuser@example.com',
            'password': 'correctpass',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account'), fetch_redirect_response=False)

    def test_login_wrong_password(self):
        """Wrong password shows error and stays on login page."""
        response = self.client.post(reverse('login'), {
            'email': 'loginuser@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wrong email or password')

    def test_login_nonexistent_user(self):
        """Non-existent email shows wrong credentials error."""
        response = self.client.post(reverse('login'), {
            'email': 'nobody@example.com',
            'password': 'anypass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Wrong email or password')

    def test_login_missing_fields(self):
        """Missing email or password shows appropriate errors."""
        response = self.client.post(reverse('login'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email is required')

    def test_login_page_get(self):
        """GET /login/ returns the login page."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_page_redirects_authenticated_user(self):
        """Authenticated user visiting /login/ is redirected to account."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)

    def test_login_case_insensitive_email(self):
        """Login works regardless of email casing."""
        response = self.client.post(reverse('login'), {
            'email': 'LOGINUSER@EXAMPLE.COM',
            'password': 'correctpass',
        })
        self.assertEqual(response.status_code, 302)


class UserLogoutTest(AccountTestBase):
    """Test user logout flow."""

    def test_logout_redirects_to_index(self):
        """Logging out redirects to the index page."""
        user = CustomUser.objects.create_user(email='logoutuser@example.com', password='pass1234')
        self.client.force_login(user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('index'), fetch_redirect_response=False)

    def test_logout_clears_session(self):
        """After logout, the user is no longer authenticated."""
        user = CustomUser.objects.create_user(email='logoutuser@example.com', password='pass1234')
        self.client.force_login(user)
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('login'))
        # Should see login page, not redirect to account
        self.assertEqual(response.status_code, 200)


class LostPasswordTest(AccountTestBase):
    """Test the lost password / password reset request flow."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='forgot@example.com', password='oldpass1234'
        )

    def test_lost_password_page_get(self):
        """GET /lost-password/ returns the form."""
        response = self.client.get(reverse('lost-password'))
        self.assertEqual(response.status_code, 200)

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_lost_password_sends_email(self, mock_email):
        """Submitting a valid email sends a password reset email."""
        response = self.client.post(reverse('lost-password'), {
            'email': 'forgot@example.com',
        })
        self.assertEqual(response.status_code, 200)
        mock_email.assert_called_once()
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.restore_password_token)

    def test_lost_password_nonexistent_email(self):
        """Submitting a non-existent email shows error."""
        response = self.client.post(reverse('lost-password'), {
            'email': 'nobody@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email')

    def test_lost_password_missing_email(self):
        """Submitting without email shows error."""
        response = self.client.post(reverse('lost-password'), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email is required')

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_lost_password_rate_limit(self, mock_email):
        """Requesting password reset twice within 10 minutes shows rate limit error."""
        self.user.lost_password_email_sent_at = timezone.now()
        self.user.save()
        response = self.client.post(reverse('lost-password'), {
            'email': 'forgot@example.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email already sent')


class RestorePasswordTest(AccountTestBase):
    """Test the restore password flow (using the reset token)."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='restore@example.com', password='oldpass'
        )
        self.user.restore_password_token = 'valid-token-123'
        self.user.save()

    def test_restore_password_page_get_with_token(self):
        """GET /restore-password/?token=... shows the form."""
        response = self.client.get(reverse('restore-password'), {'token': 'valid-token-123'})
        self.assertEqual(response.status_code, 200)

    def test_restore_password_get_no_token_unauthenticated(self):
        """GET /restore-password/ without token redirects unauthenticated users."""
        response = self.client.get(reverse('restore-password'))
        self.assertEqual(response.status_code, 302)

    def test_restore_password_success(self):
        """Submitting valid token and matching passwords resets the password."""
        response = self.client.post(reverse('restore-password'), {
            'token': 'valid-token-123',
            'password': 'newpass1234',
            'confirm_password': 'newpass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass1234'))

    def test_restore_password_mismatch(self):
        """Password mismatch shows error."""
        response = self.client.post(reverse('restore-password'), {
            'token': 'valid-token-123',
            'password': 'newpass1234',
            'confirm_password': 'different9876',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Passwords do not match')

    def test_restore_password_invalid_token(self):
        """Invalid token shows error."""
        response = self.client.post(reverse('restore-password'), {
            'token': 'invalid-token',
            'password': 'newpass1234',
            'confirm_password': 'newpass1234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid restore token')

    def test_restore_password_weak(self):
        """Short password shows weak password error."""
        response = self.client.post(reverse('restore-password'), {
            'token': 'valid-token-123',
            'password': 'ab',
            'confirm_password': 'ab',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Password is too weak')


class EmailVerificationTest(AccountTestBase):
    """Test the email verification flow at /verify/."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='verify@example.com', password='pass1234'
        )
        self.user.verification_code = '123456'
        self.user.is_confirm = False
        self.user.save()

    def test_verify_page_get_unverified_user(self):
        """GET /verify/ for an unverified logged-in user shows the form."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('verify'))
        self.assertEqual(response.status_code, 200)

    def test_verify_page_redirects_verified_user(self):
        """Already verified user is redirected to account."""
        self.user.is_confirm = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse('verify'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account'), fetch_redirect_response=False)

    def test_verify_page_redirects_anonymous(self):
        """Anonymous user visiting /verify/ is redirected to index."""
        response = self.client.get(reverse('verify'))
        self.assertEqual(response.status_code, 302)

    def test_verify_correct_code(self):
        """Submitting the correct verification code confirms the user."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('verify'), {'code': '123456'})
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_confirm)

    def test_verify_wrong_code(self):
        """Submitting a wrong code shows error."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('verify'), {'code': '000000'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid verification code')

    @mock.patch('app.utils.Utils.send_email', return_value=1)
    def test_resend_verification(self, mock_email):
        """POST to resend-verification sends a new code."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('resend-verification'))
        self.assertEqual(response.status_code, 200)
        mock_email.assert_called_once()


class AccountPageTest(AccountTestBase):
    """Test the account page at /account/."""

    def test_account_requires_login(self):
        """Unauthenticated user is redirected to login."""
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)

    def test_account_requires_verification(self):
        """Unverified user is redirected to verify page."""
        user = CustomUser.objects.create_user(email='unverified@example.com', password='pass1234')
        user.is_confirm = False
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('verify'), fetch_redirect_response=False)

    def test_account_accessible_when_verified(self):
        """Verified, logged-in user can access /account/."""
        user = CustomUser.objects.create_user(email='verified@example.com', password='pass1234')
        user.is_confirm = True
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)


class DeleteAccountTest(AccountTestBase):
    """Test account deletion at /delete-account/."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='deleteme@example.com', password='pass1234'
        )

    def test_delete_account_requires_login(self):
        """Unauthenticated user is redirected."""
        response = self.client.get(reverse('delete'))
        self.assertEqual(response.status_code, 302)

    def test_delete_account_get(self):
        """Authenticated user sees deletion confirmation page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('delete'))
        self.assertEqual(response.status_code, 200)

    def test_delete_account_post(self):
        """POST to /delete-account/ deletes the user and logs out."""
        self.client.force_login(self.user)
        user_id = self.user.id
        response = self.client.post(reverse('delete'))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(CustomUser.objects.filter(id=user_id).exists())


class CancelSubscriptionTest(AccountTestBase):
    """Test subscription cancellation."""

    def setUp(self):
        super().setUp()
        self.user = CustomUser.objects.create_user(
            email='subscriber@example.com', password='pass1234'
        )
        self.user.is_plan_active = True
        self.user.processor = 'stripe'
        self.user.payment_nonce = 'cus_test'
        self.user.card_nonce = 'card_test'
        self.user.next_billing_date = timezone.now() + timezone.timedelta(days=30)
        self.user.save()

    def test_cancel_subscription_page(self):
        """GET /cancel/ shows the cancellation page."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('cancel'))
        self.assertEqual(response.status_code, 200)

    def test_cancel_subscription_post(self):
        """POST to /cancel/ cancels the subscription and redirects."""
        self.client.force_login(self.user)
        response = self.client.post(reverse('cancel'))
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_plan_active)
        self.assertIsNone(self.user.processor)
        self.assertIsNone(self.user.card_nonce)

    def test_cancel_subscription_api(self):
        """POST to the API cancel-subscription endpoint returns success."""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('cancel-subscription'),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_plan_active)


class CustomUserModelTest(AccountTestBase):
    """Unit tests for CustomUser model methods."""

    def test_create_user(self):
        """create_user sets email and password hash."""
        user = CustomUser.objects.create_user(email='model@test.com', password='pass1234')
        self.assertEqual(user.email, 'model@test.com')
        self.assertTrue(user.check_password('pass1234'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        """create_superuser sets is_staff and is_superuser."""
        user = CustomUser.objects.create_superuser(email='admin@test.com', password='admin1234')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_create_user_no_email_raises(self):
        """create_user without email raises ValueError."""
        with self.assertRaises(ValueError):
            CustomUser.objects.create_user(email='', password='pass1234')

    def test_consume_credits(self):
        """consume_credits decrements by 1 and floors at 0."""
        user = CustomUser.objects.create_user(email='credits@test.com', password='pass1234')
        user.credits = 5
        user.save()

        CustomUser.consume_credits(user)
        user.refresh_from_db()
        self.assertEqual(user.credits, 4)

        # Consume down to 0
        user.credits = 0
        user.save()
        CustomUser.consume_credits(user)
        user.refresh_from_db()
        self.assertEqual(user.credits, 0)

    def test_consume_credits_unauthenticated(self):
        """consume_credits returns None for unauthenticated user."""
        result = CustomUser.consume_credits(user=None)
        self.assertIsNone(result)

    def test_check_plan_active(self):
        """check_plan returns True when plan is active."""
        user = CustomUser.objects.create_user(email='plan@test.com', password='pass1234')
        user.is_plan_active = True
        self.assertTrue(user.check_plan)

    def test_check_plan_inactive(self):
        """check_plan returns falsy when plan is not active."""
        user = CustomUser.objects.create_user(email='plan@test.com', password='pass1234')
        user.is_plan_active = False
        self.assertFalse(user.check_plan)

    def test_uuid_auto_generated(self):
        """User gets a uuid and api_token on creation."""
        user = CustomUser.objects.create_user(email='uuid@test.com', password='pass1234')
        self.assertIsNotNone(user.uuid)
        self.assertTrue(len(user.uuid) > 0)
        self.assertIsNotNone(user.api_token)

    def test_str_returns_email(self):
        """User string representation is the email."""
        user = CustomUser.objects.create_user(email='str@test.com', password='pass1234')
        self.assertEqual(str(user), 'str@test.com')

    def test_update_password(self):
        """update_password changes the password when inputs are valid."""
        user = CustomUser.objects.create_user(email='pwd@test.com', password='oldpass')
        i18n = Translation.get_text_by_lang('en')

        # Mock is_authenticated for the staticmethod path
        user.is_authenticated = True
        result, msg = CustomUser.update_password(user, {
            'password': 'oldpass',
            'new_password': 'newpass1234',
            'confirm_password': 'newpass1234',
        }, {'i18n': i18n})

        self.assertIsNotNone(result)
        user.refresh_from_db()
        self.assertTrue(user.check_password('newpass1234'))

    def test_update_password_wrong_current(self):
        """update_password rejects wrong current password."""
        user = CustomUser.objects.create_user(email='pwd2@test.com', password='oldpass')
        i18n = Translation.get_text_by_lang('en')
        user.is_authenticated = True

        result, errors = CustomUser.update_password(user, {
            'password': 'wrongcurrent',
            'new_password': 'newpass1234',
            'confirm_password': 'newpass1234',
        }, {'i18n': i18n})

        self.assertIsNone(result)
        self.assertIn('Wrong current password', errors)


class EmailAddressModelTest(AccountTestBase):
    """Unit tests for EmailAddress model."""

    def test_register_email(self):
        """register_email creates an EmailAddress record."""
        user = CustomUser.objects.create_user(email='main@test.com', password='pass1234')
        user.is_authenticated = True
        i18n = Translation.get_text_by_lang('en')

        email_addr, msg = EmailAddress.register_email(user, {
            'email': 'secondary@test.com'
        }, {'i18n': i18n})

        self.assertIsNotNone(email_addr)
        self.assertEqual(email_addr.email, 'secondary@test.com')
        self.assertEqual(email_addr.account, user)

    def test_register_duplicate_email(self):
        """register_email rejects duplicate email for same user."""
        user = CustomUser.objects.create_user(email='main@test.com', password='pass1234')
        user.is_authenticated = True
        i18n = Translation.get_text_by_lang('en')

        EmailAddress.objects.create(account=user, email='dup@test.com')
        result, msg = EmailAddress.register_email(user, {
            'email': 'dup@test.com'
        }, {'i18n': i18n})

        self.assertIsNone(result)


class AccountTypeModelTest(AccountTestBase):
    """Unit tests for AccountType model."""

    def test_account_type_code_name_slugified(self):
        """AccountType.save generates a slugified code_name."""
        from accounts.models import AccountType
        acct_type = AccountType.objects.create(name='Premium Plan')
        self.assertEqual(acct_type.code_name, 'premium_plan')

    def test_account_type_str(self):
        """AccountType string representation is the name."""
        from accounts.models import AccountType
        acct_type = AccountType.objects.create(name='Basic')
        self.assertEqual(str(acct_type), 'Basic')
