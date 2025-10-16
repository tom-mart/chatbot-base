from celery import shared_task
from django.utils import timezone
from django.contrib.auth import get_user_model
import logging

from .models import ScheduledNotification
from .api import send_push_notification_to_user

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def process_scheduled_notifications():
    """
    Process all pending scheduled notifications that are due.
    This task should be run periodically (e.g., every minute).
    """
    now = timezone.now()
    
    # Get all pending/snoozed notifications that are due
    notifications = ScheduledNotification.objects.filter(
        status__in=['pending', 'snoozed'],
        scheduled_time__lte=now
    ).select_related('user')
    
    sent_count = 0
    failed_count = 0
    
    for notification in notifications:
        try:
            # Prepare notification actions (snooze button)
            actions = []
            if notification.snooze_count < notification.max_snooze_count:
                actions.append({
                    "action": "snooze",
                    "title": f"Snooze {notification.snooze_duration_minutes}min"
                })
            
            # Add notification ID to data for handling snooze
            notification_data = {
                "notificationId": str(notification.id),
                "notificationType": notification.notification_type,
                **(notification.metadata or {})
            }
            
            # Send the notification
            success = send_push_notification_to_user(
                user=notification.user,
                title=notification.title,
                body=notification.body,
                icon=notification.icon,
                url=notification.url,
                tag=notification.tag or f"scheduled-{notification.id}",
                actions=actions if actions else None,
                data=notification_data
            )
            
            if success:
                notification.mark_sent()
                sent_count += 1
                logger.info(f"Sent scheduled notification {notification.id} to {notification.user.username}")
            else:
                notification.status = 'failed'
                notification.save()
                failed_count += 1
                logger.error(f"Failed to send notification {notification.id} to {notification.user.username}")
                
        except Exception as e:
            notification.status = 'failed'
            notification.save()
            failed_count += 1
            logger.error(f"Error processing notification {notification.id}: {str(e)}", exc_info=True)
    
    logger.info(f"Processed scheduled notifications: {sent_count} sent, {failed_count} failed")
    return {"sent": sent_count, "failed": failed_count}


@shared_task
def send_evening_wrapup_notification(user_id, scheduled_time_str=None):
    """
    Send an evening wrap-up notification to a specific user.
    
    Args:
        user_id: User ID
        scheduled_time_str: ISO format datetime string for when to send
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Parse scheduled time or use now
        if scheduled_time_str:
            from dateutil import parser
            scheduled_time = parser.isoparse(scheduled_time_str)
        else:
            scheduled_time = timezone.now()
        
        # Create scheduled notification
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
        
        logger.info(f"Created evening wrap-up notification for {user.username} at {scheduled_time}")
        return str(notification.id)
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return None
    except Exception as e:
        logger.error(f"Error creating evening wrap-up notification: {str(e)}", exc_info=True)
        return None


@shared_task
def create_recurring_notifications():
    """
    Process recurring notifications and create new instances.
    This should run daily to create notifications for recurring schedules.
    """
    # Get all recurring notifications
    recurring = ScheduledNotification.objects.filter(
        is_recurring=True,
        status='sent'
    )
    
    created_count = 0
    
    for notification in recurring:
        if notification.recurrence_rule:
            # TODO: Implement iCal RRULE parsing
            # For now, we'll skip this - can be implemented later with python-dateutil
            logger.info(f"Skipping recurring notification {notification.id} - RRULE parsing not yet implemented")
            continue
    
    logger.info(f"Created {created_count} recurring notification instances")
    return created_count
