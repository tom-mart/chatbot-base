from django.contrib import admin
from .models import UserFile, FileShare, StorageQuota


@admin.register(UserFile)
class UserFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'user', 'category', 'source', 'file_size', 'created_at']
    list_filter = ['category', 'source', 'is_temporary', 'is_processed']
    search_fields = ['original_filename', 'user__username', 'tool_name']
    readonly_fields = ['id', 'file_size', 'created_at', 'updated_at']
    
    fieldsets = (
        ('File Information', {
            'fields': ('id', 'user', 'file', 'original_filename', 'file_size', 'mime_type', 'category')
        }),
        ('Source', {
            'fields': ('source', 'tool_name', 'tool_execution_id')
        }),
        ('Associations', {
            'fields': ('conversation_id', 'checkin_id')
        }),
        ('Metadata', {
            'fields': ('description', 'tags', 'metadata')
        }),
        ('Status', {
            'fields': ('is_temporary', 'is_processed', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FileShare)
class FileShareAdmin(admin.ModelAdmin):
    list_display = ['file', 'share_token', 'is_public', 'download_count', 'expires_at', 'created_at']
    list_filter = ['is_public']
    search_fields = ['share_token', 'file__original_filename']
    readonly_fields = ['id', 'share_token', 'download_count', 'created_at', 'last_accessed']


@admin.register(StorageQuota)
class StorageQuotaAdmin(admin.ModelAdmin):
    list_display = ['user', 'used_storage', 'total_quota', 'usage_percentage', 'file_count']
    search_fields = ['user__username']
    readonly_fields = ['used_storage', 'file_count', 'last_calculated']
    
    actions = ['recalculate_usage']
    
    def recalculate_usage(self, request, queryset):
        for quota in queryset:
            quota.recalculate_usage()
        self.message_user(request, f"Recalculated usage for {queryset.count()} users")
    recalculate_usage.short_description = "Recalculate storage usage"
