from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from otosapp.models import SubscriptionPackage, PaymentProof
from django.core.files.base import ContentFile
from django.utils import timezone
import io
from PIL import Image


User = get_user_model()


class Command(BaseCommand):
    help = 'Test upload payment proof to Vercel Blob'

    def handle(self, *args, **options):
        try:
            # Cari user student
            student = User.objects.filter(role__role_name='Student').first()
            if not student:
                student = User.objects.first()
            
            # Cari package
            package = SubscriptionPackage.objects.filter(is_active=True).first()
            if not package:
                self.stdout.write("❌ No active package found")
                return
            
            self.stdout.write(f"Creating test payment for user: {student.username}")
            self.stdout.write(f"Package: {package.name}")
            
            # Buat gambar dummy
            img = Image.new('RGB', (300, 200), color='red')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            # Create ContentFile
            image_file = ContentFile(img_io.getvalue(), name='test_payment_proof.jpg')
            
            # Buat PaymentProof
            payment = PaymentProof.objects.create(
                user=student,
                package=package,
                amount_paid=package.price,
                payment_method='Test Upload',
                payment_date=timezone.now(),
                proof_image=image_file,
                notes='Test upload to Vercel Blob'
            )
            
            self.stdout.write(f"✅ PaymentProof created with ID: {payment.id}")
            self.stdout.write(f"Image name: {payment.proof_image.name}")
            self.stdout.write(f"Image URL: {payment.proof_image.url}")
            
            if payment.proof_image.url.startswith('http'):
                self.stdout.write("✅ Successfully uploaded to Vercel Blob!")
            else:
                self.stdout.write("❌ Still using local storage")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
