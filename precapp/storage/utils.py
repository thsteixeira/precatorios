"""
File handling utilities for upload, download, and validation
"""

from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.shortcuts import redirect
from django.core.files.storage import default_storage
from django.conf import settings
from django.contrib import messages
from django.utils.encoding import smart_str
import logging
import mimetypes
import urllib.parse

logger = logging.getLogger(__name__)


def handle_large_file_download(request, file_field, filename=None):
    """
    Handle download of large files from S3 with proper error handling
    
    Args:
        request: Django request object
        file_field: Django FileField instance
        filename: Optional custom filename for download
    
    Returns:
        HttpResponse or StreamingHttpResponse for file download
    """
    try:
        if not file_field:
            raise Http404("Arquivo não encontrado")
        
        # Get file name
        if filename is None:
            filename = file_field.name.split('/')[-1]
        
        # Check if file exists
        if not default_storage.exists(file_field.name):
            logger.error(f"File does not exist in storage: {file_field.name}")
            raise Http404("Arquivo não encontrado no armazenamento")
        
        # For S3 storage, redirect to signed URL for better performance
        if hasattr(settings, 'USE_S3') and settings.USE_S3:
            return redirect_to_s3_file(file_field, filename)
        else:
            return stream_local_file(file_field, filename)
            
    except Exception as e:
        logger.error(f"Error downloading file {file_field.name}: {str(e)}")
        messages.error(request, f"Erro ao baixar arquivo: {str(e)}")
        raise Http404("Erro ao acessar o arquivo")


def redirect_to_s3_file(file_field, filename):
    """
    Generate signed URL and redirect to S3 file for download
    More efficient for large files as it uses S3's direct download
    """
    try:
        # Generate signed URL with longer expiration for large files
        signed_url = default_storage.url(
            file_field.name,
            expire=7200,  # 2 hours for large file downloads
            http_method='GET'
        )
        
        # Add content-disposition header to force download with correct filename
        parsed_url = urllib.parse.urlparse(signed_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        # Add response-content-disposition to S3 URL
        query_params['response-content-disposition'] = [f'attachment; filename="{filename}"']
        
        # Rebuild URL with new parameters
        new_query = urllib.parse.urlencode(query_params, doseq=True)
        final_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            parsed_url.fragment
        ))
        
        # Return redirect response
        response = HttpResponse(status=302)
        response['Location'] = final_url
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        logger.info(f"Generated signed URL for download: {file_field.name}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating signed URL for {file_field.name}: {str(e)}")
        # Fallback to streaming response
        return stream_s3_file(file_field, filename)


def stream_s3_file(file_field, filename):
    """
    Stream file from S3 through Django (less efficient but more control)
    Use this as fallback when signed URLs don't work
    """
    try:
        # Open file from storage
        file_obj = default_storage.open(file_field.name, 'rb')
        
        # Get content type
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Create streaming response
        response = StreamingHttpResponse(
            file_chunks(file_obj),
            content_type=content_type
        )
        
        response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
        
        # Add content length if available
        try:
            file_size = default_storage.size(file_field.name)
            response['Content-Length'] = str(file_size)
        except:
            pass
        
        logger.info(f"Streaming file download: {file_field.name}")
        return response
        
    except Exception as e:
        logger.error(f"Error streaming file {file_field.name}: {str(e)}")
        raise Http404("Erro ao acessar o arquivo")


def stream_local_file(file_field, filename):
    """
    Stream local file for development/testing
    """
    try:
        file_obj = file_field.open('rb')
        
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        response = StreamingHttpResponse(
            file_chunks(file_obj),
            content_type=content_type
        )
        
        response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
        response['Content-Length'] = str(file_field.size)
        
        return response
        
    except Exception as e:
        logger.error(f"Error streaming local file {file_field.name}: {str(e)}")
        raise Http404("Erro ao acessar o arquivo")


def file_chunks(file_obj, chunk_size=8192):
    """
    Generator to read file in chunks for streaming
    Optimized chunk size for network transfer
    """
    try:
        while True:
            chunk = file_obj.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        file_obj.close()


def validate_file_upload(uploaded_file, max_size_mb=50, allowed_extensions=None):
    """
    Validate uploaded file before processing
    
    Args:
        uploaded_file: Django UploadedFile instance
        max_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.doc'])
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if uploaded_file.size > max_size_bytes:
        return False, f"Arquivo muito grande. Tamanho máximo: {max_size_mb}MB"
    
    # Check file extension
    import os
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    if file_extension not in allowed_extensions:
        return False, f"Tipo de arquivo não permitido. Permitidos: {', '.join(allowed_extensions)}"
    
    # Check if file is actually readable
    try:
        uploaded_file.seek(0)
        uploaded_file.read(1024)  # Try to read first 1KB
        uploaded_file.seek(0)  # Reset position
    except Exception as e:
        return False, f"Arquivo corrompido ou ilegível: {str(e)}"
    
    return True, None


def get_upload_progress_callback(request):
    """
    Return a callback function for tracking upload progress
    Can be used with custom storage backends
    """
    def progress_callback(bytes_transferred, total_bytes):
        if total_bytes > 0:
            percentage = int((bytes_transferred / total_bytes) * 100)
            # Store progress in session for AJAX retrieval
            request.session[f'upload_progress'] = {
                'percentage': percentage,
                'bytes_transferred': bytes_transferred,
                'total_bytes': total_bytes
            }
            return percentage
        return 0
    
    return progress_callback


def get_file_info(file_field):
    """
    Get comprehensive information about a file
    
    Args:
        file_field: Django FileField instance
    
    Returns:
        dict: File information including size, type, modified time, etc.
    """
    if not file_field:
        return None
    
    try:
        file_info = {
            'name': file_field.name.split('/')[-1],
            'path': file_field.name,
            'url': file_field.url if hasattr(file_field, 'url') else None,
            'exists': default_storage.exists(file_field.name),
        }
        
        # Get file size
        try:
            file_info['size'] = default_storage.size(file_field.name)
            file_info['size_mb'] = round(file_info['size'] / (1024 * 1024), 2)
        except:
            file_info['size'] = None
            file_info['size_mb'] = None
        
        # Get content type
        content_type, _ = mimetypes.guess_type(file_info['name'])
        file_info['content_type'] = content_type or 'application/octet-stream'
        
        # Get modified time
        try:
            file_info['modified_time'] = default_storage.get_modified_time(file_field.name)
        except:
            file_info['modified_time'] = None
        
        return file_info
        
    except Exception as e:
        logger.error(f"Error getting file info for {file_field.name}: {str(e)}")
        return None


def clean_old_files(path_prefix, days_old=30):
    """
    Clean up old files from storage
    
    Args:
        path_prefix: Path prefix to search for files (e.g., "test-uploads/")
        days_old: Files older than this many days will be deleted
    
    Returns:
        tuple: (files_deleted, errors)
    """
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    files_deleted = 0
    errors = []
    
    try:
        # This is a simplified implementation
        # In production, you might want to use S3 lifecycle policies instead
        logger.info(f"Starting cleanup of files older than {days_old} days in {path_prefix}")
        
        # Note: This would need to be implemented based on your specific storage backend
        # For S3, you could use boto3 to list and filter files by date
        
        return files_deleted, errors
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")
        errors.append(str(e))
        return files_deleted, errors
