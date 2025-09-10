from django.core.management.base import BaseCommand
from otosapp.models import PaymentProof, User
from django.core.files.storage import default_storage
import os


class Command(BaseCommand):
    help = 'Cleanup database references to missing files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('DRY RUN MODE - No changes will be made')
        
        self.stdout.write('=== Cleaning PaymentProof Images ===')
        
        # Check PaymentProof dengan file yang tidak ada
        payment_proofs = PaymentProof.objects.filter(
            proof_image__isnull=False
        ).exclude(
            proof_image__startswith='http'  # Skip Vercel Blob URLs
        ).exclude(
            proof_image=''  # Skip empty strings
        )
        
        cleaned_payments = 0
        for payment in payment_proofs:
            try:
                if not default_storage.exists(payment.proof_image.name):
                    if dry_run:
                        self.stdout.write(f"Would clean PaymentProof #{payment.id}: {payment.proof_image.name}")
                    else:
                        old_file = payment.proof_image.name
                        payment.proof_image = None
                        payment.save()
                        self.stdout.write(f"✅ Cleaned PaymentProof #{payment.id}: {old_file}")
                    cleaned_payments += 1
            except Exception as e:
                self.stdout.write(f"❌ Error checking PaymentProof #{payment.id}: {e}")
        
        self.stdout.write(f"\n=== Cleaning User Profile Pictures ===")
        
        # Check User profile pictures yang tidak ada
        users = User.objects.filter(
            profile_picture__isnull=False
        ).exclude(
            profile_picture__startswith='http'  # Skip Vercel Blob URLs
        ).exclude(
            profile_picture=''  # Skip empty strings
        )
        
        cleaned_users = 0
        for user in users:
            try:
                if not default_storage.exists(user.profile_picture.name):
                    if dry_run:
                        self.stdout.write(f"Would clean User #{user.id} ({user.username}): {user.profile_picture.name}")
                    else:
                        old_file = user.profile_picture.name
                        user.profile_picture = None
                        user.save()
                        self.stdout.write(f"✅ Cleaned User #{user.id} ({user.username}): {old_file}")
                    cleaned_users += 1
            except Exception as e:
                self.stdout.write(f"❌ Error checking User #{user.id}: {e}")
        
        self.stdout.write(f"\n=== Summary ===")
        self.stdout.write(f"PaymentProofs {'would be' if dry_run else ''} cleaned: {cleaned_payments}")
        self.stdout.write(f"Users {'would be' if dry_run else ''} cleaned: {cleaned_users}")
        
        if dry_run:
            self.stdout.write("\n💡 Run without --dry-run to apply changes")
        else:
            self.stdout.write("\n✅ Cleanup complete!")
