"""
Django management command to test API endpoints.

Usage:
    python manage.py test_api [--live] [--verbose]
"""

from django.core.management.base import BaseCommand
import subprocess
import sys
import os


class Command(BaseCommand):
    help = 'Run API endpoint tests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--live',
            action='store_true',
            help='Test against live production servers',
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
            'scripts',
            'test_api_endpoints.py'
        )

        cmd = [sys.executable, script_path]
        if options['live']:
            cmd.append('--live')
        if options['verbose']:
            cmd.append('--verbose')

        result = subprocess.run(cmd)
        sys.exit(result.returncode)
