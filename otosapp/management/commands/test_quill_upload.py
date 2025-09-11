from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image


User = get_user_model()


class Command(BaseCommand):
    help = 'Test QuillJS image upload endpoint'

    def handle(self, *args, **options):
        try:
            # Create test user if needed
            admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                self.stdout.write("❌ No admin user found")
                return
            
            # Create test image
            img = Image.new('RGB', (100, 100), color='blue')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            # Create uploaded file
            uploaded_file = SimpleUploadedFile(
                name='test_quill_image.jpg',
                content=img_io.getvalue(),
                content_type='image/jpeg'
            )
            
            # Test with Django test client
            client = Client()
            client.force_login(admin_user)
            
            self.stdout.write('Testing QuillJS image upload...')
            
            response = client.post('/admin/image-upload/', {
                'upload': uploaded_file
            })
            
            self.stdout.write(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    import json
                    data = json.loads(response.content)
                    self.stdout.write(f"Response data: {data}")
                    
                    if 'url' in data:
                        url = data['url']
                        self.stdout.write(f"✅ Upload successful!")
                        self.stdout.write(f"Image URL: {url}")
                        
                        if url.startswith('http'):
                            self.stdout.write("✅ Vercel Blob URL confirmed")
                        else:
                            self.stdout.write("❌ Local URL (not Vercel Blob)")
                    else:
                        self.stdout.write("❌ No URL in response")
                        
                except Exception as e:
                    self.stdout.write(f"❌ Error parsing response: {e}")
                    self.stdout.write(f"Raw response: {response.content}")
            else:
                self.stdout.write(f"❌ Upload failed with status {response.status_code}")
                self.stdout.write(f"Response: {response.content}")
                
        except Exception as e:
            self.stdout.write(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
