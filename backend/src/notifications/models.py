from django.db import models
from django.utils import timezone
import uuid


class PushSubscription(models.Model):
    """Store push notification subscriptions for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='push_subscriptions')
    
    # Push subscription details
    endpoint = models.TextField(unique=True)
    p256dh_key = models.TextField(help_text="P256DH public key")
    auth_key = models.TextField(help_text="Auth secret")
    
    # Metadata
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Push Subscription'
        verbose_name_plural = 'Push Subscriptions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"Push subscription for {self.user.username} ({self.endpoint[:50]}...)"


class ScheduledNotification(models.Model):
    """Store scheduled notifications with snooze support"""
    
    NOTIFICATION_TYPES = [
        ('daily_checkin', 'Daily Check-in'),
        ('evening_wrapup', 'Evening Wrap-up'),
        ('reminder', 'Reminder'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('snoozed', 'Snoozed'),
        ('cancelled', 'Cancelled'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='scheduled_notifications')
    
    # Notification details
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='custom')
    title = models.CharField(max_length=255)
    body = models.TextField()
    icon = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=500, default='/')
    tag = models.CharField(max_length=100, blank=True, null=True)
    
    # Scheduling
    scheduled_time = models.DateTimeField(help_text="When to send the notification")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Snooze support
    snooze_duration_minutes = models.IntegerField(default=30, help_text="Default snooze duration in minutes")
    snooze_count = models.IntegerField(default=0, help_text="Number of times this notification has been snoozed")
    max_snooze_count = models.IntegerField(default=3, help_text="Maximum number of times this can be snoozed")
    original_scheduled_time = models.DateTimeField(null=True, blank=True, help_text="Original scheduled time before any snoozes")
    
    # Recurring notifications
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=255, blank=True, null=True, help_text="iCal RRULE format")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Additional data for context (e.g., chat session type, etc.)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = 'Scheduled Notification'
        verbose_name_plural = 'Scheduled Notifications'
        indexes = [
            models.Index(fields=['user', 'status', 'scheduled_time']),
            models.Index(fields=['scheduled_time', 'status']),
        ]
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"{self.notification_type} for {self.user.username} at {self.scheduled_time}"
    
    def snooze(self, duration_minutes=None):
        """Snooze this notification"""
        if self.snooze_count >= self.max_snooze_count:
            return False
        
        if not self.original_scheduled_time:
            self.original_scheduled_time = self.scheduled_time
        
        duration = duration_minutes or self.snooze_duration_minutes
        self.scheduled_time = timezone.now() + timezone.timedelta(minutes=duration)
        self.snooze_count += 1
        self.status = 'snoozed'
        self.save()
        return True
    
    def mark_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancel this notification"""
        self.status = 'cancelled'
        self.save()
