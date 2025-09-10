"""
Test cases for S3 large file upload and download functionality
"""

from django.test import TestCase
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import time
import tempfile
import os


class S3StorageTestCase(TestCase):
    """Test S3 storage functionality with large files"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_files_created = []
    
    def tearDown(self):
        """Clean up test files"""
        for file_name in self.test_files_created:
            try:
                if default_storage.exists(file_name):
                    default_storage.delete(file_name)
            except Exception:
                pass  # Ignore cleanup errors
    
    def test_s3_configuration(self):
        """Test that S3 is properly configured"""
        self.assertTrue(getattr(settings, 'USE_S3', False), "S3 should be enabled for testing")
        self.assertTrue(getattr(settings, 'AWS_STORAGE_BUCKET_NAME', ''), "S3 bucket name should be configured")
        self.assertTrue(getattr(settings, 'AWS_S3_REGION_NAME', ''), "S3 region should be configured")
    
    def test_small_file_upload(self):
        """Test uploading a small file (< 25MB)"""
        file_size_mb = 10
        test_file, file_name = self._create_test_file(file_size_mb)
        
        # Upload file
        saved_name = default_storage.save(f"test-uploads/{file_name}", test_file)
        self.test_files_created.append(saved_name)
        
        # Verify file exists
        self.assertTrue(default_storage.exists(saved_name))
        
        # Verify file size
        stored_size = default_storage.size(saved_name)
        expected_size = file_size_mb * 1024 * 1024
        self.assertEqual(stored_size, expected_size)
    
    def test_large_file_upload(self):
        """Test uploading a large file (> 25MB) using multipart"""
        file_size_mb = 40
        test_file, file_name = self._create_test_file(file_size_mb)
        
        # Upload file
        saved_name = default_storage.save(f"test-uploads/{file_name}", test_file)
        self.test_files_created.append(saved_name)
        
        # Verify file exists
        self.assertTrue(default_storage.exists(saved_name))
        
        # Verify file size
        stored_size = default_storage.size(saved_name)
        expected_size = file_size_mb * 1024 * 1024
        self.assertEqual(stored_size, expected_size)
    
    def test_maximum_file_upload(self):
        """Test uploading maximum allowed file size (50MB)"""
        file_size_mb = 50
        test_file, file_name = self._create_test_file(file_size_mb)
        
        # Upload file
        saved_name = default_storage.save(f"test-uploads/{file_name}", test_file)
        self.test_files_created.append(saved_name)
        
        # Verify file exists
        self.assertTrue(default_storage.exists(saved_name))
        
        # Verify file size
        stored_size = default_storage.size(saved_name)
        expected_size = file_size_mb * 1024 * 1024
        self.assertEqual(stored_size, expected_size)
    
    def test_file_download(self):
        """Test file download functionality"""
        file_size_mb = 5
        test_file, file_name = self._create_test_file(file_size_mb)
        
        # Upload file
        saved_name = default_storage.save(f"test-uploads/{file_name}", test_file)
        self.test_files_created.append(saved_name)
        
        # Test URL generation
        file_url = default_storage.url(saved_name)
        self.assertTrue(file_url.startswith('http'))
        
        # Test file access
        file_obj = default_storage.open(saved_name, 'rb')
        sample_content = file_obj.read(1024)
        file_obj.close()
        
        self.assertTrue(len(sample_content) > 0)
        self.assertIn(b"This is test content for S3 upload", sample_content)
    
    def test_file_operations(self):
        """Test various file operations"""
        file_size_mb = 5
        test_file, file_name = self._create_test_file(file_size_mb)
        
        # Upload file
        saved_name = default_storage.save(f"test-uploads/{file_name}", test_file)
        self.test_files_created.append(saved_name)
        
        # Test exists
        self.assertTrue(default_storage.exists(saved_name))
        
        # Test size
        file_size = default_storage.size(saved_name)
        expected_size = file_size_mb * 1024 * 1024
        self.assertEqual(file_size, expected_size)
        
        # Test modified time
        try:
            modified_time = default_storage.get_modified_time(saved_name)
            self.assertIsNotNone(modified_time)
        except Exception:
            # Some storage backends may not support this
            pass
        
        # Test delete
        default_storage.delete(saved_name)
        self.assertFalse(default_storage.exists(saved_name))
        
        # Remove from cleanup list since we already deleted it
        if saved_name in self.test_files_created:
            self.test_files_created.remove(saved_name)
    
    def _create_test_file(self, size_mb):
        """Create a test file of specified size"""
        # Create content (simple pattern repeated)
        chunk_size = 1024 * 1024  # 1MB chunks
        content = b"This is test content for S3 upload. " * (chunk_size // 38)  # Fill 1MB
        
        # Create full content
        full_content = content * size_mb
        
        test_file_name = f"test-upload-{size_mb}mb-{int(time.time())}.txt"
        test_file = ContentFile(full_content, name=test_file_name)
        
        return test_file, test_file_name


class S3StorageManualTestCase(TestCase):
    """Manual test cases for S3 storage - these require actual S3 connection"""
    
    def setUp(self):
        """Skip if S3 is not enabled"""
        if not getattr(settings, 'USE_S3', False):
            self.skipTest("S3 not enabled - skipping S3 tests")
    
    def test_s3_connection(self):
        """Test basic S3 connection"""
        try:
            import boto3
            from precapp.storage.backends import LargeFileS3Storage
            
            # Test storage initialization
            storage = LargeFileS3Storage()
            
            # Test bucket access
            files = storage.listdir('')
            self.assertIsInstance(files, tuple)
            
        except Exception as e:
            self.fail(f"S3 connection failed: {str(e)}")
    
    def test_aws_credentials(self):
        """Test AWS credentials or IAM role"""
        try:
            import boto3
            
            session = boto3.Session()
            credentials = session.get_credentials()
            
            self.assertIsNotNone(credentials, "AWS credentials should be available")
            
        except Exception as e:
            self.fail(f"AWS credentials test failed: {str(e)}")


# Utility function for manual testing
def run_s3_upload_test(size_mb=50, cleanup=True, verbose=True):
    """
    Utility function to manually test S3 upload functionality
    Can be used in Django shell: from precapp.tests.test_s3_storage import run_s3_upload_test
    """
    from django.core.files.base import ContentFile
    from django.core.files.storage import default_storage
    import time
    
    if verbose:
        print(f"Testing S3 upload/download with {size_mb}MB file...")
        
        if size_mb > 50:
            print(f"⚠️  Warning: Testing with {size_mb}MB file exceeds the 50MB application limit")
    
    # Create test file
    chunk_size = 1024 * 1024  # 1MB chunks
    content = b"This is test content for S3 upload. " * (chunk_size // 38)  # Fill 1MB
    full_content = content * size_mb
    
    test_file_name = f"test-upload-{size_mb}mb-{int(time.time())}.txt"
    test_file = ContentFile(full_content, name=test_file_name)
    
    if verbose:
        print(f"📁 Created test file: {test_file_name} ({len(full_content):,} bytes)")
    
    try:
        # Test upload
        if verbose:
            print("⬆️  Testing file upload...")
        
        start_time = time.time()
        saved_name = default_storage.save(f"test-uploads/{test_file_name}", test_file)
        upload_time = time.time() - start_time
        
        if verbose:
            print(f"  ✅ Upload completed in {upload_time:.2f} seconds")
            print(f"  📍 File saved as: {saved_name}")
        
        # Test download
        if verbose:
            print("⬇️  Testing file download...")
        
        start_time = time.time()
        file_url = default_storage.url(saved_name)
        file_obj = default_storage.open(saved_name, 'rb')
        sample_content = file_obj.read(1024)
        file_obj.close()
        download_time = time.time() - start_time
        
        if verbose:
            print(f"  ✅ Download test completed in {download_time:.2f} seconds")
            print(f"  🔗 Generated URL: {file_url[:100]}...")
        
        # Test file operations
        if verbose:
            print("🔧 Testing file operations...")
        
        exists = default_storage.exists(saved_name)
        file_size = default_storage.size(saved_name)
        
        if verbose:
            print(f"  📁 File exists: {exists}")
            print(f"  📏 File size: {file_size:,} bytes")
        
        # Cleanup
        if cleanup:
            if verbose:
                print("🧹 Cleaning up test file...")
            default_storage.delete(saved_name)
            if verbose:
                print(f"  ✅ Deleted test file: {saved_name}")
        
        if verbose:
            print(f"✅ All tests passed! S3 is working correctly with {size_mb}MB files.")
        
        return True, saved_name if not cleanup else None
        
    except Exception as e:
        if verbose:
            print(f"❌ Test failed: {str(e)}")
        return False, str(e)
