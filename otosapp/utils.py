import os
import uuid
from datetime import datetime
from PIL import Image, ImageOps
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

def generate_unique_filename(filename):
    """Generate a unique filename while preserving the original extension."""
    # Get the file extension
    ext = os.path.splitext(filename)[1]
    # Create unique filename with timestamp and UUID
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}{ext}"
    return unique_name

def validate_image_size(image):
    """Validate image file size (max 250KB)"""
    max_size = 250 * 1024  # 250KB in bytes
    if image.size > max_size:
        raise ValidationError(f'Ukuran file terlalu besar. Maksimal {max_size // 1024}KB.')

def compress_image(image, max_size_kb=250, quality_start=90):
    """
    Compress image while maintaining quality.
    
    Args:
        image: Django UploadedFile object
        max_size_kb: Maximum file size in KB (default: 250KB)
        quality_start: Starting quality for compression (default: 90)
    
    Returns:
        ContentFile: Compressed image as Django ContentFile
    """
    max_size_bytes = max_size_kb * 1024
    
    # Open the image
    img = Image.open(image)
    
    # Convert RGBA to RGB if necessary (for JPEG compatibility)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create a white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Auto-orient the image based on EXIF data
    img = ImageOps.exif_transpose(img)
    
    # Resize image if it's too large (maintain aspect ratio)
    max_dimension = 1024
    if img.width > max_dimension or img.height > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    
    # Start with the initial quality and reduce until file size is acceptable
    quality = quality_start
    min_quality = 30
    
    while quality >= min_quality:
        # Save image to BytesIO with current quality
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Check file size
        if output.tell() <= max_size_bytes:
            break
            
        # Reduce quality for next iteration
        quality -= 10
        output.seek(0)
    
    # If still too large even at minimum quality, resize further
    if output.tell() > max_size_bytes and quality < min_quality:
        # Reduce dimensions more aggressively
        scale_factor = 0.8
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)
        
        while output.tell() > max_size_bytes and new_width > 100 and new_height > 100:
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            output = BytesIO()
            img_resized.save(output, format='JPEG', quality=min_quality, optimize=True)
            output.seek(0)
            
            if output.tell() <= max_size_bytes:
                break
                
            new_width = int(new_width * scale_factor)
            new_height = int(new_height * scale_factor)
    
    # Create ContentFile from compressed image
    output.seek(0)
    compressed_image = ContentFile(output.read())
    
    # Generate unique filename
    original_name = getattr(image, 'name', 'profile_picture.jpg')
    base_name = os.path.splitext(original_name)[0]
    compressed_image.name = f"{base_name}_compressed_{uuid.uuid4().hex[:8]}.jpg"
    
    return compressed_image