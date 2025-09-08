# AWS S3 Configuration with IAM Roles for EC2 Instances

## Overview

This guide covers setting up AWS S3 for both **test** and **production** environments using **IAM Roles** instead of access keys. This approach is more secure and is the recommended method for EC2 instances.

**Why IAM Roles are Better:**
- ✅ **No credential management** - No need to store or rotate access keys
- ✅ **Automatic credential rotation** - AWS handles this automatically
- ✅ **Enhanced security** - Credentials never leave the EC2 instance
- ✅ **Environment isolation** - Different roles for test and production

## 🗂️ S3 Folder Structure

```
precatorios-media/
├── media/
│   ├── test/           # Test environment files
│   │   ├── 2025/
│   │   └── uploads/
│   └── production/     # Production environment files
│       ├── 2025/
│       └── uploads/
└── static/            # Static files (if using S3 for static)
```

## 1. Create S3 Bucket

### Step 1: Create the S3 Bucket
1. **Go to AWS Console** → S3 → "Create bucket"
2. **Bucket name**: `precatorios-media`
3. **Region**: Choose the same region as your EC2 instances (e.g., `us-east-1`)
4. **Block Public Access**: ✅ Keep all blocks enabled (files will be private)
5. **Versioning**: Enable for production buckets
6. **Encryption**: Enable server-side encryption (SSE-S3)
7. **Click** "Create bucket"

### Step 2: Configure Bucket Settings
```bash
# Create the folder structure (optional, Django will create as needed)
aws s3api put-object --bucket precatorios-media --key media/test/
aws s3api put-object --bucket precatorios-media --key media/production/
```

## 2. Bucket Configuration

### Basic Settings:
- **Region**: Same as your EC2 instances
- **Block Public Access**: Keep enabled (files are private by default)
- **Versioning**: Enable for production, optional for test
- **Encryption**: Enable server-side encryption

### CORS Configuration (if needed for direct browser uploads):
1. **Go to** your bucket → Permissions → CORS
2. **Add CORS configuration**:
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": [
            "http://your-ec2-public-ip",
            "https://your-ec2-public-ip",
            "http://your-test-domain.com",
            "https://your-production-domain.com"
        ],
        "ExposeHeaders": []
    }
]
```

**Example with actual values:**
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": [
            "http://54.191.130.149",
            "https://54.191.130.149",
            "http://precatorios-test.example.com",
            "https://precatorios-production.example.com"
        ],
        "ExposeHeaders": []
    }
]
```

## 3. Create IAM Policies for S3 Access

### Step 1: Create the S3 Policy
1. **Go to AWS Console** → IAM → Policies → "Create policy"
2. **Switch to JSON tab** and paste the policy below
3. **Name**: `DjangoS3PrecatoriosPolicy`
4. **Description**: `S3 access for Django Precatorios application`
5. **Click** "Create policy"

### IAM Policy for Environment-Specific Access:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListBucketWithPrefix",
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
        },
        {
            "Sid": "ManageObjectsInEnvironmentFolders",
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
            "Sid": "GetBucketLocation",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::precatorios-media"
        }
    ]
}
```

### Alternative: Restrictive Policies by Environment

#### Test Environment Only Policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "TestEnvironmentAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::precatorios-media",
            "Condition": {
                "StringLike": {
                    "s3:prefix": "media/test/*"
                }
            }
        },
        {
            "Sid": "TestObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::precatorios-media/media/test/*"
        },
        {
            "Sid": "GetBucketLocation",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::precatorios-media"
        }
    ]
}
```

#### Production Environment Only Policy:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ProductionEnvironmentAccess",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::precatorios-media",
            "Condition": {
                "StringLike": {
                    "s3:prefix": "media/production/*"
                }
            }
        },
        {
            "Sid": "ProductionObjectAccess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:GetObjectAcl",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::precatorios-media/media/production/*"
        },
        {
            "Sid": "GetBucketLocation",
            "Effect": "Allow",
            "Action": [
                "s3:GetBucketLocation"
            ],
            "Resource": "arn:aws:s3:::precatorios-media"
        }
    ]
}
```

## 4. Create IAM Roles for EC2 Instances

### Step 1: Create IAM Role for Test Environment
1. **Go to AWS Console** → IAM → Roles → "Create role"
2. **Select trusted entity**:
   - Trusted entity type: ✅ **AWS service**
   - Use case: ✅ **EC2**
   - Click "Next"
3. **Attach permissions**:
   - Search for: `DjangoS3PrecatoriosPolicy` (created in Step 3)
   - ✅ Select the policy
   - Click "Next"
4. **Role details**:
   - Role name: `EC2-Django-Test-S3-Role`
   - Description: `S3 access for Django Test environment`
   - Click "Create role"

### Step 2: Create IAM Role for Production Environment
1. **Repeat the process** for production:
   - Role name: `EC2-Django-Production-S3-Role`
   - Description: `S3 access for Django Production environment`
   - **Use the same policy** or create environment-specific policies

### Step 3: Assign IAM Roles to EC2 Instances

#### For Test Environment EC2:
1. **Go to EC2 Console** → Instances
2. **Select your TEST EC2 instance**
3. **Actions** → Security → **Modify IAM role**
4. **IAM role**: Select `EC2-Django-Test-S3-Role`
5. **Click** "Update IAM role"

#### For Production Environment EC2:
1. **Select your PRODUCTION EC2 instance**
2. **Actions** → Security → **Modify IAM role**
3. **IAM role**: Select `EC2-Django-Production-S3-Role`
4. **Click** "Update IAM role"

### Step 4: Verify Role Assignment
```bash
# SSH into your EC2 instance and run:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Expected result: Should return your role name, e.g.:
# EC2-Django-Test-S3-Role

# If you get NO RESPONSE or EMPTY RESPONSE:
# 🚨 This means NO IAM ROLE is assigned to your EC2 instance!

# SOLUTION: Assign IAM role through AWS Console:
# 1. AWS Console → EC2 → Instances
# 2. Select your EC2 instance
# 3. Actions → Security → Modify IAM role
# 4. Select: EC2-Django-Test-S3-Role
# 5. Click "Update IAM role"
# 6. Wait 30 seconds, then try the curl command again
```

**🔧 Troubleshooting Role Assignment:**
```bash
# If still no response after assigning role, try:
curl -v http://169.254.169.254/latest/meta-data/iam/info

# This should show connection details and help debug the issue
```

## 5. Configure Django Environment Files (No Access Keys Needed!)

### Test Environment (.env.test):
```bash
# S3 Configuration
USE_S3=True
AWS_STORAGE_BUCKET_NAME=precatorios-media
AWS_S3_REGION_NAME=us-west-2

# NO ACCESS KEYS NEEDED - IAM Role provides automatic authentication!
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are NOT required
```

### Production Environment (.env.production):
```bash
# S3 Configuration
USE_S3=True
AWS_STORAGE_BUCKET_NAME=precatorios-media
AWS_S3_REGION_NAME=us-west-2

# NO ACCESS KEYS NEEDED - IAM Role provides automatic authentication!
# AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are NOT required
```

## 6. Update Django Settings (Already Configured)

Your `settings.py` is already configured to work with IAM roles. When using IAM roles, boto3 automatically detects and uses the instance credentials:

```python
# In settings.py - this works with both access keys AND IAM roles
if USE_S3:
    # If IAM role is assigned, boto3 automatically uses it
    # If access keys are in environment, boto3 uses those
    # No code changes needed!
    AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
    AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
    AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
    # ... rest of S3 configuration
```

## 7. Testing S3 Configuration with IAM Roles

### Step 1: Verify IAM Role Assignment
```bash
# SSH into your EC2 instance FIRST (this won't work from your local machine!)
ssh -i your-key.pem ubuntu@your-ec2-ip

# ⚠️  IMPORTANT: The following command ONLY works from INSIDE the EC2 instance
# 169.254.169.254 is the AWS Instance Metadata Service - only accessible from EC2
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Should return your role name, e.g., EC2-Django-Test-S3-Role
```

**🚨 Common Error**: If you get "connection refused" or "timeout", you're probably running this from your local machine instead of inside the EC2 instance.

**✅ Correct Process**:
1. SSH into your EC2 instance first
2. Then run the curl command from within the EC2 instance
3. The command will only work from inside AWS EC2 instances

### Step 2: Test AWS CLI Access
```bash
# Test S3 access using IAM role (no credentials needed)
aws s3 ls s3://precatorios-media/

# Test upload
echo "test content from $(date)" > test-iam-role.txt
aws s3 cp test-iam-role.txt s3://precatorios-media/media/test/

# Test download
aws s3 cp s3://precatorios-media/media/test/test-iam-role.txt downloaded-iam.txt

# Test delete
aws s3 rm s3://precatorios-media/media/test/test-iam-role.txt
```

### Step 3: Test Django Integration
```bash
# Navigate to your Django project
cd /var/www/precatorios
source venv/bin/activate

# Test Django S3 integration
python manage.py shell
```

```python
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os

print(f"Environment: {settings.ENVIRONMENT}")
print(f"Using S3: {settings.USE_S3}")
print(f"Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
print(f"Location: {settings.AWS_LOCATION}")

# Check if using IAM role (no access keys in environment)
access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'Not set')
print(f"Access Key ID: {access_key}")
if access_key == 'Not set':
    print("✅ Using IAM role for authentication (recommended)")
else:
    print("⚠️  Using access keys for authentication")

# Test file upload
file_content = f"Test content from {settings.ENVIRONMENT} environment at {os.system('date')}"
file = ContentFile(file_content.encode(), name=f"test-{settings.ENVIRONMENT}.txt")
saved_name = default_storage.save(f"test-uploads/test-{settings.ENVIRONMENT}.txt", file)
print(f"✅ File saved as: {saved_name}")

# Test URL generation
url = default_storage.url(saved_name)
print(f"✅ File URL: {url}")

# Test file existence
exists = default_storage.exists(saved_name)
print(f"✅ File exists: {exists}")

# Test file size
try:
    size = default_storage.size(saved_name)
    print(f"✅ File size: {size} bytes")
except:
    print("⚠️  Could not get file size")

# Clean up test file
default_storage.delete(saved_name)
print("✅ Test file deleted successfully")
```

### Step 4: Test Different Environments
```bash
# Test that TEST environment only accesses test folder
# and PRODUCTION environment only accesses production folder

# In test environment:
python manage.py shell -c "
from django.conf import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'S3 Location: {settings.AWS_LOCATION}')
# Should show: Environment: test, S3 Location: media/test
"

# In production environment:
python manage.py shell -c "
from django.conf import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'S3 Location: {settings.AWS_LOCATION}')
# Should show: Environment: production, S3 Location: media/production
"
```

## 8. File Upload Testing in Django Application

### Test File Upload in Views:
```python
# In your Django view or shell
from django.core.files.base import ContentFile
from precapp.models import YourModel  # Replace with your actual model

# Test file upload
test_file = ContentFile(b"Test file content for IAM role", name="test-iam.txt")
instance = YourModel.objects.create(
    name="Test Upload with IAM Role",
    file_field=test_file  # Replace with your actual file field
)

print(f"File uploaded to: {instance.file_field.url}")
print(f"File name: {instance.file_field.name}")

# The URL should point to S3 and include your environment path
# Example: https://precatorios-media.s3.amazonaws.com/media/test/test-iam.txt
```

## 9. Troubleshooting IAM Role Issues

### Common IAM Role Issues:

#### 0. "Connection Refused" or "Timeout" for 169.254.169.254 ⚠️
```bash
# ERROR: curl: (7) Failed to connect to 169.254.169.254 port 80: Connection refused
# ERROR: curl: (28) Failed to connect to 169.254.169.254 port 80: Connection timed out

# 🚨 CAUSE: You're running this from your LOCAL machine, not from EC2!
# 🔧 SOLUTION: You MUST be inside an EC2 instance to access the metadata service

# ✅ CORRECT PROCESS:
# 1. SSH into your EC2 instance first:
ssh -i your-key.pem ubuntu@your-ec2-public-ip

# 2. THEN run the metadata commands from inside EC2:
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# 📝 NOTE: 169.254.169.254 is the AWS Instance Metadata Service
# It's only accessible from WITHIN EC2 instances, never from outside AWS
```

#### 1. "No IAM Role Assigned" Error
```bash
# Check if role is assigned to EC2 instance (run from INSIDE EC2!)
curl http://169.254.169.254/latest/meta-data/iam/info

# If no role assigned, you'll get an error
# Solution: Assign IAM role to EC2 instance (Step 4 above)
```

#### 2. "Access Denied" Error
```bash
# Check IAM role permissions
aws iam get-role-policy --role-name EC2-Django-Test-S3-Role --policy-name DjangoS3PrecatoriosPolicy

# Check if bucket exists and is accessible
aws s3 ls s3://precatorios-media/

# Solution: Verify IAM policy has correct permissions
```

#### 3. "Wrong Environment Folder" Error
```bash
# Check Django environment configuration
python manage.py shell -c "
from django.conf import settings
print('Environment:', settings.ENVIRONMENT)
print('S3 Location:', settings.AWS_LOCATION)
print('Expected path: media/' + settings.ENVIRONMENT + '/')
"

# Solution: Ensure .env file has correct ENVIRONMENT variable
```

#### 4. "Region Mismatch" Error
```bash
# Check bucket region
aws s3api get-bucket-location --bucket precatorios-media

# Check EC2 instance region
curl http://169.254.169.254/latest/meta-data/placement/region

# Solution: Ensure bucket and EC2 are in same region
```

#### 5. Django Settings Verification
```python
# Run this in Django shell to check configuration
python manage.py shell -c "
from django.conf import settings
import os

print('=== Django S3 Configuration ===')
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Use S3: {getattr(settings, \"USE_S3\", \"Not set\")}')
print(f'Bucket: {getattr(settings, \"AWS_STORAGE_BUCKET_NAME\", \"Not set\")}')
print(f'Region: {getattr(settings, \"AWS_S3_REGION_NAME\", \"Not set\")}')
print(f'Location: {getattr(settings, \"AWS_LOCATION\", \"Not set\")}')

print('\n=== Environment Variables ===')
print(f'AWS_ACCESS_KEY_ID: {os.environ.get(\"AWS_ACCESS_KEY_ID\", \"Not set (Good! Using IAM role)\")}')
print(f'AWS_SECRET_ACCESS_KEY: {\"Set\" if os.environ.get(\"AWS_SECRET_ACCESS_KEY\") else \"Not set (Good! Using IAM role)\"}')

print('\n=== IAM Role Check ===')
try:
    import boto3
    session = boto3.Session()
    credentials = session.get_credentials()
    print(f'Credentials source: {credentials.method}')
    if 'iam-role' in credentials.method:
        print('✅ Using IAM role for authentication')
    else:
        print('⚠️  Using other authentication method')
except Exception as e:
    print(f'Error checking credentials: {e}')
"
```

### IAM Role Best Practices

#### **🔒 Security Considerations**
1. **Principle of Least Privilege**: Only grant necessary S3 permissions
2. **Environment Isolation**: Use separate roles for test and production
3. **No Hardcoded Credentials**: Never put access keys in code or config files
4. **Monitor Usage**: Enable CloudTrail for S3 API calls
5. **Regular Audits**: Review IAM role permissions periodically

#### **📊 Permission Explanation**

| Permission | Purpose | Required? |
|------------|---------|-----------|
| `s3:ListBucket` | List objects in bucket | ✅ Yes |
| `s3:GetObject` | Download/read files | ✅ Yes |
| `s3:PutObject` | Upload files | ✅ Yes |
| `s3:DeleteObject` | Delete files | ✅ Yes |
| `s3:GetObjectAcl` | Read object permissions | ⚠️ If using ACLs |
| `s3:PutObjectAcl` | Set object permissions | ⚠️ If using ACLs |
| `s3:GetBucketLocation` | Get bucket region | ✅ Yes |

### Quick Debugging Commands

```bash
# 1. Check IAM role assignment
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# 2. Test S3 access
aws s3 ls s3://precatorios-media/media/test/ --region us-east-1

# 3. Check Django environment
cd /var/www/precatorios && python manage.py shell -c "
from django.conf import settings; 
print(f'{settings.ENVIRONMENT=}'); 
print(f'{settings.USE_S3=}'); 
print(f'{settings.AWS_LOCATION=}')
"

# 4. Test file upload
echo "test $(date)" > /tmp/test.txt
aws s3 cp /tmp/test.txt s3://precatorios-media/media/test/debug-test.txt

# 5. Test Django file upload
cd /var/www/precatorios && python manage.py shell -c "
from django.core.files.storage import default_storage;
from django.core.files.base import ContentFile;
f = ContentFile(b'Debug test');
name = default_storage.save('debug/test.txt', f);
print(f'Saved: {name}');
print(f'URL: {default_storage.url(name)}');
default_storage.delete(name)
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

This configuration ensures your test and production environments use S3 storage with proper isolation and security using IAM roles!

## 11. Summary: Benefits of IAM Role-Based S3 Integration

### 🔐 **Security Advantages**

#### **1. No Credential Management**
- **❌ With Access Keys**: Need to store, rotate, and secure AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY
- **✅ With IAM Roles**: AWS automatically handles credential rotation and security

#### **2. Enhanced Security**
- **❌ Access Keys**: Can be accidentally exposed in logs, environment variables, or code
- **✅ IAM Roles**: Temporary credentials that can't be extracted from EC2 instances

#### **3. Simplified Deployment**
- **❌ Access Keys**: Must securely transfer credentials to production servers
- **✅ IAM Roles**: Automatically available on EC2 instances, no manual configuration

#### **4. Audit and Compliance**
- **❌ Access Keys**: Difficult to track which key is used where
- **✅ IAM Roles**: Clear audit trail showing which EC2 instance accessed which S3 resources

### 🚀 **Operational Benefits**

| Aspect | Access Keys | IAM Roles |
|--------|-------------|-----------|
| **Setup Complexity** | Medium | Simple |
| **Credential Rotation** | Manual | Automatic |
| **Security Risk** | High | Low |
| **Deployment** | Complex | Simple |
| **Monitoring** | Limited | Comprehensive |
| **Compliance** | Difficult | Easy |

### 📋 **Implementation Checklist**

- [ ] **Step 1**: Create S3 bucket for each environment
- [ ] **Step 2**: Create IAM policy with specific S3 permissions
- [ ] **Step 3**: Create IAM role and attach policy
- [ ] **Step 4**: Assign IAM role to EC2 instances
- [ ] **Step 5**: Update Django settings to remove access key variables
- [ ] **Step 6**: Test file uploads in each environment
- [ ] **Step 7**: Verify Django uses IAM role authentication
- [ ] **Step 8**: Monitor S3 access through CloudTrail

### 🎯 **Final Configuration Verification**

After completing this setup, your Django application will:

1. **✅ Automatically authenticate** to S3 using EC2 IAM roles
2. **✅ Isolate files by environment** (test/production folders)
3. **✅ Handle file uploads securely** without hardcoded credentials
4. **✅ Provide audit trails** for all S3 operations
5. **✅ Scale securely** as you add more EC2 instances

### 📞 **Support Resources**

- **AWS IAM Role Documentation**: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html
- **Django-Storages Documentation**: https://django-storages.readthedocs.io/
- **AWS S3 Security Best Practices**: https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html

---

**🔒 Remember**: IAM roles represent the security best practice for EC2-to-S3 authentication. This setup eliminates the need for AWS access keys while providing enhanced security, automatic credential rotation, and comprehensive audit capabilities.
