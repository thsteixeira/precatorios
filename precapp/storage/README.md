# Storage Package - Large File Upload and Download Configuration

## Overview

This document describes the `precapp.storage` package which provides enhanced file storage functionality for handling large files (up to 50MB) in the Django Precatorios application with AWS S3 storage.

## 📁 Package Structure

```
precapp/storage/
├── __init__.py              # Package exports and imports
├── backends.py              # Custom S3 storage backend classes
├── utils.py                 # File handling utilities
├── config.py                # Configuration management and validation
└── README.md               # This documentation file
```

## � Package Components

### **Storage Backends** (`backends.py`)
- **`LargeFileS3Storage`**: Base S3 storage optimized for large files
- **`MediaS3Storage`**: Environment-specific media file storage
- **`StaticS3Storage`**: Static file storage (future use)

### **File Utilities** (`utils.py`)
- **`handle_large_file_download()`**: Enhanced download with signed URLs
- **`validate_file_upload()`**: File validation and size checking
- **`get_file_info()`**: File metadata extraction
- **`clean_old_files()`**: Storage cleanup utilities

### **Configuration** (`config.py`)
- **`validate_s3_configuration()`**: Validate S3 setup
- **`get_s3_config()`**: Get S3 settings with defaults
- **`get_upload_limits()`**: Get file upload limits
- **`get_allowed_extensions()`**: Get allowed file types by category

## �🚀 Key Improvements

### **1. Enhanced S3 Configuration**
- **Multipart uploads** for files > 25MB
- **Parallel chunk processing** with 10 concurrent connections
- **Signed URLs** for secure file downloads
- **Custom storage backend** optimized for large files
- **Retry logic** with adaptive backoff

### **2. Increased Upload Limits**
- **Django file size limit**: Set to 50MB maximum
- **S3 multipart threshold**: 25MB chunks for optimal performance
- **Memory usage**: Controlled with streaming uploads

### **3. Download Optimization**
- **Direct S3 URLs** for faster downloads
- **Signed URLs** with 1-hour expiration for security
- **Streaming responses** as fallback
- **Proper MIME type detection**

## 📁 File Structure

## 📁 File Structure

### **Storage Package Files:**
```
precapp/storage/                  # Storage package directory
├── __init__.py                  # Package exports
├── backends.py                  # Custom S3 storage backends
├── utils.py                     # File handling utilities
├── config.py                    # Configuration management
└── README.md                    # This documentation
```

### **Related Files:**
```
precapp/
├── tests/
│   └── test_s3_storage.py       # Comprehensive S3 unit tests
├── management/commands/
│   └── validate_storage.py      # Storage configuration validator
└── views.py                     # Uses storage package for file operations
```

### **Modified Files:**
```
precatorios/settings.py     # Enhanced S3 configuration
deployment/environments/
├── .env.test              # Updated with S3 settings
└── .env.production        # Updated with S3 settings
```

## ⚙️ Configuration Details

### **Django Settings (settings.py)**

#### **File Upload Limits:**
```python
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 50     # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024 * 50     # 50MB
SESSION_COOKIE_AGE = 7200                           # 2 hours for large uploads
```

#### **S3 Multipart Configuration:**
```python
AWS_S3_MULTIPART_THRESHOLD = 1024 * 1024 * 25      # 25MB threshold
AWS_S3_MULTIPART_CHUNKSIZE = 1024 * 1024 * 25      # 25MB chunks
AWS_S3_MAX_MEMORY_SIZE = 1024 * 1024 * 25          # 25MB max memory
AWS_S3_USE_THREADS = True                           # Enable threading
AWS_S3_MAX_CONCURRENCY = 10                        # 10 parallel uploads
```

#### **Download Security:**
```python
AWS_QUERYSTRING_AUTH = True                         # Signed URLs
AWS_QUERYSTRING_EXPIRE = 3600                       # 1 hour expiration
AWS_S3_SIGNATURE_VERSION = 's3v4'                   # Latest signature
```

### **Environment Variables**

#### **Required S3 Settings:**
```bash
# Basic S3 Configuration
USE_S3=True
AWS_STORAGE_BUCKET_NAME=precatorios-media
AWS_S3_REGION_NAME=us-west-2

# Multipart Upload Settings
AWS_S3_MULTIPART_THRESHOLD=26214400      # 25MB
AWS_S3_MULTIPART_CHUNKSIZE=26214400      # 25MB
AWS_S3_MAX_MEMORY_SIZE=26214400          # 25MB
AWS_S3_USE_THREADS=True
AWS_S3_MAX_CONCURRENCY=10
AWS_S3_MAX_IO_QUEUE=1000

# Security Settings
AWS_QUERYSTRING_AUTH=True
AWS_QUERYSTRING_EXPIRE=3600
AWS_S3_SIGNATURE_VERSION=s3v4
```

## 🔧 Usage Examples

### **1. Testing S3 Configuration**
```bash
# Validate storage configuration
python manage.py validate_storage

# Show detailed configuration
python manage.py validate_storage --show-config

# Simple management command test
python manage.py test_s3_upload --size=50

# Run comprehensive unit tests
python manage.py test precapp.tests.test_s3_storage

# Web-based diagnostic (admin users only)
# Visit: /admin/test-s3/ in your browser
```

### **2. Handling File Downloads in Views**
```python
from precapp.storage.utils import handle_large_file_download

def download_precatorio_file(request, precatorio_id):
    precatorio = get_object_or_404(Precatorio, id=precatorio_id)
    
    if not precatorio.integra_precatorio:
        raise Http404("Arquivo não encontrado")
    
    return handle_large_file_download(
        request, 
        precatorio.integra_precatorio,
        filename=f"precatorio_{precatorio.cnj}.pdf"
    )
```

### **3. File Upload Validation**
```python
from precapp.storage.utils import validate_file_upload

def upload_view(request):
    if request.method == 'POST' and request.FILES:
        uploaded_file = request.FILES['file']
        
        # Validate file (50MB max, PDF only)
        is_valid, error_msg = validate_file_upload(
            uploaded_file, 
            max_size_mb=50, 
            allowed_extensions=['.pdf']
        )
        
        if not is_valid:
            messages.error(request, error_msg)
            return redirect('upload_form')
        
        # Process valid file...
```

### **4. Manual Testing in Django Shell**
```python
# Import and run manual test
from precapp.tests.test_s3_storage import run_s3_upload_test

# Test with 25MB file
success, result = run_s3_upload_test(size_mb=25, cleanup=True, verbose=True)

# Test and keep file for inspection
success, filename = run_s3_upload_test(size_mb=10, cleanup=False, verbose=True)
```

## 🧪 Testing and Validation

### **1. Basic S3 Connection Test**
```python
python manage.py shell -c "
from django.core.files.storage import default_storage;
from django.conf import settings;
print(f'S3 Enabled: {settings.USE_S3}');
print(f'Bucket: {settings.AWS_STORAGE_BUCKET_NAME}');
print(f'Storage Backend: {settings.DEFAULT_FILE_STORAGE}');
"
```

### **2. Upload Performance Test**
```bash
# Validate configuration first
python manage.py validate_storage

# Run comprehensive unit tests
python manage.py test precapp.tests.test_s3_storage.S3StorageTestCase.test_small_file_upload
python manage.py test precapp.tests.test_s3_storage.S3StorageTestCase.test_large_file_upload
python manage.py test precapp.tests.test_s3_storage.S3StorageTestCase.test_maximum_file_upload

# Run all storage tests with verbose output
python manage.py test precapp.tests.test_s3_storage -v 2
```

### **3. IAM Role Verification**
```bash
# Check IAM role (run on EC2)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Test AWS CLI access
aws s3 ls s3://precatorios-media/media/test/
```

## 🐛 Troubleshooting

### **Common Issues and Solutions:**

#### **1. Upload Timeouts**
```bash
# Symptom: Large files timeout during upload
# Solution: Check these settings:

# Nginx (if applicable)
client_max_body_size 50M;
client_body_timeout 300s;

# Gunicorn
--timeout 300

# Environment
SESSION_COOKIE_AGE=7200
```

#### **2. Download URL Errors**
```bash
# Symptom: Downloaded URLs return 403/404
# Solution: Verify IAM permissions and region:

# Check bucket region
aws s3api get-bucket-location --bucket precatorios-media

# Test signed URL generation
python manage.py shell -c "
from django.core.files.storage import default_storage;
url = default_storage.url('test-file.txt');
print(f'Generated URL: {url}');
"
```

#### **3. Multipart Upload Failures**
```bash
# Symptom: Large files fail to upload
# Solution: Check S3 bucket CORS configuration:

[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": ["ETag"]
    }
]
```

#### **4. Memory Issues**
```bash
# Symptom: Server runs out of memory during uploads
# Solution: Reduce chunk sizes:

AWS_S3_MULTIPART_THRESHOLD=10485760  # 10MB
AWS_S3_MULTIPART_CHUNKSIZE=10485760  # 10MB
AWS_S3_MAX_MEMORY_SIZE=10485760      # 10MB
```

## 📊 Performance Optimization

### **File Size Recommendations:**
- **< 25MB**: Single part upload (fastest)
- **25-50MB**: Multipart with 25MB chunks (balanced)
- **> 50MB**: Not supported (exceeds limit)

### **Network Optimization:**
- **Concurrent uploads**: 5-10 threads optimal
- **Chunk size**: Balance between speed and memory
- **Retry policy**: Adaptive backoff prevents overwhelming

### **Cost Optimization:**
- **Lifecycle policies**: Move old files to cheaper storage
- **Compression**: Use gzip for text-based files
- **Monitoring**: Track S3 usage and costs

## 🔐 Security Considerations

### **Access Control:**
- **IAM Roles**: Preferred over access keys
- **Signed URLs**: Temporary access with expiration
- **Private ACLs**: Files not publicly accessible
- **Environment separation**: Test/Production isolation

### **Data Protection:**
- **Encryption**: Server-side encryption enabled
- **Versioning**: Track file changes
- **Backup**: Regular backups to different region
- **Audit**: CloudTrail logging enabled

## 📋 Deployment Checklist

### **Pre-Deployment:**
- [ ] **Update environment files** with new S3 settings
- [ ] **Test S3 connectivity** with test command
- [ ] **Verify IAM role** assignment on EC2
- [ ] **Check bucket region** matches EC2 region
- [ ] **Test file upload/download** in staging

### **Post-Deployment:**
- [ ] **Run upload tests** with various file sizes
- [ ] **Monitor performance** and memory usage
- [ ] **Check error logs** for S3-related issues
- [ ] **Verify signed URLs** work correctly
- [ ] **Test download speeds** from different locations

### **Monitoring:**
- [ ] **S3 CloudWatch metrics** enabled
- [ ] **Django logging** configured for file operations
- [ ] **Application performance monitoring** setup
- [ ] **Regular backup verification**

---

## 🆘 Quick Emergency Fixes

### **If S3 is completely broken:**
1. **Disable S3**: Set `USE_S3=False` in environment
2. **Use local storage**: Files will be stored locally
3. **Fix S3 config**: Debug and reconfigure S3
4. **Re-enable S3**: Set `USE_S3=True` after testing

### **If uploads are failing:**
1. **Check file size**: Ensure < 100MB limit
2. **Verify IAM permissions**: Test with AWS CLI
3. **Check network**: Test S3 connectivity
4. **Reduce chunk size**: Lower memory requirements

This configuration should resolve your large file upload and download issues while providing robust error handling and monitoring capabilities.
