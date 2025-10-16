"""
Schemas for file management API.
"""
from ninja import Schema
from typing import Optional, List
from datetime import datetime


class FileUploadResponse(Schema):
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    category: str
    file_url: str
    download_url: str
    created_at: datetime


class FileSchema(Schema):
    id: str
    original_filename: str
    file_size: int
    mime_type: str
    category: str
    source: str
    tool_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    metadata: dict = {}
    is_temporary: bool
    is_processed: bool
    file_url: str
    download_url: str
    created_at: datetime
    updated_at: datetime


class FileListResponse(Schema):
    files: List[FileSchema]
    total_count: int
    used_storage: int
    total_quota: int
    usage_percentage: float


class FileUpdateSchema(Schema):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None


class FileShareSchema(Schema):
    file_id: str
    is_public: bool = False
    shared_with_user_id: Optional[str] = None
    max_downloads: Optional[int] = None
    expires_in_hours: Optional[int] = None


class FileShareResponse(Schema):
    id: str
    share_token: str
    share_url: str
    is_public: bool
    download_count: int
    max_downloads: Optional[int] = None
    expires_at: Optional[datetime] = None
    created_at: datetime


class StorageQuotaSchema(Schema):
    total_quota: int
    used_storage: int
    available_storage: int
    usage_percentage: float
    file_count: int
    max_files: int
