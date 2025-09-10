#!/usr/bin/env python3
"""
Debug script to test S3 access and download functionality
Run this in your test environment to diagnose S3 issues
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'precatorios.settings')
django.setup()

from precapp.models import Precatorio
from django.core.files.storage import default_storage

def test_s3_configuration():
    """Test S3 configuration and access"""
    print("🔧 Testing S3 Configuration...")
    print(f"Environment: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
    print(f"USE_S3: {getattr(settings, 'USE_S3', 'not set')}")
    
    if hasattr(settings, 'AWS_STORAGE_BUCKET_NAME'):
        print(f"S3 Bucket: {settings.AWS_STORAGE_BUCKET_NAME}")
    if hasattr(settings, 'AWS_S3_REGION_NAME'):
        print(f"S3 Region: {settings.AWS_S3_REGION_NAME}")
    if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
        print(f"AWS Access Key: {settings.AWS_ACCESS_KEY_ID[:10]}...")
    if hasattr(settings, 'AWS_LOCATION'):
        print(f"AWS Location: {settings.AWS_LOCATION}")
    
    print()

def test_file_access():
    """Test file access for precatorios with files"""
    print("📁 Testing File Access...")
    
    # Find precatorios with files
    precatorios_with_files = Precatorio.objects.filter(
        integra_precatorio__isnull=False
    ).exclude(integra_precatorio='')[:5]
    
    print(f"Found {precatorios_with_files.count()} precatorios with files")
    
    for precatorio in precatorios_with_files:
        print(f"\n📋 Testing Precatorio: {precatorio.cnj}")
        print(f"   File field: {precatorio.integra_precatorio}")
        
        if precatorio.integra_precatorio:
            file_name = precatorio.integra_precatorio.name
            print(f"   File path: {file_name}")
            
            # Test file existence
            try:
                exists = default_storage.exists(file_name)
                print(f"   File exists: {exists}")
            except Exception as e:
                print(f"   Error checking existence: {e}")
            
            # Test file size
            try:
                size = default_storage.size(file_name)
                print(f"   File size: {size} bytes ({size/(1024*1024):.2f} MB)")
            except Exception as e:
                print(f"   Error getting size: {e}")
            
            # Test file URL generation
            try:
                url = default_storage.url(file_name)
                print(f"   Generated URL: {url[:100]}...")
            except Exception as e:
                print(f"   Error generating URL: {e}")
            
            # Test file opening
            try:
                with default_storage.open(file_name, 'rb') as f:
                    first_bytes = f.read(100)
                    print(f"   Can read file: True ({len(first_bytes)} bytes read)")
            except Exception as e:
                print(f"   Error opening file: {e}")

def test_boto3_direct():
    """Test direct boto3 access"""
    print("\n🔗 Testing Direct Boto3 Access...")
    
    if not getattr(settings, 'USE_S3', False):
        print("S3 not enabled, skipping boto3 test")
        return
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        # Create S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', '')
        print(f"Testing bucket: {bucket_name}")
        
        # Test bucket access
        try:
            response = s3_client.head_bucket(Bucket=bucket_name)
            print("✅ Bucket access successful")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"❌ Bucket access failed: {error_code}")
            if error_code == '403':
                print("   This is likely a permissions issue")
            elif error_code == '404':
                print("   Bucket not found")
            return
        
        # List some objects
        try:
            aws_location = getattr(settings, 'AWS_LOCATION', 'media/test')
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=aws_location,
                MaxKeys=5
            )
            
            if 'Contents' in response:
                print(f"✅ Found {len(response['Contents'])} objects in {aws_location}")
                for obj in response['Contents'][:3]:
                    print(f"   - {obj['Key']} ({obj['Size']} bytes)")
            else:
                print(f"⚠️  No objects found in {aws_location}")
                
        except Exception as e:
            print(f"❌ Error listing objects: {e}")
    
    except ImportError:
        print("❌ boto3 not installed")
    except NoCredentialsError:
        print("❌ AWS credentials not found")
    except Exception as e:
        print(f"❌ Error with boto3: {e}")

if __name__ == "__main__":
    print("🧪 S3 Access Debug Tool")
    print("=" * 50)
    
    test_s3_configuration()
    test_file_access()
    test_boto3_direct()
    
    print("\n✅ Debug test complete!")
    print("\nNext steps:")
    print("1. Run this script in your test environment")
    print("2. Check the output for specific error messages")
    print("3. Verify AWS credentials and permissions")
    print("4. Check S3 bucket configuration and region")
