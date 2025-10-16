"""
Utility functions for file management in tools.
"""
from django.core.files import File
from django.conf import settings
from pathlib import Path
import mimetypes
import uuid
from datetime import timedelta
from django.utils import timezone

from .models import UserFile, StorageQuota


class ToolFileHelper:
    """
    Helper class for tools to save files easily.
    
    Usage in tool scripts:
        from files.utils import ToolFileHelper
        
        helper = ToolFileHelper(user, tool_name='my_tool', tool_execution_id=execution_id)
        file_record = helper.save_file(
            file_path='/path/to/file.pdf',
            original_filename='report.pdf',
            category='pdf',
            description='Generated report'
        )
    """
    
    def __init__(self, user, tool_name=None, tool_execution_id=None):
        self.user = user
        self.tool_name = tool_name
        self.tool_execution_id = tool_execution_id
        self.quota, _ = StorageQuota.objects.get_or_create(user=user)
    
    def check_quota(self, file_size):
        """Check if user has enough storage quota"""
        if self.quota.used_storage + file_size > self.quota.total_quota:
            raise Exception(f"Storage quota exceeded. Available: {self.quota.available_storage} bytes, Required: {file_size} bytes")
        
        if self.quota.file_count >= self.quota.max_files:
            raise Exception(f"Maximum file count reached ({self.quota.max_files})")
        
        return True
    
    def save_file(
        self,
        file_path,
        original_filename=None,
        category='other',
        description='',
        metadata=None,
        is_temporary=False,
        expires_in_hours=None,
        conversation_id=None,
        checkin_id=None
    ):
        """
        Save a file to user's storage.
        
        Args:
            file_path: Path to the file to save
            original_filename: Original filename (defaults to basename of file_path)
            category: File category
            description: File description
            metadata: Additional metadata dict
            is_temporary: Whether file should be auto-deleted
            expires_in_hours: Hours until expiration (for temporary files)
            conversation_id: Associated conversation UUID
            checkin_id: Associated check-in UUID
            
        Returns:
            UserFile instance
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file info
        file_size = file_path.stat().st_size
        mime_type = mimetypes.guess_type(str(file_path))[0] or 'application/octet-stream'
        
        if not original_filename:
            original_filename = file_path.name
        
        # Check quota
        self.check_quota(file_size)
        
        # Calculate expiration
        expires_at = None
        if is_temporary and expires_in_hours:
            expires_at = timezone.now() + timedelta(hours=expires_in_hours)
        elif is_temporary:
            expires_at = timezone.now() + timedelta(hours=24)  # Default 24h
        
        # Create UserFile record
        with open(file_path, 'rb') as f:
            user_file = UserFile.objects.create(
                user=self.user,
                file=File(f, name=file_path.name),
                original_filename=original_filename,
                file_size=file_size,
                mime_type=mime_type,
                category=category,
                source='tool_generated',
                tool_name=self.tool_name,
                tool_execution_id=self.tool_execution_id,
                description=description,
                metadata=metadata or {},
                is_temporary=is_temporary,
                expires_at=expires_at,
                conversation_id=conversation_id,
                checkin_id=checkin_id,
                is_processed=True
            )
        
        # Update quota
        self.quota.used_storage += file_size
        self.quota.file_count += 1
        self.quota.save()
        
        return user_file
    
    def save_from_bytes(
        self,
        content,
        filename,
        category='other',
        mime_type='application/octet-stream',
        description='',
        metadata=None,
        is_temporary=False,
        expires_in_hours=None
    ):
        """
        Save file from bytes content.
        
        Args:
            content: File content as bytes
            filename: Filename to save as
            category: File category
            mime_type: MIME type
            description: File description
            metadata: Additional metadata
            is_temporary: Whether file should be auto-deleted
            expires_in_hours: Hours until expiration
            
        Returns:
            UserFile instance
        """
        # Create temp file
        temp_dir = Path(settings.MEDIA_ROOT) / 'temp' / str(self.user.id)
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        temp_path = temp_dir / f"{uuid.uuid4()}_{filename}"
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        try:
            # Save using save_file
            user_file = self.save_file(
                file_path=temp_path,
                original_filename=filename,
                category=category,
                description=description,
                metadata=metadata,
                is_temporary=is_temporary,
                expires_in_hours=expires_in_hours
            )
            
            return user_file
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    def get_user_files(self, category=None, limit=10):
        """Get user's files, optionally filtered by category"""
        files = UserFile.objects.filter(user=self.user)
        
        if category:
            files = files.filter(category=category)
        
        return files.order_by('-created_at')[:limit]


def create_temp_directory(user_id):
    """Create temporary directory for user"""
    temp_dir = Path(settings.MEDIA_ROOT) / 'temp' / str(user_id)
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def get_file_category_from_mime(mime_type):
    """Determine file category from MIME type"""
    if mime_type.startswith('image/'):
        return 'image'
    elif mime_type.startswith('audio/'):
        return 'audio'
    elif mime_type.startswith('video/'):
        return 'video'
    elif mime_type == 'application/pdf':
        return 'pdf'
    elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
        return 'document'
    else:
        return 'other'
