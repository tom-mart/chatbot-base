from ninja import Router
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.conf import settings
from typing import List
import os
import json
import logging
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)

from .models import PushSubscription, ScheduledNotification
from .schemas import (
    PushSubscriptionSchema,
    PushSubscriptionResponseSchema,
    SendPushNotificationSchema,
    VAPIDPublicKeySchema,
    TestNotificationSchema,
    CreateScheduledNotificationSchema,
    UpdateScheduledNotificationSchema,
    ScheduledNotificationResponseSchema,
    SnoozeNotificationSchema
)

router = Router()


@router.get("/vapid-public-key", auth=JWTAuth(), response=VAPIDPublicKeySchema, tags=["Push Notifications"])
def get_vapid_public_key(request):
    """Get VAPID public key for push notification subscription"""
    public_key = os.environ.get('VAPID_PUBLIC_KEY', '')
    if not public_key:
        return 500, {"error": "VAPID keys not configured"}
    return {"public_key": public_key}


@router.post("/subscribe", auth=JWTAuth(), response={201: PushSubscriptionResponseSchema, 400: dict}, tags=["Push Notifications"])
def subscribe_to_push(request, payload: PushSubscriptionSchema):
    """Subscribe user to push notifications"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("🔔 PUSH NOTIFICATION SUBSCRIPTION REQUEST RECEIVED")
    logger.info("=" * 80)
    
    try:
        # Extract keys from the subscription
        p256dh = payload.keys.get('p256dh')
        auth = payload.keys.get('auth')
        
        logger.info(f"User: {request.user.username} (ID: {request.user.id})")
        logger.info(f"Endpoint: {payload.endpoint[:80]}...")
        logger.info(f"Keys present - p256dh: {bool(p256dh)}, auth: {bool(auth)}")
        logger.info(f"User agent: {payload.user_agent[:100] if payload.user_agent else 'Not provided'}")
        
        if not p256dh or not auth:
            logger.error("Missing required keys")
            return 400, {"error": "Missing required keys (p256dh, auth)"}
        
        # Deactivate all existing subscriptions for this user
        # This handles the case where PWA cache is cleared and a new subscription is created
        old_subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        ).exclude(endpoint=payload.endpoint)
        
        deactivated_count = old_subscriptions.update(is_active=False)
        if deactivated_count > 0:
            logger.info(f"Deactivated {deactivated_count} old subscription(s) for user {request.user.username}")
        
        # Create or update subscription
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=payload.endpoint,
            defaults={
                'user': request.user,
                'p256dh_key': p256dh,
                'auth_key': auth,
                'user_agent': payload.user_agent,
                'is_active': True
            }
        )
        
        logger.info(f"Subscription {'created' if created else 'updated'} successfully")
        
        return 201, {
            'id': subscription.id,
            'endpoint': subscription.endpoint,
            'created_at': subscription.created_at,
            'is_active': subscription.is_active
        }
    except Exception as e:
        logger.error(f"Subscription error: {str(e)}", exc_info=True)
        return 400, {"error": str(e)}


@router.delete("/unsubscribe", auth=JWTAuth(), response={200: dict, 404: dict}, tags=["Push Notifications"])
def unsubscribe_from_push(request, endpoint: str):
    """Unsubscribe from push notifications"""
    try:
        subscription = PushSubscription.objects.get(
            user=request.user,
            endpoint=endpoint
        )
        subscription.is_active = False
        subscription.save()
        return 200, {"success": True, "message": "Unsubscribed successfully"}
    except PushSubscription.DoesNotExist:
        return 404, {"error": "Subscription not found"}


@router.get("/subscriptions", auth=JWTAuth(), response=List[PushSubscriptionResponseSchema], tags=["Push Notifications"])
def get_user_subscriptions(request):
    """Get all active push subscriptions for the current user"""
    subscriptions = PushSubscription.objects.filter(
        user=request.user,
        is_active=True
    )
    return [
        {
            'id': sub.id,
            'endpoint': sub.endpoint,
            'created_at': sub.created_at,
            'is_active': sub.is_active
        }
        for sub in subscriptions
    ]


@router.post("/test", auth=JWTAuth(), response={200: dict, 400: dict, 500: dict}, tags=["Push Notifications"])
def send_test_notification(request, payload: TestNotificationSchema):
    """Send a test push notification to all user's devices"""
    try:
        vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY')
        vapid_claims = {
            "sub": os.environ.get('VAPID_SUBJECT', 'mailto:admin@lifepal.app')
        }
        
        if not vapid_private_key:
            return 500, {"error": "VAPID keys not configured on server"}
        
        subscriptions = PushSubscription.objects.filter(
            user=request.user,
            is_active=True
        )
        
        if not subscriptions.exists():
            return 400, {"error": "No active push subscriptions found"}
        
        success_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            try:
                notification_data = {
                    "title": "LifePal Test Notification",
                    "body": payload.message,
                    "icon": "/web-app-manifest-192x192.png",
                    "badge": "/favicon-96x96.png",
                    "tag": "test-notification",
                    "url": "/"
                }
                
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh_key,
                            "auth": subscription.auth_key
                        }
                    },
                    data=json.dumps(notification_data),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                    # Add TTL (Time To Live) - notification expires after 12 hours
                    ttl=43200,
                    # Set urgency to 'high' for test notifications
                    headers={
                        "Urgency": "high",
                        "Topic": "test-notification"
                    }
                )
                success_count += 1
                subscription.save()  # Update last_used timestamp
            except WebPushException as e:
                failed_count += 1
                if e.response and e.response.status_code in [404, 410]:
                    # Subscription is no longer valid
                    subscription.is_active = False
                    subscription.save()
        
        return 200, {
            "success": True,
            "message": f"Sent to {success_count} device(s), {failed_count} failed",
            "sent": success_count,
            "failed": failed_count
        }
    except Exception as e:
        return 500, {"error": str(e)}


def send_push_notification_to_user(user, title, body, icon=None, url=None, tag=None, actions=None, data=None):
    """
    Helper function to send push notifications to a user.
    Can be called from other parts of the application.
    
    Args:
        user: User object
        title: Notification title
        body: Notification body
        icon: Icon URL
        url: URL to open when clicked
        tag: Notification tag
        actions: List of action buttons (e.g., [{"action": "snooze", "title": "Snooze 30min"}])
        data: Additional data to pass to the notification
    """
    import sys
    print(f"[PUSH] send_push_notification_to_user called for {user.username}: {title}", file=sys.stderr, flush=True)
    logger.info(f"send_push_notification_to_user called for {user.username}: {title}")
    try:
        vapid_private_key = os.environ.get('VAPID_PRIVATE_KEY')
        vapid_claims = {
            "sub": os.environ.get('VAPID_SUBJECT', 'mailto:admin@lifepal.app')
        }
        
        if not vapid_private_key:
            logger.error("VAPID_PRIVATE_KEY not set!")
            return False
        
        subscriptions = PushSubscription.objects.filter(
            user=user,
            is_active=True
        )
        
        sub_count = subscriptions.count()
        print(f"[PUSH] Found {sub_count} active subscriptions for {user.username}", file=sys.stderr, flush=True)
        logger.info(f"Found {sub_count} active subscriptions for {user.username}")
        
        success = False
        failed_count = 0
        for subscription in subscriptions:
            try:
                notification_data = {
                    "title": title,
                    "body": body,
                    "icon": icon or "/web-app-manifest-192x192.png",
                    "badge": "/favicon-96x96.png",
                    "tag": tag or "notification",
                    "url": url or "/",
                    "requireInteraction": bool(actions),  # Keep notification visible if there are actions
                }
                
                if actions:
                    notification_data["actions"] = actions
                
                if data:
                    notification_data["data"] = data
                
                # Determine urgency based on notification type
                urgency = "high"  # Default to high for scheduled notifications
                ttl = 86400  # 24 hours default TTL - long enough to not miss notifications
                
                # Adjust based on notification type
                if data and data.get('notificationType') == 'reminder':
                    urgency = "high"
                    ttl = 43200  # 12 hours for reminders - important but can wait
                elif data and data.get('notificationType') == 'evening_wrapup':
                    urgency = "normal"
                    ttl = 28800  # 8 hours for wrap-ups - relevant for the evening
                
                webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {
                            "p256dh": subscription.p256dh_key,
                            "auth": subscription.auth_key
                        }
                    },
                    data=json.dumps(notification_data),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims,
                    ttl=ttl,
                    headers={
                        "Urgency": urgency,
                        "Topic": tag or "notification"
                    }
                )
                success = True
                print(f"[PUSH] Successfully sent to {user.username} via subscription {subscription.id}", file=sys.stderr, flush=True)
                logger.info(f"Successfully sent push notification to {user.username} via subscription {subscription.id}")
                subscription.save()
            except WebPushException as e:
                failed_count += 1
                status_code = e.response.status_code if e.response else 'unknown'
                print(f"[PUSH] WebPush error for subscription {subscription.id}: status {status_code}", file=sys.stderr, flush=True)
                if e.response and e.response.status_code in [404, 410]:
                    logger.info(f"Subscription {subscription.id} expired (status {e.response.status_code}), marking inactive")
                    subscription.is_active = False
                    subscription.save()
                else:
                    logger.warning(f"WebPush error for subscription {subscription.id}: {e}")
        
        if not success and failed_count > 0:
            print(f"[PUSH] FAILED: tried {failed_count} subscriptions for {user.username}, none succeeded", file=sys.stderr, flush=True)
            logger.warning(f"Failed to send notification to {user.username}: tried {failed_count} subscriptions, none succeeded")
        
        return success
    except Exception as e:
        logger.error(f"Error in send_push_notification_to_user: {str(e)}", exc_info=True)
        return False


# ============================================================================
# Scheduled Notifications API
# ============================================================================

@router.post("/scheduled", auth=JWTAuth(), response={201: ScheduledNotificationResponseSchema, 400: dict}, tags=["Scheduled Notifications"])
def create_scheduled_notification(request, payload: CreateScheduledNotificationSchema):
    """Create a new scheduled notification"""
    try:
        notification = ScheduledNotification.objects.create(
            user=request.user,
            notification_type=payload.notification_type,
            title=payload.title,
            body=payload.body,
            scheduled_time=payload.scheduled_time,
            icon=payload.icon,
            url=payload.url,
            tag=payload.tag,
            snooze_duration_minutes=payload.snooze_duration_minutes,
            max_snooze_count=payload.max_snooze_count,
            is_recurring=payload.is_recurring,
            recurrence_rule=payload.recurrence_rule,
            metadata=payload.metadata or {}
        )
        
        return 201, notification
    except Exception as e:
        return 400, {"error": str(e)}


@router.get("/scheduled", auth=JWTAuth(), response=List[ScheduledNotificationResponseSchema], tags=["Scheduled Notifications"])
def list_scheduled_notifications(request, status: str = None):
    """List all scheduled notifications for the current user"""
    notifications = ScheduledNotification.objects.filter(user=request.user)
    
    if status:
        notifications = notifications.filter(status=status)
    
    return list(notifications)


@router.get("/scheduled/{notification_id}", auth=JWTAuth(), response={200: ScheduledNotificationResponseSchema, 404: dict}, tags=["Scheduled Notifications"])
def get_scheduled_notification(request, notification_id: str):
    """Get a specific scheduled notification"""
    try:
        notification = ScheduledNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        return 200, notification
    except ScheduledNotification.DoesNotExist:
        return 404, {"error": "Notification not found"}


@router.patch("/scheduled/{notification_id}", auth=JWTAuth(), response={200: ScheduledNotificationResponseSchema, 404: dict, 400: dict}, tags=["Scheduled Notifications"])
def update_scheduled_notification(request, notification_id: str, payload: UpdateScheduledNotificationSchema):
    """Update a scheduled notification"""
    try:
        notification = ScheduledNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        # Only allow updates if notification is pending or snoozed
        if notification.status not in ['pending', 'snoozed']:
            return 400, {"error": "Cannot update notification with status: " + notification.status}
        
        # Update fields
        update_data = payload.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(notification, field, value)
        
        notification.save()
        return 200, notification
    except ScheduledNotification.DoesNotExist:
        return 404, {"error": "Notification not found"}


@router.post("/scheduled/{notification_id}/snooze", auth=JWTAuth(), response={200: ScheduledNotificationResponseSchema, 404: dict, 400: dict}, tags=["Scheduled Notifications"])
def snooze_notification(request, notification_id: str, payload: SnoozeNotificationSchema):
    """Snooze a scheduled notification"""
    try:
        notification = ScheduledNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        
        success = notification.snooze(payload.duration_minutes)
        
        if not success:
            return 400, {"error": "Maximum snooze count reached"}
        
        return 200, notification
    except ScheduledNotification.DoesNotExist:
        return 404, {"error": "Notification not found"}


@router.delete("/scheduled/{notification_id}", auth=JWTAuth(), response={200: dict, 404: dict}, tags=["Scheduled Notifications"])
def cancel_scheduled_notification(request, notification_id: str):
    """Cancel a scheduled notification"""
    try:
        notification = ScheduledNotification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.cancel()
        return 200, {"success": True, "message": "Notification cancelled"}
    except ScheduledNotification.DoesNotExist:
        return 404, {"error": "Notification not found"}
