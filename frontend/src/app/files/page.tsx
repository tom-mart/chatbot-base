'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/contexts/ToastContext';
import { apiClient } from '@/lib/api';

interface UserFile {
  id: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  category: string;
  source: string;
  tool_name?: string;
  description: string;
  tags: string[];
  metadata: any;
  is_temporary: boolean;
  is_processed: boolean;
  file_url: string;
  download_url: string;
  created_at: string;
  updated_at: string;
}

interface StorageQuota {
  total_quota: number;
  used_storage: number;
  available_storage: number;
  usage_percentage: number;
  file_count: number;
  max_files: number;
}

export default function FilesPage() {
  const { user, loading: authLoading } = useAuth();
  const { showToast } = useToast();
  const router = useRouter();
  const [files, setFiles] = useState<UserFile[]>([]);
  const [quota, setQuota] = useState<StorageQuota | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [editingFile, setEditingFile] = useState<UserFile | null>(null);
  const [editCategory, setEditCategory] = useState<string>('');
  const [editDescription, setEditDescription] = useState<string>('');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadFiles();
      loadQuota();
    }
  }, [user, selectedCategory, selectedSource]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory !== 'all') params.append('category', selectedCategory);
      if (selectedSource !== 'all') params.append('source', selectedSource);
      
      const data = await apiClient.get<{
        files: UserFile[];
        total_count: number;
        used_storage: number;
        total_quota: number;
        usage_percentage: number;
      }>(`/api/files/list?${params.toString()}`);
      
      setFiles(data.files);
    } catch (error: any) {
      console.error('Failed to load files:', error);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const loadQuota = async () => {
    try {
      const data = await apiClient.get<StorageQuota>('/api/files/quota');
      setQuota(data);
    } catch (error: any) {
      console.error('Failed to load quota:', error);
      setQuota({
        total_quota: 1073741824,
        used_storage: 0,
        available_storage: 1073741824,
        usage_percentage: 0,
        file_count: 0,
        max_files: 1000
      });
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', 'other');
      formData.append('description', '');

      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/files/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }
      
      await loadFiles();
      await loadQuota();
      showToast('File uploaded successfully', 'success');
      
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      console.error('Failed to upload file:', error);
      showToast(error.message || 'Failed to upload file', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
      await apiClient.delete(`/api/files/${fileId}`);
      await loadFiles();
      await loadQuota();
      showToast('File deleted successfully', 'success');
    } catch (error: any) {
      console.error('Failed to delete file:', error);
      showToast(error.message || 'Failed to delete file', 'error');
    }
  };

  const handleDownloadFile = async (file: UserFile) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(file.download_url, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Download failed');
      }
      
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = file.original_filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
      showToast('File downloaded successfully', 'success');
    } catch (error: any) {
      console.error('Failed to download file:', error);
      showToast(error.message || 'Failed to download file', 'error');
    }
  };

  const handleEditFile = (file: UserFile) => {
    setEditingFile(file);
    setEditCategory(file.category);
    setEditDescription(file.description || '');
  };

  const handleSaveEdit = async () => {
    if (!editingFile) return;

    try {
      await apiClient.put(`/api/files/${editingFile.id}`, {
        category: editCategory,
        description: editDescription
      });
      
      setEditingFile(null);
      await loadFiles();
      showToast('File updated successfully', 'success');
    } catch (error: any) {
      console.error('Failed to update file:', error);
      showToast(error.message || 'Failed to update file', 'error');
    }
  };

  const handleCancelEdit = () => {
    setEditingFile(null);
    setEditCategory('');
    setEditDescription('');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.startsWith('video/')) return '🎥';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('document') || mimeType.includes('word')) return '📝';
    if (mimeType.includes('spreadsheet') || mimeType.includes('excel')) return '📊';
    return '📎';
  };

  const filteredFiles = files.filter(file => 
    file.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
    file.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base-200">
      {/* Header */}
      <div className="bg-base-100 border-b border-base-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-base-content">My Files</h1>
              <p className="text-base-content/60 mt-1">Manage your uploaded files and documents</p>
            </div>
            <button
              onClick={() => router.push('/home')}
              className="btn btn-ghost btn-sm gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back
            </button>
          </div>

          {/* Storage Quota */}
          {quota && (
            <div className="mt-6 bg-base-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Storage Usage</span>
                <span className="text-sm text-base-content/60">
                  {formatFileSize(quota.used_storage)} / {formatFileSize(quota.total_quota)}
                </span>
              </div>
              <div className="w-full bg-base-300 rounded-full h-2.5">
                <div 
                  className={`h-2.5 rounded-full ${
                    quota.usage_percentage > 90 ? 'bg-error' : 
                    quota.usage_percentage > 70 ? 'bg-warning' : 'bg-primary'
                  }`}
                  style={{ width: `${Math.min(quota.usage_percentage, 100)}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-base-content/60">
                  {quota.file_count} / {quota.max_files} files
                </span>
                <span className="text-xs text-base-content/60">
                  {formatFileSize(quota.available_storage)} available
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          {/* Upload Button */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileUpload}
              className="hidden"
              disabled={uploading}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn btn-primary gap-2"
              disabled={uploading}
            >
              {uploading ? (
                <>
                  <span className="loading loading-spinner loading-sm"></span>
                  Uploading...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  Upload File
                </>
              )}
            </button>
          </div>

          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input input-bordered w-full"
            />
          </div>

          {/* Filters */}
          <div className="flex gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="select select-bordered"
            >
              <option value="all">All Categories</option>
              <option value="receipt">Receipts</option>
              <option value="document">Documents</option>
              <option value="image">Images</option>
              <option value="audio">Audio</option>
              <option value="video">Video</option>
              <option value="pdf">PDF</option>
              <option value="other">Other</option>
            </select>

            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="select select-bordered"
            >
              <option value="all">All Sources</option>
              <option value="user_upload">User Upload</option>
              <option value="tool_generated">Tool Generated</option>
              <option value="tool_downloaded">Tool Downloaded</option>
            </select>
          </div>
        </div>

        {/* Files Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <span className="loading loading-spinner loading-lg text-primary"></span>
          </div>
        ) : filteredFiles.length === 0 ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 mx-auto text-base-content/30 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <h3 className="text-lg font-semibold text-base-content/70 mb-2">No files found</h3>
            <p className="text-base-content/50 mb-4">
              {searchQuery ? 'Try a different search term' : 'Upload your first file to get started'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                className="card bg-base-100 shadow-md hover:shadow-lg transition-shadow"
              >
                <div className="card-body p-4">
                  {/* File Icon & Name */}
                  <div className="flex items-start gap-3">
                    <div className="text-4xl">{getFileIcon(file.mime_type)}</div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-base truncate" title={file.original_filename}>
                        {file.original_filename}
                      </h3>
                      <p className="text-xs text-base-content/60">
                        {formatFileSize(file.file_size)} • {new Date(file.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>

                  {/* Description */}
                  {file.description && (
                    <p className="text-sm text-base-content/70 mt-2 line-clamp-2">
                      {file.description}
                    </p>
                  )}

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 mt-3">
                    <span className="badge badge-sm badge-outline">{file.category}</span>
                    {file.source === 'tool_generated' && (
                      <span className="badge badge-sm badge-primary">Tool Generated</span>
                    )}
                    {file.is_temporary && (
                      <span className="badge badge-sm badge-warning">Temporary</span>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="card-actions justify-end mt-4 pt-4 border-t border-base-200">
                    <button
                      onClick={() => handleEditFile(file)}
                      className="btn btn-ghost btn-sm gap-1"
                      title="Edit"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </button>
                    <button
                      onClick={() => handleDownloadFile(file)}
                      className="btn btn-ghost btn-sm gap-1"
                      title="Download"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Download
                    </button>
                    <button
                      onClick={() => handleDeleteFile(file.id)}
                      className="btn btn-ghost btn-sm gap-1 text-error hover:bg-error/10"
                      title="Delete"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Edit Modal */}
      {editingFile && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">Edit File</h3>
            
            <div className="space-y-4">
              {/* Filename (read-only) */}
              <div>
                <label className="label">
                  <span className="label-text">Filename</span>
                </label>
                <input
                  type="text"
                  value={editingFile.original_filename}
                  disabled
                  className="input input-bordered w-full bg-base-200"
                />
              </div>

              {/* Category */}
              <div>
                <label className="label">
                  <span className="label-text">Category</span>
                </label>
                <select
                  value={editCategory}
                  onChange={(e) => setEditCategory(e.target.value)}
                  className="select select-bordered w-full"
                >
                  <option value="receipt">Receipt</option>
                  <option value="document">Document</option>
                  <option value="image">Image</option>
                  <option value="audio">Audio</option>
                  <option value="video">Video</option>
                  <option value="pdf">PDF</option>
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="label">
                  <span className="label-text">Description</span>
                </label>
                <textarea
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="textarea textarea-bordered w-full"
                  rows={3}
                  placeholder="Add a description..."
                />
              </div>
            </div>

            <div className="modal-action">
              <button onClick={handleCancelEdit} className="btn btn-ghost">
                Cancel
              </button>
              <button onClick={handleSaveEdit} className="btn btn-primary">
                Save Changes
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={handleCancelEdit}></div>
        </div>
      )}
    </div>
  );
}
