"""
File management API endpoints.
"""
from ninja import Router, File, UploadedFile
from ninja_jwt.authentication import JWTAuth
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import mimetypes
import secrets

from .models import UserFile, FileShare, StorageQuota
from .schemas import (
    FileUploadResponse, FileSchema, FileListResponse,
    FileUpdateSchema, FileShareSchema, FileShareResponse,
    StorageQuotaSchema
)

router = Router(tags=['Files'], auth=JWTAuth())


@router.post('/upload', response=FileUploadResponse)
def upload_file(
    request,
    file: UploadedFile = File(...),
    category: str = 'other',
    description: str = ''
):
    """Upload a file"""
    user = request.auth
    
    # Get or create storage quota
    quota, _ = StorageQuota.objects.get_or_create(user=user)
    
    # Check storage quota
    file_size = file.size
    if quota.used_storage + file_size > quota.total_quota:
        return HttpResponse(
            {"error": "Storage quota exceeded"},
            status=400
        )
    
    # Check file count limit
    if quota.file_count >= quota.max_files:
        return HttpResponse(
            {"error": "Maximum file count reached"},
            status=400
        )
    
    # Determine MIME type
    mime_type = file.content_type or mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
    
    # Create file record
    user_file = UserFile.objects.create(
        user=user,
        file=file,
        original_filename=file.name,
        file_size=file_size,
        mime_type=mime_type,
        category=category,
        description=description,
        source='user_upload'
    )
    
    # Update quota
    quota.used_storage += file_size
    quota.file_count += 1
    quota.save()
    
    return {
        'id': str(user_file.id),
        'original_filename': user_file.original_filename,
        'file_size': user_file.file_size,
        'mime_type': user_file.mime_type,
        'category': user_file.category,
        'file_url': user_file.file_url,
        'download_url': user_file.download_url,
        'created_at': user_file.created_at
    }


@router.get('/list', response=FileListResponse)
def list_files(
    request,
    category: str = None,
    source: str = None,
    limit: int = 50,
    offset: int = 0
):
    """List user's files"""
    user = request.auth
    
    # Get quota
    quota, _ = StorageQuota.objects.get_or_create(user=user)
    
    # Build query
    files = UserFile.objects.filter(user=user)
    
    if category:
        files = files.filter(category=category)
    if source:
        files = files.filter(source=source)
    
    total_count = files.count()
    files = files[offset:offset + limit]
    
    return {
        'files': [
            {
                'id': str(f.id),
                'original_filename': f.original_filename,
                'file_size': f.file_size,
                'mime_type': f.mime_type,
                'category': f.category,
                'source': f.source,
                'tool_name': f.tool_name,
                'description': f.description,
                'tags': f.tags,
                'metadata': f.metadata,
                'is_temporary': f.is_temporary,
                'is_processed': f.is_processed,
                'file_url': f.file_url,
                'download_url': f.download_url,
                'created_at': f.created_at,
                'updated_at': f.updated_at
            }
            for f in files
        ],
        'total_count': total_count,
        'used_storage': quota.used_storage,
        'total_quota': quota.total_quota,
        'usage_percentage': quota.usage_percentage
    }


@router.get('/quota', response=StorageQuotaSchema)
def get_storage_quota(request):
    """Get user's storage quota information"""
    user = request.auth
    quota, _ = StorageQuota.objects.get_or_create(user=user)
    
    return {
        'total_quota': quota.total_quota,
        'used_storage': quota.used_storage,
        'available_storage': quota.available_storage,
        'usage_percentage': quota.usage_percentage,
        'file_count': quota.file_count,
        'max_files': quota.max_files
    }


@router.get('/{file_id}', response=FileSchema)
def get_file(request, file_id: str):
    """Get file details"""
    user = request.auth
    file = get_object_or_404(UserFile, id=file_id, user=user)
    
    return {
        'id': str(file.id),
        'original_filename': file.original_filename,
        'file_size': file.file_size,
        'mime_type': file.mime_type,
        'category': file.category,
        'source': file.source,
        'tool_name': file.tool_name,
        'description': file.description,
        'tags': file.tags,
        'metadata': file.metadata,
        'is_temporary': file.is_temporary,
        'is_processed': file.is_processed,
        'file_url': file.file_url,
        'download_url': file.download_url,
        'created_at': file.created_at,
        'updated_at': file.updated_at
    }


@router.get('/{file_id}/download')
def download_file(request, file_id: str):
    """Download a file"""
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    user = request.auth
    file = get_object_or_404(UserFile, id=file_id, user=user)
    
    try:
        # Check if file exists
        if not file.file:
            logger.error(f"File object is None for file_id: {file_id}")
            return HttpResponse(
                {"error": "File not found in storage"},
                status=404
            )
        
        # Get the file path
        file_path = file.file.path
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            logger.error(f"File does not exist on disk: {file_path}")
            return HttpResponse(
                {"error": "File not found on disk"},
                status=404
            )
        
        # Open and return the file
        response = FileResponse(
            file.file.open('rb'),
            content_type=file.mime_type,
            as_attachment=True,
            filename=file.original_filename
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}", exc_info=True)
        return HttpResponse(
            {"error": f"Failed to download file: {str(e)}"},
            status=500
        )


@router.put('/{file_id}', response=FileSchema)
def update_file(request, file_id: str, data: FileUpdateSchema):
    """Update file metadata"""
    user = request.auth
    file = get_object_or_404(UserFile, id=file_id, user=user)
    
    if data.description is not None:
        file.description = data.description
    if data.tags is not None:
        file.tags = data.tags
    if data.category is not None:
        file.category = data.category
    
    file.save()
    
    return {
        'id': str(file.id),
        'original_filename': file.original_filename,
        'file_size': file.file_size,
        'mime_type': file.mime_type,
        'category': file.category,
        'source': file.source,
        'tool_name': file.tool_name,
        'description': file.description,
        'tags': file.tags,
        'metadata': file.metadata,
        'is_temporary': file.is_temporary,
        'is_processed': file.is_processed,
        'file_url': file.file_url,
        'download_url': file.download_url,
        'created_at': file.created_at,
        'updated_at': file.updated_at
    }


@router.delete('/{file_id}')
def delete_file(request, file_id: str):
    """Delete a file"""
    user = request.auth
    file = get_object_or_404(UserFile, id=file_id, user=user)
    
    # Update quota
    quota = user.storage_quota
    quota.used_storage -= file.file_size
    quota.file_count -= 1
    quota.save()
    
    # Delete file
    file.delete()
    
    return {'success': True}


@router.post('/share', response=FileShareResponse)
def create_file_share(request, data: FileShareSchema):
    """Create a shareable link for a file"""
    user = request.auth
    file = get_object_or_404(UserFile, id=data.file_id, user=user)
    
    # Generate share token
    share_token = secrets.token_urlsafe(32)
    
    # Calculate expiration
    expires_at = None
    if data.expires_in_hours:
        expires_at = timezone.now() + timedelta(hours=data.expires_in_hours)
    
    # Create share
    share = FileShare.objects.create(
        file=file,
        share_token=share_token,
        is_public=data.is_public,
        shared_with_id=data.shared_with_user_id,
        max_downloads=data.max_downloads,
        expires_at=expires_at
    )
    
    # Generate share URL
    share_url = f"/api/files/shared/{share_token}"
    
    return {
        'id': str(share.id),
        'share_token': share.share_token,
        'share_url': share_url,
        'is_public': share.is_public,
        'download_count': share.download_count,
        'max_downloads': share.max_downloads,
        'expires_at': share.expires_at,
        'created_at': share.created_at
    }


@router.get('/shared/{share_token}')
def download_shared_file(request, share_token: str):
    """Download a file via share link"""
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    share = get_object_or_404(FileShare, share_token=share_token)
    
    # Check if expired
    if share.is_expired:
        return HttpResponse({"error": "Share link has expired"}, status=410)
    
    # Check permissions
    if not share.is_public:
        # Require authentication
        if not request.auth:
            return HttpResponse({"error": "Authentication required"}, status=401)
        
        # Check if user is the owner or shared_with user
        if share.shared_with and request.auth.id != share.shared_with.id:
            return HttpResponse({"error": "Access denied"}, status=403)
    
    # Increment download count
    share.download_count += 1
    share.last_accessed = timezone.now()
    share.save()
    
    # Serve file
    file = share.file
    
    try:
        # Check if file exists
        if not file.file:
            logger.error(f"File object is None for share_token: {share_token}")
            return HttpResponse(
                {"error": "File not found in storage"},
                status=404
            )
        
        # Get the file path
        file_path = file.file.path
        
        # Check if file exists on disk
        if not os.path.exists(file_path):
            logger.error(f"File does not exist on disk: {file_path}")
            return HttpResponse(
                {"error": "File not found on disk"},
                status=404
            )
        
        # Open and return the file
        response = FileResponse(
            file.file.open('rb'),
            content_type=file.mime_type,
            as_attachment=True,
            filename=file.original_filename
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading shared file {share_token}: {str(e)}", exc_info=True)
        return HttpResponse(
            {"error": f"Failed to download file: {str(e)}"},
            status=500
        )
