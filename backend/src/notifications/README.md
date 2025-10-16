# LifePal Notifications System

This module provides push notification functionality with support for scheduled notifications and snooze capabilities.

## Features

- **Push Notifications**: Web push notifications using VAPID
- **Scheduled Notifications**: Schedule notifications for future delivery
- **Snooze Support**: Users can snooze notifications with customizable duration
- **Recurring Notifications**: Support for recurring notification schedules
- **Action Buttons**: Notifications can include action buttons (e.g., Snooze)

## Testing Push Notifications from Backend

### 1. Using Django Management Command

Send a test notification to a specific user:

```bash
# Basic usage
python manage.py send_test_notification <username>

# With custom message
python manage.py send_test_notification john --title "Hello" --message "This is a test!"

# With custom URL
python manage.py send_test_notification john --url "/chat" --message "Check your chat"
```

### 2. Using Python Shell

```python
from django.contrib.auth import get_user_model
from notifications.api import send_push_notification_to_user

User = get_user_model()
user = User.objects.get(username='john')

# Simple notification
send_push_notification_to_user(
    user=user,
    title="Test Notification",
    body="This is a test from the backend!"
)

# Notification with actions
send_push_notification_to_user(
    user=user,
    title="Meeting Reminder",
    body="Your meeting starts in 10 minutes",
    url="/calendar",
    actions=[
        {"action": "snooze", "title": "Snooze 10min"}
    ],
    data={"notificationId": "some-id"}
)
```

### 3. Using Celery Task

```python
from notifications.tasks import send_evening_wrapup_notification

# Schedule an evening wrap-up notification
send_evening_wrapup_notification.delay(
    user_id=user.id,
    scheduled_time_str="2025-10-03T21:00:00Z"
)
```

## Scheduled Notifications API

### Create a Scheduled Notification

```bash
POST /api/notifications/scheduled
```

**Request Body:**
```json
{
  "notification_type": "evening_wrapup",
  "title": "Time for your evening wrap-up! 🌙",
  "body": "Do you want to catch up with LifePal?",
  "scheduled_time": "2025-10-03T21:00:00Z",
  "url": "/chat?session=evening_wrapup",
  "tag": "evening-wrapup",
  "snooze_duration_minutes": 30,
  "max_snooze_count": 3,
  "metadata": {
    "session_type": "evening_wrapup",
    "auto_start": true
  }
}
```

### List Scheduled Notifications

```bash
GET /api/notifications/scheduled
GET /api/notifications/scheduled?status=pending
```

### Snooze a Notification

```bash
POST /api/notifications/scheduled/{notification_id}/snooze
```

**Request Body:**
```json
{
  "duration_minutes": 30
}
```

### Cancel a Notification

```bash
DELETE /api/notifications/scheduled/{notification_id}
```

## Example Use Case: Evening Wrap-up Session

Here's how to implement the evening wrap-up notification with snooze:

### 1. Create the Scheduled Notification

```python
from django.utils import timezone
from datetime import timedelta
from notifications.models import ScheduledNotification

# Schedule for 9 PM today
scheduled_time = timezone.now().replace(hour=21, minute=0, second=0, microsecond=0)

notification = ScheduledNotification.objects.create(
    user=user,
    notification_type='evening_wrapup',
    title='Time for your evening wrap-up! 🌙',
    body='Do you want to catch up with LifePal?',
    scheduled_time=scheduled_time,
    url='/chat?session=evening_wrapup',
    tag='evening-wrapup',
    snooze_duration_minutes=30,
    max_snooze_count=3,
    metadata={
        'session_type': 'evening_wrapup',
        'auto_start': True
    }
)
```

### 2. The Notification Will:

1. **Appear at 9 PM** with a "Snooze 30min" button
2. **Open chat window** when clicked, with the URL parameter `session=evening_wrapup`
3. **Allow snoozing** up to 3 times (configurable)
4. **Automatically reschedule** when snoozed (handled by service worker)

### 3. Frontend Integration

The service worker (`/public/sw.js`) automatically handles:
- Displaying the notification with action buttons
- Calling the snooze API when the snooze button is clicked
- Opening the correct URL when the notification body is clicked

## Running the Notification Processor

The scheduled notifications are processed by a Celery beat task that runs every minute.

### Start Celery Worker

```bash
cd backend/src
celery -A core worker -l info
```

### Start Celery Beat (Scheduler)

```bash
cd backend/src
celery -A core beat -l info
```

Or run both together:

```bash
cd backend/src
celery -A core worker -B -l info
```

## Notification Types

- `daily_checkin`: Daily check-in reminders
- `evening_wrapup`: Evening wrap-up sessions
- `reminder`: General reminders
- `custom`: Custom notifications

## Database Models

### PushSubscription
Stores user's push notification subscriptions (browser endpoints).

### ScheduledNotification
Stores scheduled notifications with:
- Scheduling information
- Snooze settings
- Recurring rules
- Metadata for context

## Admin Interface

Both models are registered in Django admin for easy management:
- View all subscriptions and scheduled notifications
- Manually create/edit scheduled notifications
- Cancel or reschedule notifications
- View snooze history

## Migration

Don't forget to create and run migrations:

```bash
python manage.py makemigrations notifications
python manage.py migrate
```
