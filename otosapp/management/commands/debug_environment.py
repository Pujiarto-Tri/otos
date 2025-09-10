from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Debug environment and storage configuration'

    def handle(self, *args, **options):
        self.stdout.write('=== Environment Debug ===')
        
        # Environment variables
        env_vars = [
            'VERCEL',
            'VERCEL_URL', 
            'BLOB_READ_WRITE_TOKEN',
            'VERCEL_BLOB_TOKEN',
            'DEBUG',
            'DEFAULT_FILE_STORAGE'
        ]
        
        for var in env_vars:
            value = os.environ.get(var, '(not set)')
            if 'TOKEN' in var and value != '(not set)':
                # Mask token for security
                value = f"{value[:10]}...{value[-10:]}"
            self.stdout.write(f"{var}: {value}")
        
        self.stdout.write('\n=== Django Settings ===')
        settings_to_check = [
            'DEFAULT_FILE_STORAGE',
            'MEDIA_URL', 
            'MEDIA_ROOT',
            'DEBUG',
        ]
        
        for setting in settings_to_check:
            value = getattr(settings, setting, '(not set)')
            self.stdout.write(f"{setting}: {value}")
        
        # Test storage
        self.stdout.write('\n=== Storage Test ===')
        try:
            from django.core.files.storage import default_storage
            from otosapp.storage import VercelBlobStorage
            
            self.stdout.write(f"default_storage type: {type(default_storage)}")
            
            # Test Vercel storage directly
            vercel_storage = VercelBlobStorage()
            self.stdout.write(f"VercelBlobStorage.use_vercel: {vercel_storage.use_vercel}")
            if vercel_storage.token:
                self.stdout.write(f"Token available: {vercel_storage.token[:10]}...{vercel_storage.token[-5:]}")
            
        except Exception as e:
            self.stdout.write(f"Storage test error: {e}")
        
        self.stdout.write('\n=== Recommendations ===')
        
        # Check if running on Vercel
        if os.environ.get('VERCEL'):
            self.stdout.write('✅ Running on Vercel')
            
            # Check if blob token exists
            if os.environ.get('BLOB_READ_WRITE_TOKEN'):
                self.stdout.write('✅ BLOB_READ_WRITE_TOKEN is set')
            else:
                self.stdout.write('❌ BLOB_READ_WRITE_TOKEN is missing!')
                self.stdout.write('   Add environment variable in Vercel Dashboard:')
                self.stdout.write('   BLOB_READ_WRITE_TOKEN=vercel_blob_rw_...')
        else:
            self.stdout.write('💻 Running locally')
            self.stdout.write('   Make sure .env file contains BLOB_READ_WRITE_TOKEN')
