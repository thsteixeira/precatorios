# AWS S3 Configuration for Test and Production Environments

## Overview

This guide covers setting up AWS S3 for both **test** and **production** environments. The configuration uses:

- **Test Environment**: Separate S3 bucket or folder structure for testing
- **Production Environment**: Dedicated S3 bucket for production files
- **Environment Isolation**: Files are stored in separate paths to prevent conflicts

## 🗂️ S3 Folder Structure

```
your-bucket-name/
├── media/
│   ├── test/           # Test environment files
│   │   ├── 2025/
│   │   └── uploads/
│   └── production/     # Production environment files
│       ├── 2025/
│       └── uploads/
└── static/            # Static files (if using S3 for static)
```

## 1. Create S3 Buckets

### Option A: Single Bucket with Folders (Recommended)
Create one bucket with environment-specific folders:

1. **Bucket name**: `precatorios-media` (or your preferred name)
2. **Test files**: Stored in `media/test/` folder
3. **Production files**: Stored in `media/production/` folder

### Option B: Separate Buckets
Create separate buckets for each environment:

1. **Test bucket**: `precatorios-test-media`
2. **Production bucket**: `precatorios-production-media`

## 2. Bucket Configuration

### Basic Settings:
- **Region**: Same as your EC2 instances
- **Block Public Access**: Keep enabled (files are private by default)
- **Versioning**: Enable for production, optional for test
- **Encryption**: Enable server-side encryption

### CORS Configuration (if needed):
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": [
            "https://your-test-domain.com",
            "https://your-production-domain.com"
        ],
        "ExposeHeaders": []
    }
]
```

## 3. IAM Configuration

### Create IAM User for Django
1. **Username**: `django-s3-user`
2. **Access type**: Programmatic access

### IAM Policy for Single Bucket (Option A):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::precatorios-media/media/test/*",
                "arn:aws:s3:::precatorios-media/media/production/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::precatorios-media",
            "Condition": {
                "StringLike": {
                    "s3:prefix": [
                        "media/test/*",
                        "media/production/*"
                    ]
                }
            }
        }
    ]
}
```

### IAM Policy for Separate Buckets (Option B):
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::precatorios-test-media/*",
                "arn:aws:s3:::precatorios-production-media/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::precatorios-test-media",
                "arn:aws:s3:::precatorios-production-media"
            ]
        }
    ]
}
```

## 4. Environment Configuration

### Test Environment (.env.test):
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_STORAGE_BUCKET_NAME=precatorios-media  # or precatorios-test-media
AWS_S3_REGION_NAME=us-east-1
```

### Production Environment (.env.production):
```bash
USE_S3=True
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_STORAGE_BUCKET_NAME=precatorios-media  # or precatorios-production-media
AWS_S3_REGION_NAME=us-east-1
```

## 5. Alternative: IAM Roles (More Secure)

Instead of access keys, assign IAM roles to your EC2 instances:

### Create IAM Roles:
1. **Test Role**: `EC2-Django-Test-S3-Role`
2. **Production Role**: `EC2-Django-Production-S3-Role`

### Attach Policies:
- Attach the appropriate S3 policy to each role
- Assign roles to respective EC2 instances

### Environment Configuration (with IAM roles):
```bash
USE_S3=True
# Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
# boto3 will automatically use the instance role
AWS_STORAGE_BUCKET_NAME=precatorios-media
AWS_S3_REGION_NAME=us-east-1
```

## 6. Testing S3 Configuration

### Test Connection:
```bash
python manage.py shell
```

```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings

print(f"Environment: {settings.ENVIRONMENT}")
print(f"Using S3: {settings.USE_S3}")
print(f"Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
print(f"Location: {settings.AWS_LOCATION}")

# Test upload
file = ContentFile(b"Test content from TEST environment")
name = default_storage.save("test-upload.txt", file)
print(f"File saved as: {name}")

# Test URL generation
url = default_storage.url(name)
print(f"File URL: {url}")

# Test file existence
exists = default_storage.exists(name)
print(f"File exists: {exists}")

# Clean up
default_storage.delete(name)
print("Test file deleted")
```

## 7. File Upload Testing

### Test File Upload in Views:
```python
# In your Django view or shell
from django.core.files.base import ContentFile
from precapp.models import YourModel  # Replace with your model

# Test file upload
test_file = ContentFile(b"Test file content", name="test.txt")
instance = YourModel.objects.create(
    name="Test Upload",
    file_field=test_file  # Replace with your file field
)

print(f"File uploaded to: {instance.file_field.url}")
```

## 8. Monitoring and Maintenance

### CloudWatch Metrics:
- Monitor S3 storage usage
- Track request metrics
- Set up billing alerts

### Backup Strategy:
- Enable versioning for production
- Set up cross-region replication (optional)
- Configure lifecycle policies for old files

### Security:
- Regularly rotate access keys
- Monitor access logs
- Use least privilege principle

## 9. Troubleshooting

### Common Issues:

#### Permission Denied:
```bash
# Check IAM permissions
aws s3 ls s3://your-bucket-name/

# Check bucket policy
aws s3api get-bucket-policy --bucket your-bucket-name
```

#### Region Mismatch:
```bash
# Verify bucket region
aws s3api get-bucket-location --bucket your-bucket-name
```

#### Django Settings:
```python
# Check Django configuration
python manage.py shell -c "
from django.conf import settings
print('Environment:', settings.ENVIRONMENT)
print('Use S3:', getattr(settings, 'USE_S3', 'Not set'))
print('Bucket:', getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set'))
print('Region:', getattr(settings, 'AWS_S3_REGION_NAME', 'Not set'))
print('Location:', getattr(settings, 'AWS_LOCATION', 'Not set'))
"
```

## 10. Cost Optimization

### Storage Classes:
- **Standard**: For frequently accessed files
- **Standard-IA**: For less frequently accessed files
- **Glacier**: For archival storage

### Lifecycle Policies:
```json
{
    "Rules": [
        {
            "Id": "TransitionToIA",
            "Status": "Enabled",
            "Transitions": [
                {
                    "Days": 30,
                    "StorageClass": "STANDARD_IA"
                }
            ]
        }
    ]
}
```

This configuration ensures your test and production environments use S3 storage with proper isolation and security!
