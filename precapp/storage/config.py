"""
Storage configuration and constants
"""

from django.conf import settings


# Default S3 configuration
DEFAULT_S3_CONFIG = {
    'multipart_threshold': 1024 * 1024 * 25,  # 25MB
    'multipart_chunksize': 1024 * 1024 * 25,  # 25MB
    'max_memory_size': 1024 * 1024 * 25,      # 25MB
    'use_threads': True,
    'max_concurrency': 10,
    'max_io_queue': 1000,
    'querystring_auth': True,
    'querystring_expire': 3600,  # 1 hour
    'signature_version': 's3v4',
    'retries': {
        'max_attempts': 10,
        'mode': 'adaptive'
    }
}

# File upload limits
FILE_UPLOAD_LIMITS = {
    'max_size_mb': 50,
    'max_size_bytes': 50 * 1024 * 1024,
    'session_timeout': 7200,  # 2 hours
}

# Allowed file extensions by category
ALLOWED_EXTENSIONS = {
    'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
    'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'spreadsheets': ['.xls', '.xlsx', '.csv'],
    'presentations': ['.ppt', '.pptx'],
    'all': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
}

# Content type mappings
CONTENT_TYPE_MAPPINGS = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.txt': 'text/plain',
    '.rtf': 'application/rtf',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.webp': 'image/webp',
}

# Storage paths by environment
STORAGE_PATHS = {
    'local': {
        'media_root': 'media/',
        'static_root': 'static/',
    },
    'test': {
        's3_location': 'media/test',
        'static_location': 'static/test',
    },
    'production': {
        's3_location': 'media/production',
        'static_location': 'static/production',
    }
}


def get_s3_config():
    """
    Get S3 configuration from settings with defaults
    """
    config = DEFAULT_S3_CONFIG.copy()
    
    # Override with settings values if available
    config.update({
        'multipart_threshold': getattr(settings, 'AWS_S3_MULTIPART_THRESHOLD', config['multipart_threshold']),
        'multipart_chunksize': getattr(settings, 'AWS_S3_MULTIPART_CHUNKSIZE', config['multipart_chunksize']),
        'max_memory_size': getattr(settings, 'AWS_S3_MAX_MEMORY_SIZE', config['max_memory_size']),
        'use_threads': getattr(settings, 'AWS_S3_USE_THREADS', config['use_threads']),
        'max_concurrency': getattr(settings, 'AWS_S3_MAX_CONCURRENCY', config['max_concurrency']),
        'max_io_queue': getattr(settings, 'AWS_S3_MAX_IO_QUEUE', config['max_io_queue']),
        'querystring_auth': getattr(settings, 'AWS_QUERYSTRING_AUTH', config['querystring_auth']),
        'querystring_expire': getattr(settings, 'AWS_QUERYSTRING_EXPIRE', config['querystring_expire']),
        'signature_version': getattr(settings, 'AWS_S3_SIGNATURE_VERSION', config['signature_version']),
        'retries': getattr(settings, 'AWS_S3_RETRIES', config['retries']),
    })
    
    return config


def get_upload_limits():
    """
    Get file upload limits from settings with defaults
    """
    limits = FILE_UPLOAD_LIMITS.copy()
    
    # Override with settings values if available
    if hasattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE'):
        limits['max_size_bytes'] = settings.FILE_UPLOAD_MAX_MEMORY_SIZE
        limits['max_size_mb'] = settings.FILE_UPLOAD_MAX_MEMORY_SIZE // (1024 * 1024)
    
    if hasattr(settings, 'SESSION_COOKIE_AGE'):
        limits['session_timeout'] = settings.SESSION_COOKIE_AGE
    
    return limits


def get_allowed_extensions(category='all'):
    """
    Get allowed file extensions for a category
    """
    return ALLOWED_EXTENSIONS.get(category, ALLOWED_EXTENSIONS['all'])


def get_content_type(filename):
    """
    Get content type for a filename
    """
    import os
    ext = os.path.splitext(filename)[1].lower()
    return CONTENT_TYPE_MAPPINGS.get(ext, 'application/octet-stream')


def get_storage_path(environment=None):
    """
    Get storage path configuration for environment
    """
    if environment is None:
        environment = getattr(settings, 'ENVIRONMENT', 'local')
    
    return STORAGE_PATHS.get(environment, STORAGE_PATHS['local'])


def validate_s3_configuration():
    """
    Validate S3 configuration
    Returns tuple (is_valid, errors)
    """
    errors = []
    
    # Check if S3 is enabled
    if not getattr(settings, 'USE_S3', False):
        return True, []  # Not using S3, no validation needed
    
    # Check required settings
    required_settings = [
        'AWS_STORAGE_BUCKET_NAME',
        'AWS_S3_REGION_NAME',
    ]
    
    for setting_name in required_settings:
        if not getattr(settings, setting_name, None):
            errors.append(f"Missing required setting: {setting_name}")
    
    # Check file upload limits
    limits = get_upload_limits()
    if limits['max_size_mb'] > 50:
        errors.append(f"File upload limit ({limits['max_size_mb']}MB) exceeds recommended maximum (50MB)")
    
    # Check S3 configuration values
    s3_config = get_s3_config()
    if s3_config['multipart_threshold'] < 5 * 1024 * 1024:  # 5MB minimum
        errors.append("Multipart threshold should be at least 5MB")
    
    return len(errors) == 0, errors
