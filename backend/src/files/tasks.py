"""
Celery tasks for file management.
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_files():
    """
    Delete expired temporary files.
    Run this task periodically (e.g., every hour).
    """
    from .models import UserFile, StorageQuota
    
    now = timezone.now()
    
    # Find expired files
    expired_files = UserFile.objects.filter(
        is_temporary=True,
        expires_at__lte=now
    )
    
    deleted_count = 0
    freed_space = 0
    
    for file in expired_files:
        user = file.user
        file_size = file.file_size
        
        # Delete file
        file.delete()
        
        # Update quota
        try:
            quota = user.storage_quota
            quota.used_storage = max(0, quota.used_storage - file_size)
            quota.file_count = max(0, quota.file_count - 1)
            quota.save()
        except StorageQuota.DoesNotExist:
            pass
        
        deleted_count += 1
        freed_space += file_size
    
    logger.info(f"Cleaned up {deleted_count} expired files, freed {freed_space} bytes")
    return {"deleted": deleted_count, "freed_space": freed_space}


@shared_task
def cleanup_old_temporary_files():
    """
    Delete temporary files older than 24 hours without explicit expiration.
    """
    from .models import UserFile, StorageQuota
    
    cutoff_time = timezone.now() - timedelta(hours=24)
    
    old_temp_files = UserFile.objects.filter(
        is_temporary=True,
        expires_at__isnull=True,
        created_at__lte=cutoff_time
    )
    
    deleted_count = 0
    freed_space = 0
    
    for file in old_temp_files:
        user = file.user
        file_size = file.file_size
        
        file.delete()
        
        try:
            quota = user.storage_quota
            quota.used_storage = max(0, quota.used_storage - file_size)
            quota.file_count = max(0, quota.file_count - 1)
            quota.save()
        except StorageQuota.DoesNotExist:
            pass
        
        deleted_count += 1
        freed_space += file_size
    
    logger.info(f"Cleaned up {deleted_count} old temporary files, freed {freed_space} bytes")
    return {"deleted": deleted_count, "freed_space": freed_space}


@shared_task
def recalculate_all_storage_quotas():
    """
    Recalculate storage usage for all users.
    Run this periodically (e.g., daily) to ensure accuracy.
    """
    from .models import StorageQuota
    
    quotas = StorageQuota.objects.all()
    updated_count = 0
    
    for quota in quotas:
        quota.recalculate_usage()
        updated_count += 1
    
    logger.info(f"Recalculated storage quotas for {updated_count} users")
    return {"updated": updated_count}


@shared_task
def cleanup_expired_shares():
    """
    Delete expired file shares.
    """
    from .models import FileShare
    from django.db.models import F
    
    now = timezone.now()
    
    # Find expired shares
    expired_shares = FileShare.objects.filter(expires_at__lte=now)
    deleted_count = expired_shares.count()
    expired_shares.delete()
    
    # Find shares that exceeded max downloads
    maxed_shares = FileShare.objects.filter(
        max_downloads__isnull=False
    ).filter(
        download_count__gte=F('max_downloads')
    )
    maxed_count = maxed_shares.count()
    maxed_shares.delete()
    
    total_deleted = deleted_count + maxed_count
    logger.info(f"Cleaned up {total_deleted} expired file shares")
    return {"deleted": total_deleted}
