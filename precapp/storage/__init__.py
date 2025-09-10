"""
Storage package for Django Precatorios application

This package provides enhanced file storage functionality including:
- Custom S3 storage backends optimized for large files
- File upload/download utilities
- File validation and processing helpers
- Configuration management for storage settings
"""

from .backends import MediaS3Storage, LargeFileS3Storage, StaticS3Storage
from .utils import (
    handle_large_file_download,
    validate_file_upload,
    get_upload_progress_callback,
    get_file_info,
    clean_old_files
)
from .config import (
    get_s3_config,
    get_upload_limits,
    get_allowed_extensions,
    get_content_type,
    validate_s3_configuration
)

__all__ = [
    # Storage backends
    'MediaS3Storage',
    'LargeFileS3Storage', 
    'StaticS3Storage',
    
    # File utilities
    'handle_large_file_download',
    'validate_file_upload',
    'get_upload_progress_callback',
    'get_file_info',
    'clean_old_files',
    
    # Configuration
    'get_s3_config',
    'get_upload_limits',
    'get_allowed_extensions',
    'get_content_type',
    'validate_s3_configuration',
]
