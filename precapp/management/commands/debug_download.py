"""
Management command to debug download functionality
Usage: python manage.py debug_download <precatorio_cnj>
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.storage import default_storage
from precapp.models import Precatorio
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug download functionality for a specific precatorio'

    def add_arguments(self, parser):
        parser.add_argument('precatorio_cnj', type=str, help='CNJ of the precatorio to test')

    def handle(self, *args, **options):
        precatorio_cnj = options['precatorio_cnj']
        
        self.stdout.write("=" * 60)
        self.stdout.write(f"🔍 DEBUG DOWNLOAD FOR PRECATORIO: {precatorio_cnj}")
        self.stdout.write("=" * 60)
        
        # Environment info
        self.stdout.write(f"\n🌍 Environment Info:")
        self.stdout.write(f"   Environment: {getattr(settings, 'ENVIRONMENT', 'unknown')}")
        self.stdout.write(f"   USE_S3: {getattr(settings, 'USE_S3', False)}")
        
        if getattr(settings, 'USE_S3', False):
            self.stdout.write(f"   S3 Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'not set')}")
            self.stdout.write(f"   S3 Region: {getattr(settings, 'AWS_S3_REGION_NAME', 'not set')}")
            self.stdout.write(f"   AWS Location: {getattr(settings, 'AWS_LOCATION', 'not set')}")
        
        # Find precatorio
        try:
            precatorio = Precatorio.objects.get(cnj=precatorio_cnj)
            self.stdout.write(f"\n✅ Found precatorio: {precatorio.cnj}")
        except Precatorio.DoesNotExist:
            self.stdout.write(f"\n❌ Precatorio not found: {precatorio_cnj}")
            return
        
        # Check file field
        self.stdout.write(f"\n📁 File Info:")
        if not precatorio.integra_precatorio:
            self.stdout.write("   ❌ No file attached to this precatorio")
            return
        
        self.stdout.write(f"   File field: {precatorio.integra_precatorio}")
        self.stdout.write(f"   File name: {precatorio.integra_precatorio.name}")
        self.stdout.write(f"   Stored filename: {precatorio.integra_precatorio_filename or 'Not set'}")
        
        # Test file operations
        file_name = precatorio.integra_precatorio.name
        
        # Test existence
        try:
            exists = default_storage.exists(file_name)
            self.stdout.write(f"   File exists in storage: {exists}")
            
            if not exists:
                self.stdout.write("   ❌ File not found in storage - this is the main issue!")
                return
        except Exception as e:
            self.stdout.write(f"   ❌ Error checking file existence: {e}")
            return
        
        # Test file size
        try:
            size = default_storage.size(file_name)
            self.stdout.write(f"   File size: {size} bytes ({size/(1024*1024):.2f} MB)")
        except Exception as e:
            self.stdout.write(f"   ❌ Error getting file size: {e}")
        
        # Test URL generation
        try:
            url = default_storage.url(file_name)
            self.stdout.write(f"   Generated URL: {url}")
            
            # Check if URL looks valid
            if 'amazonaws.com' in url and getattr(settings, 'USE_S3', False):
                self.stdout.write("   ✅ URL appears to be valid S3 signed URL")
            elif not getattr(settings, 'USE_S3', False):
                self.stdout.write("   ✅ URL appears to be valid local URL")
            else:
                self.stdout.write("   ⚠️  URL format might be unexpected")
                
        except Exception as e:
            self.stdout.write(f"   ❌ Error generating URL: {e}")
        
        # Test file opening
        try:
            with default_storage.open(file_name, 'rb') as f:
                first_bytes = f.read(100)
                self.stdout.write(f"   ✅ Can open file: {len(first_bytes)} bytes read")
                
                # Check if it looks like a PDF
                if first_bytes.startswith(b'%PDF'):
                    self.stdout.write("   ✅ File appears to be a valid PDF")
                else:
                    self.stdout.write(f"   ⚠️  File doesn't appear to be PDF (starts with: {first_bytes[:20]})")
                    
        except Exception as e:
            self.stdout.write(f"   ❌ Error opening file: {e}")
            if "Access Denied" in str(e):
                self.stdout.write("       This suggests an AWS permissions issue")
        
        # Test download simulation
        self.stdout.write(f"\n🔄 Simulating Download:")
        try:
            from precapp.views import stream_s3_file_direct
            
            # Determine filename
            if precatorio.integra_precatorio_filename:
                filename = precatorio.integra_precatorio_filename
            else:
                filename = f"precatorio_{precatorio.cnj.replace('/', '_')}.pdf"
            
            self.stdout.write(f"   Download filename: {filename}")
            
            if getattr(settings, 'USE_S3', False):
                self.stdout.write("   Attempting S3 stream simulation...")
                # This would normally return a StreamingHttpResponse
                # We'll just test the file opening part
                file_obj = default_storage.open(file_name, 'rb')
                chunk = file_obj.read(1024)  # Read first 1KB
                file_obj.close()
                self.stdout.write(f"   ✅ Stream simulation successful: {len(chunk)} bytes")
            else:
                self.stdout.write("   Local file download would work")
                
        except Exception as e:
            self.stdout.write(f"   ❌ Download simulation failed: {e}")
            import traceback
            self.stdout.write(f"   Full error: {traceback.format_exc()}")
        
        # Recommendations
        self.stdout.write(f"\n💡 Recommendations:")
        
        if not getattr(settings, 'USE_S3', False):
            self.stdout.write("   - S3 is disabled, file should download locally")
        else:
            self.stdout.write("   - Check AWS credentials are correctly set")
            self.stdout.write("   - Verify S3 bucket permissions allow file access")
            self.stdout.write("   - Confirm file was uploaded to the correct S3 location")
            self.stdout.write("   - Check if S3 bucket policy allows the current AWS user to access files")
        
        self.stdout.write("\n✅ Debug completed!")
