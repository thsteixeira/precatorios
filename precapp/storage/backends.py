"""
Enhanced S3 Storage Backend for Large File Handling
Optimized with better multipart upload support and signed URL generation
"""

from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings
from botocore.config import Config
import logging

logger = logging.getLogger(__name__)


class LargeFileS3Storage(S3Boto3Storage):
    """
    Custom S3 storage optimized for large file uploads (up to 50MB)
    with enhanced multipart upload support and signed URL generation
    """
    
    def __init__(self, *args, **kwargs):
        # Enhanced configuration for large files
        kwargs.update({
            'region_name': getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
            'config': Config(
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
                retries=getattr(settings, 'AWS_S3_RETRIES', {
                    'max_attempts': 10,
                    'mode': 'adaptive'
                }),
                max_pool_connections=50,
                # Multipart configuration
                s3={
                    'multipart_threshold': getattr(settings, 'AWS_S3_MULTIPART_THRESHOLD', 1024 * 1024 * 25),
                    'multipart_chunksize': getattr(settings, 'AWS_S3_MULTIPART_CHUNKSIZE', 1024 * 1024 * 25),
                    'max_concurrency': getattr(settings, 'AWS_S3_MAX_CONCURRENCY', 10),
                    'use_threads': getattr(settings, 'AWS_S3_USE_THREADS', True),
                    'max_io_queue': getattr(settings, 'AWS_S3_MAX_IO_QUEUE', 1000),
                }
            ),
            'signature_version': getattr(settings, 'AWS_S3_SIGNATURE_VERSION', 's3v4'),
        })
        super().__init__(*args, **kwargs)
    
    def _save(self, name, content):
        """
        Enhanced save method with progress tracking for large files
        """
        try:
            logger.info(f"Starting upload of file: {name}, size: {content.size} bytes")
            
            # Use parent method which handles multipart automatically
            saved_name = super()._save(name, content)
            
            logger.info(f"Successfully uploaded file: {saved_name}")
            return saved_name
            
        except Exception as e:
            logger.error(f"Failed to upload file {name}: {str(e)}")
            raise
    
    def url(self, name, parameters=None, expire=None, http_method=None):
        """
        Enhanced URL generation with proper signed URLs for private files
        """
        try:
            # Use custom expiration time if provided, otherwise use settings default
            if expire is None:
                expire = getattr(settings, 'AWS_QUERYSTRING_EXPIRE', 3600)
            
            # Generate signed URL for private files
            if getattr(settings, 'AWS_QUERYSTRING_AUTH', True):
                return super().url(name, parameters=parameters, expire=expire, http_method=http_method)
            else:
                # For public files (if ACL is public)
                return super().url(name)
                
        except Exception as e:
            logger.error(f"Failed to generate URL for file {name}: {str(e)}")
            # Fallback to basic URL
            return f"https://{self.custom_domain}/{self.location}/{name}"
    
    def exists(self, name):
        """
        Enhanced exists check with better error handling
        """
        try:
            return super().exists(name)
        except Exception as e:
            logger.error(f"Error checking if file exists {name}: {str(e)}")
            return False
    
    def size(self, name):
        """
        Enhanced size method with better error handling
        """
        try:
            return super().size(name)
        except Exception as e:
            logger.error(f"Error getting file size {name}: {str(e)}")
            return 0
    
    def delete(self, name):
        """
        Enhanced delete method with better error handling
        """
        try:
            result = super().delete(name)
            logger.info(f"Successfully deleted file: {name}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete file {name}: {str(e)}")
            raise


class MediaS3Storage(LargeFileS3Storage):
    """
    Storage class specifically for media files with environment-specific locations
    """
    
    def __init__(self, *args, **kwargs):
        # Set location based on environment
        if hasattr(settings, 'AWS_LOCATION'):
            kwargs['location'] = settings.AWS_LOCATION
        
        super().__init__(*args, **kwargs)


class StaticS3Storage(LargeFileS3Storage):
    """
    Storage class for static files (if needed in the future)
    """
    
    def __init__(self, *args, **kwargs):
        kwargs.update({
            'location': getattr(settings, 'AWS_STATIC_LOCATION', 'static'),
            'default_acl': 'public-read',
        })
        super().__init__(*args, **kwargs)


# Progress callback for large file uploads (can be used in views)
def upload_progress_callback(bytes_transferred, total_bytes):
    """
    Callback function to track upload progress
    Can be used in views to show upload progress
    """
    percentage = int((bytes_transferred / total_bytes) * 100)
    logger.info(f"Upload progress: {percentage}% ({bytes_transferred}/{total_bytes} bytes)")
    return percentage
