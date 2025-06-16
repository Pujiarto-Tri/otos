from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os

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