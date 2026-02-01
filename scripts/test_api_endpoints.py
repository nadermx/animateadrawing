#!/usr/bin/env python3
"""
API Endpoint Test Suite for Animate a Drawing

Tests both animateadrawing.com and api.animateadrawing.com endpoints.

Usage:
    python scripts/test_api_endpoints.py [--live] [--verbose]

Options:
    --live      Test against live production servers (default: localhost)
    --verbose   Show detailed output for each test
"""

import os
import sys
import json
import argparse
import requests
from urllib.parse import urljoin
from io import BytesIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class APITestSuite:
    """Test suite for all API endpoints."""

    def __init__(self, base_url='https://animateadrawing.com',
                 api_url='https://api.animateadrawing.com',
                 verbose=False):
        self.base_url = base_url.rstrip('/')
        self.api_url = api_url.rstrip('/')
        self.verbose = verbose
        self.session = requests.Session()
        self.results = {'passed': 0, 'failed': 0, 'skipped': 0}
        self.test_user_token = None  # Set this for authenticated tests

    def log(self, message, color=None):
        """Print a message with optional color."""
        if color:
            print(f"{color}{message}{Colors.RESET}")
        else:
            print(message)

    def log_result(self, name, passed, message='', expected=None, actual=None):
        """Log a test result."""
        if passed:
            self.results['passed'] += 1
            status = f"{Colors.GREEN}PASS{Colors.RESET}"
        else:
            self.results['failed'] += 1
            status = f"{Colors.RED}FAIL{Colors.RESET}"

        print(f"  [{status}] {name}")
        if self.verbose or not passed:
            if message:
                print(f"         {message}")
            if expected is not None and actual is not None:
                print(f"         Expected: {expected}, Got: {actual}")

    def skip(self, name, reason):
        """Skip a test."""
        self.results['skipped'] += 1
        print(f"  [{Colors.YELLOW}SKIP{Colors.RESET}] {name} - {reason}")

    # =========================================================================
    # Public Page Tests
    # =========================================================================

    def test_public_pages(self):
        """Test all public pages return 200."""
        self.log(f"\n{Colors.BOLD}=== Public Pages ==={Colors.RESET}")

        pages = [
            ('/', 'Homepage'),
            ('/pricing/', 'Pricing'),
            ('/about/', 'About'),
            ('/contact/', 'Contact'),
            ('/faq/', 'FAQ'),
            ('/examples/', 'Examples'),
            ('/how-it-works/', 'How It Works'),
            ('/privacy/', 'Privacy Policy'),
            ('/terms/', 'Terms of Service'),
            ('/api/docs/', 'API Documentation'),
            ('/animator/motion-presets/', 'Motion Presets'),
            ('/animator/backgrounds/', 'Background Library'),
            ('/animator/templates/', 'Character Templates'),
            ('/animator/backgrounds/generate/', 'AI Background Generator'),
        ]

        for path, name in pages:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                passed = response.status_code == 200
                self.log_result(
                    f"{name} ({path})",
                    passed,
                    expected=200,
                    actual=response.status_code
                )
            except Exception as e:
                self.log_result(f"{name} ({path})", False, str(e))

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    def test_auth_pages(self):
        """Test authentication pages."""
        self.log(f"\n{Colors.BOLD}=== Authentication Pages ==={Colors.RESET}")

        pages = [
            ('/login/', 'Login Page', 200),
            ('/signup/', 'Signup Page', 200),
            ('/logout/', 'Logout (redirect)', 302),
        ]

        for path, name, expected_code in pages:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10, allow_redirects=False)
                passed = response.status_code == expected_code
                self.log_result(
                    f"{name} ({path})",
                    passed,
                    expected=expected_code,
                    actual=response.status_code
                )
            except Exception as e:
                self.log_result(f"{name} ({path})", False, str(e))

    # =========================================================================
    # Protected Animator Pages (should redirect to login)
    # =========================================================================

    def test_protected_pages(self):
        """Test protected pages redirect to login."""
        self.log(f"\n{Colors.BOLD}=== Protected Pages (should redirect) ==={Colors.RESET}")

        pages = [
            '/animator/',
            '/animator/projects/',
            '/animator/quick/',
        ]

        for path in pages:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10, allow_redirects=False)
                # Should redirect (302) to login
                passed = response.status_code == 302
                self.log_result(
                    f"Protected: {path}",
                    passed,
                    expected="302 (redirect to login)",
                    actual=response.status_code
                )
            except Exception as e:
                self.log_result(f"Protected: {path}", False, str(e))

    # =========================================================================
    # API Proxy Tests (animateadrawing.com -> api.animateadrawing.com)
    # =========================================================================

    def test_api_proxy(self):
        """Test API proxy forwards requests correctly."""
        self.log(f"\n{Colors.BOLD}=== API Proxy (/api/v1/* -> api.animateadrawing.com) ==={Colors.RESET}")

        # Test /api/v1/animate/ without auth (should get error from backend)
        try:
            url = urljoin(self.base_url, '/api/v1/animate/')
            response = self.session.post(url, timeout=10)
            data = response.json()

            # Should get "NO AUTH HEADER PROVIDED" error from GPU backend
            passed = 'error' in data and 'AUTH' in data.get('error', '').upper()
            self.log_result(
                "POST /api/v1/animate/ (no auth)",
                passed,
                message=f"Response: {data.get('error', data)}"
            )
        except Exception as e:
            self.log_result("POST /api/v1/animate/ (no auth)", False, str(e))

        # Test /api/v1/animate/results/ without UUID
        try:
            url = urljoin(self.base_url, '/api/v1/animate/results/')
            response = self.session.post(url, timeout=10)
            data = response.json()

            # Should get UUID error from GPU backend
            passed = data.get('failed') == True or 'uuid' in str(data).lower()
            self.log_result(
                "POST /api/v1/animate/results/ (no uuid)",
                passed,
                message=f"Response: {data}"
            )
        except Exception as e:
            self.log_result("POST /api/v1/animate/results/ (no uuid)", False, str(e))

    # =========================================================================
    # GPU Backend Direct Tests
    # =========================================================================

    def test_gpu_backend_direct(self):
        """Test GPU backend directly."""
        self.log(f"\n{Colors.BOLD}=== GPU Backend (api.animateadrawing.com) ==={Colors.RESET}")

        # Test /v1/animate/
        try:
            url = f"{self.api_url}/v1/animate/"
            response = self.session.post(url, timeout=10)
            data = response.json()

            passed = 'error' in data
            self.log_result(
                "POST /v1/animate/ (direct)",
                passed,
                message=f"Response: {data.get('error', data)}"
            )
        except Exception as e:
            self.log_result("POST /v1/animate/ (direct)", False, str(e))

        # Test /v1/animate/results/
        try:
            url = f"{self.api_url}/v1/animate/results/"
            response = self.session.post(url, data={'uuid': 'test-invalid-uuid'}, timeout=10)
            data = response.json()

            # Should handle gracefully (not crash)
            passed = isinstance(data, dict)
            self.log_result(
                "POST /v1/animate/results/ (invalid uuid)",
                passed,
                message=f"Response: {data}"
            )
        except Exception as e:
            self.log_result("POST /v1/animate/results/ (invalid uuid)", False, str(e))

    # =========================================================================
    # Internal API Tests
    # =========================================================================

    def test_accounts_api(self):
        """Test accounts API endpoints."""
        self.log(f"\n{Colors.BOLD}=== Accounts API ==={Colors.RESET}")

        # Test APIDeduct without key
        try:
            url = urljoin(self.base_url, '/api/accounts/api/deduct/')
            response = self.session.post(url, json={}, timeout=10)
            data = response.json()

            passed = (
                data.get('authorized') == False and
                data.get('error') == 'No API key provided'
            )
            self.log_result(
                "POST /api/accounts/api/deduct/ (no key)",
                passed,
                message=f"Response: {data}"
            )
        except Exception as e:
            self.log_result("POST /api/accounts/api/deduct/ (no key)", False, str(e))

        # Test APIDeduct with invalid key
        try:
            url = urljoin(self.base_url, '/api/accounts/api/deduct/')
            response = self.session.post(url, json={'key': 'invalid-test-key'}, timeout=10)
            data = response.json()

            passed = (
                data.get('authorized') == False and
                'Invalid' in data.get('error', '')
            )
            self.log_result(
                "POST /api/accounts/api/deduct/ (invalid key)",
                passed,
                message=f"Response: {data}"
            )
        except Exception as e:
            self.log_result("POST /api/accounts/api/deduct/ (invalid key)", False, str(e))

    def test_animator_api_unauthenticated(self):
        """Test animator API endpoints without authentication."""
        self.log(f"\n{Colors.BOLD}=== Animator API (unauthenticated) ==={Colors.RESET}")

        test_uuid = '00000000-0000-0000-0000-000000000000'

        endpoints = [
            ('GET', f'/animator/api/projects/{test_uuid}/data/', 'Project Data'),
            ('POST', f'/animator/api/characters/{test_uuid}/detect/', 'Detect Character'),
            ('POST', f'/animator/api/characters/{test_uuid}/rig/', 'Save Rig'),
            ('GET', f'/animator/api/scenes/{test_uuid}/data/', 'Scene Data'),
            ('POST', f'/animator/api/scenes/{test_uuid}/save/', 'Save Scene'),
            ('POST', '/animator/api/animations/generate/', 'Generate Animation'),
            ('POST', '/animator/api/render/preview/', 'Render Preview'),
            ('GET', f'/animator/api/export/{test_uuid}/status/', 'Export Status'),
        ]

        for method, path, name in endpoints:
            try:
                url = urljoin(self.base_url, path)
                if method == 'GET':
                    response = self.session.get(url, timeout=10, allow_redirects=False)
                else:
                    response = self.session.post(url, json={}, timeout=10, allow_redirects=False)

                # Should redirect to login (302) or return 403
                passed = response.status_code in [302, 403]
                self.log_result(
                    f"{method} {name}",
                    passed,
                    expected="302 or 403 (requires auth)",
                    actual=response.status_code
                )
            except Exception as e:
                self.log_result(f"{method} {name}", False, str(e))

    # =========================================================================
    # Static Files Tests
    # =========================================================================

    def test_static_files(self):
        """Test static files are served correctly."""
        self.log(f"\n{Colors.BOLD}=== Static Files ==={Colors.RESET}")

        files = [
            '/static/css/styles.css',
            '/static/css/design-system.css',
            '/static/favicon.ico',
            '/static/manifest.json',
        ]

        for path in files:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                passed = response.status_code == 200
                self.log_result(
                    f"Static: {path}",
                    passed,
                    expected=200,
                    actual=response.status_code
                )
            except Exception as e:
                self.log_result(f"Static: {path}", False, str(e))

    # =========================================================================
    # SSL/HTTPS Tests
    # =========================================================================

    def test_ssl_redirects(self):
        """Test HTTP to HTTPS redirects."""
        self.log(f"\n{Colors.BOLD}=== SSL/HTTPS Redirects ==={Colors.RESET}")

        if 'localhost' in self.base_url:
            self.skip("HTTP->HTTPS redirect", "Not applicable for localhost")
            return

        # Test main domain
        try:
            http_url = self.base_url.replace('https://', 'http://')
            response = requests.get(http_url, timeout=10, allow_redirects=False)
            passed = response.status_code == 301 and 'https://' in response.headers.get('Location', '')
            self.log_result(
                "HTTP -> HTTPS redirect",
                passed,
                expected="301 to HTTPS",
                actual=f"{response.status_code} -> {response.headers.get('Location', 'N/A')}"
            )
        except Exception as e:
            self.log_result("HTTP -> HTTPS redirect", False, str(e))

        # Test www redirect
        try:
            www_url = self.base_url.replace('://', '://www.')
            response = requests.get(www_url, timeout=10, allow_redirects=False)
            passed = response.status_code == 301
            self.log_result(
                "www -> non-www redirect",
                passed,
                expected="301 redirect",
                actual=response.status_code
            )
        except Exception as e:
            self.log_result("www -> non-www redirect", False, str(e))

    # =========================================================================
    # Run All Tests
    # =========================================================================

    def run_all(self):
        """Run all tests."""
        self.log(f"\n{Colors.BOLD}{Colors.BLUE}API Endpoint Test Suite{Colors.RESET}")
        self.log(f"Base URL: {self.base_url}")
        self.log(f"API URL: {self.api_url}")
        self.log("=" * 60)

        # Run all test categories
        self.test_public_pages()
        self.test_auth_pages()
        self.test_protected_pages()
        self.test_api_proxy()
        self.test_gpu_backend_direct()
        self.test_accounts_api()
        self.test_animator_api_unauthenticated()
        self.test_static_files()
        self.test_ssl_redirects()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        total = self.results['passed'] + self.results['failed'] + self.results['skipped']

        self.log(f"\n{'=' * 60}")
        self.log(f"{Colors.BOLD}Test Summary{Colors.RESET}")
        self.log(f"{'=' * 60}")
        self.log(f"  {Colors.GREEN}Passed:{Colors.RESET}  {self.results['passed']}")
        self.log(f"  {Colors.RED}Failed:{Colors.RESET}  {self.results['failed']}")
        self.log(f"  {Colors.YELLOW}Skipped:{Colors.RESET} {self.results['skipped']}")
        self.log(f"  Total:   {total}")

        if self.results['failed'] == 0:
            self.log(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.RESET}")
        else:
            self.log(f"\n{Colors.RED}{Colors.BOLD}{self.results['failed']} test(s) failed!{Colors.RESET}")

        return self.results['failed'] == 0


def main():
    parser = argparse.ArgumentParser(description='Test API endpoints')
    parser.add_argument('--live', action='store_true',
                        help='Test against live production servers')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed output')
    parser.add_argument('--base-url', default=None,
                        help='Override base URL')
    parser.add_argument('--api-url', default=None,
                        help='Override API URL')

    args = parser.parse_args()

    if args.live or args.base_url:
        base_url = args.base_url or 'https://animateadrawing.com'
        api_url = args.api_url or 'https://api.animateadrawing.com'
    else:
        base_url = 'http://localhost:8000'
        api_url = 'https://api.animateadrawing.com'

    suite = APITestSuite(
        base_url=base_url,
        api_url=api_url,
        verbose=args.verbose
    )

    success = suite.run_all()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
