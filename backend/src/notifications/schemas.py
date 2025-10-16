from ninja import Schema
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime


class PushSubscriptionSchema(Schema):
    """Schema for creating a push subscription"""
    endpoint: str
    keys: dict  # Contains p256dh and auth keys
    user_agent: Optional[str] = None


class PushSubscriptionResponseSchema(Schema):
    """Schema for push subscription response"""
    id: UUID
    endpoint: str
    created_at: datetime
    is_active: bool


class SendPushNotificationSchema(Schema):
    """Schema for sending a push notification"""
    title: str
    body: str
    icon: Optional[str] = None
    url: Optional[str] = None
    tag: Optional[str] = None
    requireInteraction: Optional[bool] = False


class VAPIDPublicKeySchema(Schema):
    """Schema for VAPID public key"""
    public_key: str


class TestNotificationSchema(Schema):
    """Schema for test notification"""
    message: Optional[str] = "This is a test notification from LifePal!"


class CreateScheduledNotificationSchema(Schema):
    """Schema for creating a scheduled notification"""
    notification_type: str = 'custom'
    title: str
    body: str
    scheduled_time: datetime
    icon: Optional[str] = None
    url: Optional[str] = '/'
    tag: Optional[str] = None
    snooze_duration_minutes: Optional[int] = 30
    max_snooze_count: Optional[int] = 3
    is_recurring: Optional[bool] = False
    recurrence_rule: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class UpdateScheduledNotificationSchema(Schema):
    """Schema for updating a scheduled notification"""
    title: Optional[str] = None
    body: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    icon: Optional[str] = None
    url: Optional[str] = None
    tag: Optional[str] = None
    snooze_duration_minutes: Optional[int] = None
    max_snooze_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ScheduledNotificationResponseSchema(Schema):
    """Schema for scheduled notification response"""
    id: UUID
    notification_type: str
    title: str
    body: str
    scheduled_time: datetime
    status: str
    icon: Optional[str] = None
    url: str
    tag: Optional[str] = None
    snooze_duration_minutes: int
    snooze_count: int
    max_snooze_count: int
    original_scheduled_time: Optional[datetime] = None
    is_recurring: bool
    recurrence_rule: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime] = None
    metadata: Dict[str, Any]


class SnoozeNotificationSchema(Schema):
    """Schema for snoozing a notification"""
    duration_minutes: Optional[int] = None
