"""
Django management command to validate storage configuration
Usage: python manage.py validate_storage
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from precapp.storage.config import validate_s3_configuration, get_s3_config, get_upload_limits


class Command(BaseCommand):
    help = 'Validate storage configuration and settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-config',
            action='store_true',
            help='Show detailed configuration values'
        )

    def handle(self, *args, **options):
        show_config = options['show_config']
        
        self.stdout.write("🔍 Validating storage configuration...")
        
        # Validate S3 configuration
        is_valid, errors = validate_s3_configuration()
        
        if is_valid:
            self.stdout.write(
                self.style.SUCCESS("✅ Storage configuration is valid!")
            )
        else:
            self.stdout.write(
                self.style.ERROR("❌ Storage configuration has errors:")
            )
            for error in errors:
                self.stdout.write(f"  • {error}")
        
        # Show basic configuration
        self.stdout.write("\n📊 Current Configuration:")
        self.stdout.write(f"  USE_S3: {getattr(settings, 'USE_S3', False)}")
        self.stdout.write(f"  ENVIRONMENT: {getattr(settings, 'ENVIRONMENT', 'Not set')}")
        self.stdout.write(f"  DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
        
        # Show detailed configuration if requested
        if show_config:
            self.show_detailed_config()
        
        # Show recommendations
        self.show_recommendations()

    def show_detailed_config(self):
        """Show detailed configuration values"""
        self.stdout.write("\n🔧 Detailed Configuration:")
        
        # S3 Configuration
        if getattr(settings, 'USE_S3', False):
            s3_config = get_s3_config()
            self.stdout.write("  S3 Settings:")
            self.stdout.write(f"    Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not set')}")
            self.stdout.write(f"    Region: {getattr(settings, 'AWS_S3_REGION_NAME', 'Not set')}")
            self.stdout.write(f"    Location: {getattr(settings, 'AWS_LOCATION', 'Not set')}")
            self.stdout.write(f"    Multipart Threshold: {s3_config['multipart_threshold'] / (1024*1024):.1f}MB")
            self.stdout.write(f"    Chunk Size: {s3_config['multipart_chunksize'] / (1024*1024):.1f}MB")
            self.stdout.write(f"    Max Concurrency: {s3_config['max_concurrency']}")
            self.stdout.write(f"    Signed URLs: {s3_config['querystring_auth']}")
            self.stdout.write(f"    URL Expiration: {s3_config['querystring_expire']}s")
        
        # Upload Limits
        limits = get_upload_limits()
        self.stdout.write("  Upload Limits:")
        self.stdout.write(f"    Max File Size: {limits['max_size_mb']}MB")
        self.stdout.write(f"    Session Timeout: {limits['session_timeout']}s")

    def show_recommendations(self):
        """Show configuration recommendations"""
        self.stdout.write("\n💡 Recommendations:")
        
        # Check upload limits
        limits = get_upload_limits()
        if limits['max_size_mb'] > 50:
            self.stdout.write(
                self.style.WARNING(f"  ⚠️  File size limit ({limits['max_size_mb']}MB) is high - consider 50MB max")
            )
        
        # Check S3 configuration
        if getattr(settings, 'USE_S3', False):
            s3_config = get_s3_config()
            
            if s3_config['multipart_threshold'] > 50 * 1024 * 1024:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  Multipart threshold is very high - consider 25MB")
                )
            
            if not s3_config['querystring_auth']:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  Signed URLs disabled - files will be publicly accessible")
                )
            
            if s3_config['querystring_expire'] > 7200:
                self.stdout.write(
                    self.style.WARNING("  ⚠️  URL expiration is long - consider shorter times for security")
                )
        
        # Environment-specific recommendations
        environment = getattr(settings, 'ENVIRONMENT', 'local')
        if environment == 'production':
            if getattr(settings, 'DEBUG', True):
                self.stdout.write(
                    self.style.ERROR("  ❌ DEBUG should be False in production")
                )
            
            if not getattr(settings, 'USE_S3', False):
                self.stdout.write(
                    self.style.WARNING("  ⚠️  Consider using S3 for production file storage")
                )
        
        self.stdout.write("  ✅ Use unit tests: 'python manage.py test precapp.tests.test_s3_storage' for comprehensive testing")
        self.stdout.write("  ✅ Use 'python manage.py test precapp.tests.test_s3_storage' for unit tests")
