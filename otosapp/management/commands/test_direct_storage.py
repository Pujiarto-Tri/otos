from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from otosapp.storage import VercelBlobStorage


class Command(BaseCommand):
    help = 'Test direct storage upload'

    def handle(self, *args, **options):
        self.stdout.write('=== Direct Storage Test ===')
        
        # Test default_storage
        self.stdout.write(f"default_storage type: {type(default_storage)}")
        
        # Test VercelBlobStorage directly
        vercel_storage = VercelBlobStorage()
        self.stdout.write(f"VercelBlobStorage.use_vercel: {vercel_storage.use_vercel}")
        
        # Test upload dengan VercelBlobStorage langsung
        try:
            test_content = ContentFile(b"Test direct upload", name="direct_test.txt")
            filename = vercel_storage.save("test_uploads/direct_test.txt", test_content)
            url = vercel_storage.url(filename)
            
            self.stdout.write(f"✅ Direct VercelBlobStorage upload successful:")
            self.stdout.write(f"  Filename: {filename}")
            self.stdout.write(f"  URL: {url}")
            
            if url.startswith('http'):
                self.stdout.write("✅ Vercel Blob URL confirmed")
            else:
                self.stdout.write("❌ Local URL")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test default_storage
        try:
            test_content2 = ContentFile(b"Test default storage", name="default_test.txt")
            filename2 = default_storage.save("test_uploads/default_test.txt", test_content2)
            url2 = default_storage.url(filename2)
            
            self.stdout.write(f"\n✅ default_storage upload:")
            self.stdout.write(f"  Filename: {filename2}")
            self.stdout.write(f"  URL: {url2}")
            
            if url2.startswith('http'):
                self.stdout.write("✅ Vercel Blob URL")
            else:
                self.stdout.write("❌ Local URL")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
