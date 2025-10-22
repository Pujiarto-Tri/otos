from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import requests
from django.core.files.base import ContentFile
from urllib.parse import urljoin
from io import BytesIO
from pathlib import PurePosixPath

import mimetypes

try:
    from PIL import Image, ImageOps, UnidentifiedImageError
except ImportError:  # Pillow is optional until installed
    Image = None
    ImageOps = None
    UnidentifiedImageError = Exception

class UniqueFileSystemStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            # If a file with the name already exists, 
            # call the filename generator to get a new name
            filename_generator = settings.CKEDITOR_5_FILENAME_GENERATOR
            if filename_generator:
                module_path, function_name = filename_generator.rsplit('.', 1)
                module = __import__(module_path, fromlist=[function_name])
                generator_function = getattr(module, function_name)
                name = generator_function(name)
        return name


class VercelBlobStorage(FileSystemStorage):
    """Django storage backend for Vercel Blob with local fallback."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Try BLOB_READ_WRITE_TOKEN first (official env var), then VERCEL_BLOB_TOKEN as fallback
        self.token = os.environ.get('BLOB_READ_WRITE_TOKEN') or os.environ.get('VERCEL_BLOB_TOKEN')
        self.use_vercel = bool(self.token and len(self.token) > 30)  # Basic token validation
        
        if not self.use_vercel:
            print("Warning: Vercel Blob token not found or invalid, falling back to local storage")

    def _save(self, name, content):
        """Save file to Vercel Blob or fall back to local storage."""
        name = name.replace('\\', '/')
        optimized_name, file_bytes, content_type = self._prepare_upload(name, content)

        if not self.use_vercel:
            # Fallback to local storage with optimized content
            django_file = ContentFile(file_bytes)
            django_file.name = PurePosixPath(optimized_name).name
            return super()._save(optimized_name, django_file)

        try:
            url = f'https://blob.vercel-storage.com/{optimized_name}'
            headers = {
                'Authorization': f'Bearer {self.token}',
            }

            if content_type:
                headers['Content-Type'] = content_type

            response = requests.put(url, data=file_bytes, headers=headers)

            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    public_url = result.get('url', url)
                    return public_url
                except Exception:
                    return url

            # Fallback to local storage on non-success response
            django_file = ContentFile(file_bytes)
            django_file.name = PurePosixPath(optimized_name).name
            return super()._save(optimized_name, django_file)

        except Exception:
            # Fallback to local storage
            django_file = ContentFile(file_bytes)
            django_file.name = PurePosixPath(optimized_name).name
            return super()._save(optimized_name, django_file)

    def _prepare_upload(self, name, content):
        """Optimize file bytes before upload; returns (name, bytes, content_type)."""
        name = name.replace('\\', '/')
        content.seek(0)
        raw_bytes = content.read()

        if not raw_bytes:
            return name, raw_bytes, mimetypes.guess_type(name)[0]

        if not Image:
            content.seek(0)
            return name, raw_bytes, mimetypes.guess_type(name)[0]

        if not self._should_optimize(name):
            content.seek(0)
            return name, raw_bytes, mimetypes.guess_type(name)[0]

        try:
            with Image.open(BytesIO(raw_bytes)) as img:
                if getattr(img, "is_animated", False):
                    return name, raw_bytes, mimetypes.guess_type(name)[0]

                max_size = getattr(settings, 'UPLOAD_IMAGE_MAX_SIZE', 1920)
                quality = getattr(settings, 'UPLOAD_IMAGE_WEBP_QUALITY', 80)

                # Normalize orientation and color mode
                img = self._normalize_image(img)

                resampling_enum = getattr(Image, 'Resampling', None)
                resample_filter = getattr(resampling_enum, 'LANCZOS', getattr(Image, 'LANCZOS', Image.BICUBIC))

                img.thumbnail((max_size, max_size), resample=resample_filter)

                buffer = BytesIO()
                img.save(buffer, format='WEBP', quality=quality, method=6)
                buffer.seek(0)

                optimized_name = str(PurePosixPath(name).with_suffix('.webp'))
                return optimized_name, buffer.read(), 'image/webp'

        except (UnidentifiedImageError, OSError):
            pass

        finally:
            content.seek(0)

        return name, raw_bytes, mimetypes.guess_type(name)[0]

    def _should_optimize(self, name):
        extension = PurePosixPath(name).suffix.lower()
        if extension in {'.webp', '.gif'}:
            return False
        return extension in {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}

    def _normalize_image(self, img):
        if ImageOps is not None:
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        return img

    def url(self, name):
        """Return the URL for the file."""
        if not name:
            return ''
        # If name is already a full URL (from Vercel Blob), return it
        if name.startswith('http'):
            return name
        # Otherwise use default behavior
        return super().url(name)

    def exists(self, name):
        """Check if file exists."""
        if name and name.startswith('http'):
            # For Vercel URLs, try a HEAD request
            try:
                response = requests.head(name, timeout=5)
                return response.status_code == 200
            except:
                return True  # Assume it exists if we can't check
        return super().exists(name)

    def path(self, name):
        """For URLs, return the name itself."""
        if name and name.startswith('http'):
            return name
        return super().path(name)

    def delete(self, name):
        """Delete file."""
        if name and name.startswith('http'):
            # For Vercel URLs, we could implement delete API call here
            # For now, just log that it can't be deleted
            print(f"Cannot delete Vercel Blob file: {name}")
            return
        return super().delete(name)