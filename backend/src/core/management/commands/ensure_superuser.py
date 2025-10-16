from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Create superuser if it does not exist'

    def handle(self, *args, **options):
        # Require these values to be provided via environment variables.
        # Do NOT include defaults with secrets in code or repo.
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not email or not password:
            self.stdout.write(
                self.style.ERROR('Missing DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL or DJANGO_SUPERUSER_PASSWORD environment variables')
            )
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'Superuser "{username}" already exists')
            )
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Superuser "{username}" created successfully')
        )
