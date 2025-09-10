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
    """A minimal Django storage backend that uploads files to Vercel Blob via its API.

    This implementation is intentionally small: it uploads the file bytes to
    Vercel Blob using a POST to create an upload, then a PUT to the returned
    upload URL. It stores the returned `url` (public URL) as the file's name/path.
    """

    def __init__(self, *args, **kwargs):
        # keep local tmp storage for temp saves
        super().__init__(*args, **kwargs)
        self.token = os.environ.get('VERCEL_BLOB_TOKEN')
        self.api_base = 'https://api.vercel.com/v1/blob'

    def _get_upload_create(self, name):
        """Call Vercel to create an upload session. Returns JSON."""
        if not self.token:
            raise RuntimeError('VERCEL_BLOB_TOKEN not set')
        endpoint = f'{self.api_base}/uploads'
        headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}
        resp = requests.post(endpoint, headers=headers, json={'name': name})
        resp.raise_for_status()
        return resp.json()

    def _upload_bytes(self, upload_info, content_bytes):
        # upload_info expected to contain 'uploadURL' or similar keys returned by Vercel
        upload_url = upload_info.get('uploadURL') or upload_info.get('url') or upload_info.get('upload_url')
        if not upload_url:
            raise RuntimeError('Vercel upload URL not found in response')
        # PUT the bytes directly to the upload URL
        put_resp = requests.put(upload_url, data=content_bytes)
        put_resp.raise_for_status()
        return put_resp

    def _save(self, name, content):
        # content may be a File-like object
        content.seek(0)
        data = content.read()
        if hasattr(data, 'read'):
            data = data.read()
        # create upload session
        info = self._get_upload_create(name)
        # send bytes
        self._upload_bytes(info, data)
        # Vercel returns a public url (try multiple keys)
        public_url = info.get('url') or info.get('fileUrl') or info.get('cdnUrl')
        # Fallback: if no public_url, use a placeholder path using returned id
        if not public_url:
            public_url = urljoin('https://vercel.storage/', info.get('id', name))

        # We return the storage name. To keep Django FileField behaviour, return a path-like string
        return public_url