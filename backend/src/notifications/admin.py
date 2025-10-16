from django.contrib import admin
from .models import PushSubscription, ScheduledNotification


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint_preview', 'is_active', 'created_at', 'last_used')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'endpoint')
    readonly_fields = ('id', 'created_at', 'last_used')
    
    def endpoint_preview(self, obj):
        return f"{obj.endpoint[:50]}..." if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_preview.short_description = 'Endpoint'


@admin.register(ScheduledNotification)
class ScheduledNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'scheduled_time', 'status', 'snooze_count', 'created_at')
    list_filter = ('status', 'notification_type', 'is_recurring', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'body')
    readonly_fields = ('id', 'created_at', 'updated_at', 'sent_at', 'original_scheduled_time')
    
    fieldsets = (
        ('User & Type', {
            'fields': ('user', 'notification_type')
        }),
        ('Content', {
            'fields': ('title', 'body', 'icon', 'url', 'tag')
        }),
        ('Scheduling', {
            'fields': ('scheduled_time', 'status', 'is_recurring', 'recurrence_rule')
        }),
        ('Snooze Settings', {
            'fields': ('snooze_duration_minutes', 'snooze_count', 'max_snooze_count', 'original_scheduled_time')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_cancelled', 'mark_as_pending']
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} notification(s) marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as cancelled'
    
    def mark_as_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} notification(s) marked as pending.')
    mark_as_pending.short_description = 'Mark selected as pending'
