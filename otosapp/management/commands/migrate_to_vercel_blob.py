from django.core.management.base import BaseCommand
from django.conf import settings
from otosapp.models import PaymentProof, User
from otosapp.storage import VercelBlobStorage
from django.core.files.base import ContentFile
import os
import requests


class Command(BaseCommand):
    help = 'Migrate existing images from local paths to Vercel Blob'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be migrated without actually doing it')
        parser.add_argument('--limit', type=int, default=50, help='Limit number of objects to migrate')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        limit = options.get('limit', 50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(f'Current storage: {getattr(settings, "DEFAULT_FILE_STORAGE", "(not set)")}')
        
        # Initialize Vercel Blob storage
        vercel_storage = VercelBlobStorage()
        if not vercel_storage.use_vercel:
            self.stdout.write(self.style.ERROR('Vercel Blob not available. Make sure BLOB_READ_WRITE_TOKEN is set.'))
            return
        
        # Migrate PaymentProof images
        self.migrate_payment_proofs(vercel_storage, dry_run, limit)
        
        # Migrate User profile pictures
        self.migrate_user_profiles(vercel_storage, dry_run, limit)

    def migrate_payment_proofs(self, storage, dry_run, limit):
        self.stdout.write('\n=== Migrating PaymentProof Images ===')
        
        # Find PaymentProofs with local image paths
        proofs = PaymentProof.objects.filter(
            proof_image__isnull=False
        ).exclude(
            proof_image__startswith='http'
        )[:limit]
        
        self.stdout.write(f'Found {proofs.count()} PaymentProof objects to migrate')
        
        for proof in proofs:
            try:
                old_path = proof.proof_image.name
                self.stdout.write(f'Migrating PaymentProof #{proof.id}: {old_path}')
                
                if dry_run:
                    self.stdout.write(f'  -> Would migrate to Vercel Blob')
                    continue
                
                # Check if local file exists
                local_path = os.path.join(settings.MEDIA_ROOT, old_path)
                if not os.path.exists(local_path):
                    self.stdout.write(f'  -> ❌ Local file not found: {local_path}')
                    continue
                
                # Read local file
                with open(local_path, 'rb') as f:
                    file_content = f.read()
                
                # Create ContentFile
                content_file = ContentFile(file_content, name=os.path.basename(old_path))
                
                # Upload to Vercel Blob
                new_name = storage.save(old_path, content_file)
                
                # Update the model
                proof.proof_image.name = new_name
                proof.save(update_fields=['proof_image'])
                
                self.stdout.write(f'  -> ✅ Migrated to: {new_name}')
                
            except Exception as e:
                self.stdout.write(f'  -> ❌ Error: {e}')

    def migrate_user_profiles(self, storage, dry_run, limit):
        self.stdout.write('\n=== Migrating User Profile Pictures ===')
        
        # Find Users with local profile pictures
        users = User.objects.filter(
            profile_picture__isnull=False
        ).exclude(
            profile_picture__startswith='http'
        )[:limit]
        
        self.stdout.write(f'Found {users.count()} User objects to migrate')
        
        for user in users:
            try:
                old_path = user.profile_picture.name
                self.stdout.write(f'Migrating User #{user.id}: {old_path}')
                
                if dry_run:
                    self.stdout.write(f'  -> Would migrate to Vercel Blob')
                    continue
                
                # Check if local file exists
                local_path = os.path.join(settings.MEDIA_ROOT, old_path)
                if not os.path.exists(local_path):
                    self.stdout.write(f'  -> ❌ Local file not found: {local_path}')
                    continue
                
                # Read local file
                with open(local_path, 'rb') as f:
                    file_content = f.read()
                
                # Create ContentFile
                content_file = ContentFile(file_content, name=os.path.basename(old_path))
                
                # Upload to Vercel Blob
                new_name = storage.save(old_path, content_file)
                
                # Update the model
                user.profile_picture.name = new_name
                user.save(update_fields=['profile_picture'])
                
                self.stdout.write(f'  -> ✅ Migrated to: {new_name}')
                
            except Exception as e:
                self.stdout.write(f'  -> ❌ Error: {e}')
