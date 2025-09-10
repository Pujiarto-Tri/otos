from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import requests
from django.core.files.base import ContentFile
from urllib.parse import urljoin

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
        if not self.use_vercel:
            # Fallback to local storage
            return super()._save(name, content)
        
        # Read content
        content.seek(0)
        file_content = content.read()
        
        try:
            # Use PUT method to upload directly
            url = f'https://blob.vercel-storage.com/{name}'
            headers = {
                'Authorization': f'Bearer {self.token}',
            }
            
            # Detect content type
            import mimetypes
            content_type, _ = mimetypes.guess_type(name)
            if content_type:
                headers['Content-Type'] = content_type
            
            response = requests.put(url, data=file_content, headers=headers)
            
            if response.status_code in [200, 201]:
                try:
                    result = response.json()
                    # Return the public URL as the stored name
                    public_url = result.get('url', url)
                    return public_url
                except Exception:
                    # If no JSON response, assume the URL is the public URL
                    return url
            else:
                print(f"Vercel Blob upload failed: {response.status_code} - {response.text}")
                print("Falling back to local storage")
                # Fallback to local storage
                return super()._save(name, content)
                
        except Exception as e:
            print(f"Error uploading to Vercel Blob: {e}")
            print("Falling back to local storage")
            # Fallback to local storage
            return super()._save(name, content)

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