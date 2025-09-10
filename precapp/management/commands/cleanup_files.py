"""
Clean up orphaned files in S3 storage
"""

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from precapp.models import Precatorio
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up orphaned files in storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--path',
            type=str,
            default='precatorios/integras/',
            help='Path to clean up (default: precatorios/integras/)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        path = options['path']
        
        self.stdout.write(f"🔍 Scanning path: {path}")
        self.stdout.write(f"🧪 Dry run: {dry_run}")
        
        # Get all file paths from database
        db_files = set()
        for precatorio in Precatorio.objects.exclude(integra_precatorio=''):
            if precatorio.integra_precatorio:
                db_files.add(precatorio.integra_precatorio.name)
        
        self.stdout.write(f"📊 Found {len(db_files)} files in database")
        
        # List all files in storage
        try:
            storage_files = []
            self._list_files_recursive(path, storage_files)
            
            self.stdout.write(f"📊 Found {len(storage_files)} files in storage")
            
            # Find orphaned files
            orphaned_files = []
            for storage_file in storage_files:
                if storage_file not in db_files:
                    orphaned_files.append(storage_file)
            
            self.stdout.write(f"🗑️  Found {len(orphaned_files)} orphaned files")
            
            # Delete or show orphaned files
            total_size = 0
            for orphaned_file in orphaned_files:
                try:
                    size = default_storage.size(orphaned_file)
                    total_size += size
                    
                    if dry_run:
                        self.stdout.write(f"Would delete: {orphaned_file} ({size} bytes)")
                    else:
                        default_storage.delete(orphaned_file)
                        self.stdout.write(f"Deleted: {orphaned_file} ({size} bytes)")
                        
                except Exception as e:
                    self.stdout.write(f"❌ Error processing {orphaned_file}: {e}")
            
            self.stdout.write(f"💾 Total size: {total_size / (1024*1024):.2f} MB")
            
            if dry_run:
                self.stdout.write("🧪 This was a dry run. Use --no-dry-run to actually delete files.")
            else:
                self.stdout.write("✅ Cleanup completed!")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
    
    def _list_files_recursive(self, path, file_list):
        """Recursively list all files in a path"""
        try:
            dirs, files = default_storage.listdir(path)
            
            # Add files from current directory
            for file in files:
                full_path = f"{path}/{file}".replace('//', '/')
                file_list.append(full_path)
            
            # Recursively process subdirectories
            for dir_name in dirs:
                sub_path = f"{path}/{dir_name}".replace('//', '/')
                self._list_files_recursive(sub_path, file_list)
                
        except Exception as e:
            # If we can't list the directory, just skip it
            pass
