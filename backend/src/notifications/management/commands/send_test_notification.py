from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from notifications.api import send_push_notification_to_user

User = get_user_model()


class Command(BaseCommand):
    help = 'Send a test push notification to a user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user to send notification to'
        )
        parser.add_argument(
            '--title',
            type=str,
            default='LifePal Test',
            help='Notification title'
        )
        parser.add_argument(
            '--message',
            type=str,
            default='This is a test notification from the backend!',
            help='Notification message'
        )
        parser.add_argument(
            '--url',
            type=str,
            default='/',
            help='URL to open when notification is clicked'
        )
        parser.add_argument(
            '--tag',
            type=str,
            default='test',
            help='Notification tag'
        )

    def handle(self, *args, **options):
        username = options['username']
        title = options['title']
        message = options['message']
        url = options['url']
        tag = options['tag']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
            return

        self.stdout.write(f'Sending notification to {user.username}...')
        
        success = send_push_notification_to_user(
            user=user,
            title=title,
            body=message,
            url=url,
            tag=tag
        )

        if success:
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully sent notification to {user.username}'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'✗ Failed to send notification. Check VAPID keys and user subscriptions.'
            ))
