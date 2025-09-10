"""
Debug command to investigate file issues with precatorios
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from precapp.models import Precatorio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Debug file issues with precatorios'

    def add_arguments(self, parser):
        parser.add_argument(
            'cnj',
            type=str,
            help='CNJ of the precatorio to debug'
        )

    def handle(self, *args, **options):
        cnj = options['cnj']
        
        try:
            # Get the precatorio
            precatorio = Precatorio.objects.get(cnj=cnj)
            
            self.stdout.write(f"🔍 Debugging precatorio: {cnj}")
            self.stdout.write(f"📁 Current file field: {precatorio.integra_precatorio}")
            
            if precatorio.integra_precatorio:
                file_name = precatorio.integra_precatorio.name
                self.stdout.write(f"📄 File name: {file_name}")
                
                # Check if file exists in storage
                exists = default_storage.exists(file_name)
                self.stdout.write(f"✅ File exists in storage: {exists}")
                
                if exists:
                    # Get file size
                    try:
                        size = default_storage.size(file_name)
                        self.stdout.write(f"📊 File size: {size} bytes ({size / (1024*1024):.2f} MB)")
                    except Exception as e:
                        self.stdout.write(f"❌ Error getting file size: {e}")
                    
                    # Get file URL
                    try:
                        url = default_storage.url(file_name)
                        self.stdout.write(f"🔗 File URL: {url}")
                    except Exception as e:
                        self.stdout.write(f"❌ Error getting file URL: {e}")
                        
                    # Get modified time
                    try:
                        modified_time = default_storage.get_modified_time(file_name)
                        self.stdout.write(f"🕐 Modified time: {modified_time}")
                    except Exception as e:
                        self.stdout.write(f"❌ Error getting modified time: {e}")
                else:
                    self.stdout.write("❌ File does not exist in storage!")
                    
                # List all files in the directory
                import os
                dir_path = os.path.dirname(file_name)
                if dir_path:
                    self.stdout.write(f"📂 Files in directory {dir_path}:")
                    try:
                        dirs, files = default_storage.listdir(dir_path)
                        for file in files:
                            full_path = os.path.join(dir_path, file).replace('\\', '/')
                            size = default_storage.size(full_path)
                            self.stdout.write(f"   📄 {file} ({size} bytes)")
                    except Exception as e:
                        self.stdout.write(f"❌ Error listing directory: {e}")
            else:
                self.stdout.write("❌ No file associated with this precatorio")
                
        except Precatorio.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Precatorio with CNJ {cnj} not found"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
