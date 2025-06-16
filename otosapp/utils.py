import os
import uuid
from datetime import datetime

def generate_unique_filename(filename):
    """Generate a unique filename while preserving the original extension."""
    # Get the file extension
    ext = os.path.splitext(filename)[1]
    # Create unique filename with timestamp and UUID
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}{ext}"
    return unique_name