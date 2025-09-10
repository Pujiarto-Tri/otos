from django.core.management.base import BaseCommand
from django.conf import settings
from otosapp.models import PaymentProof
import os


class Command(BaseCommand):
    help = 'Test upload file baru untuk verifikasi Vercel Blob di production'

    def handle(self, *args, **options):
        self.stdout.write('=== Testing Vercel Blob Upload ===')
        
        # Environment check
        self.stdout.write(f"VERCEL: {os.environ.get('VERCEL', 'Not set')}")
        self.stdout.write(f"VERCEL_URL: {os.environ.get('VERCEL_URL', 'Not set')}")
        self.stdout.write(f"BLOB_READ_WRITE_TOKEN: {'Set' if os.environ.get('BLOB_READ_WRITE_TOKEN') else 'Not set'}")
        self.stdout.write(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
        
        # Test storage
        try:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            from otosapp.storage import VercelBlobStorage
            
            # Test dengan storage langsung
            storage = VercelBlobStorage()
            self.stdout.write(f"VercelBlobStorage.use_vercel: {storage.use_vercel}")
            
            if storage.use_vercel:
                # Test upload
                test_content = ContentFile(b"Test upload from production", name="test.txt")
                filename = storage.save("test_uploads/production_test.txt", test_content)
                self.stdout.write(f"✅ Upload successful: {filename}")
                
                # Test URL
                url = storage.url(filename)
                self.stdout.write(f"✅ URL generated: {url}")
                
                if filename.startswith('http'):
                    self.stdout.write("✅ File uploaded to Vercel Blob successfully!")
                else:
                    self.stdout.write("❌ File uploaded to local storage (not Vercel Blob)")
            else:
                self.stdout.write("❌ Vercel Blob not configured properly")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Check existing PaymentProof dengan masalah
        self.stdout.write('\n=== Checking Existing PaymentProofs ===')
        problem_proofs = PaymentProof.objects.filter(
            proof_image__isnull=False
        ).exclude(
            proof_image__startswith='http'
        )[:5]
        
        self.stdout.write(f"Found {problem_proofs.count()} PaymentProofs with local paths")
        for proof in problem_proofs:
            self.stdout.write(f"  ID {proof.id}: {proof.proof_image.name}")
        
        if problem_proofs.exists():
            self.stdout.write("\n💡 To fix these, run:")
            self.stdout.write("python manage.py migrate_to_vercel_blob --dry-run")
            self.stdout.write("python manage.py migrate_to_vercel_blob")
