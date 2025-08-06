#!/usr/bin/env python
"""
Test script for profile picture compression functionality
"""
import os
import sys
import django
from io import BytesIO
from PIL import Image
import tempfile

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.utils import compress_image, validate_image_size
from django.core.files.uploadedfile import SimpleUploadedFile

def create_test_image(width, height, format='JPEG', quality=95):
    """Create a test image with specified dimensions"""
    img = Image.new('RGB', (width, height), color='red')
    output = BytesIO()
    img.save(output, format=format, quality=quality)
    size = output.tell()
    output.seek(0)
    return output, size

def test_compression():
    print("=== Testing Profile Picture Compression ===\n")
    
    # Test 1: Large image that needs compression
    print("Test 1: Large image (should be compressed)")
    large_img, large_size = create_test_image(2000, 2000, quality=100)
    print(f"Original size: {large_size / 1024:.1f}KB")
    
    # Create uploaded file
    large_img.seek(0)
    uploaded_file = SimpleUploadedFile(
        name='large_test.jpg',
        content=large_img.read(),
        content_type='image/jpeg'
    )
    
    try:
        # Test validation (should not raise error since we compress automatically)
        validate_image_size(uploaded_file)
        print("Validation: PASSED (within limit)")
    except Exception as e:
        print(f"Validation: File too large ({e}), but will be compressed")
    
    # Test compression
    uploaded_file.seek(0)
    compressed = compress_image(uploaded_file)
    compressed_size = len(compressed.read())
    print(f"Compressed size: {compressed_size / 1024:.1f}KB")
    if large_size > 0:
        print(f"Compression ratio: {(large_size - compressed_size) / large_size * 100:.1f}%")
    print(f"Within 250KB limit: {compressed_size <= 250 * 1024}")
    print()
    
    # Test 2: Small image (should be optimized but not heavily compressed)
    print("Test 2: Small image (should be optimized)")
    small_img, small_size = create_test_image(400, 400, quality=90)
    print(f"Original size: {small_size / 1024:.1f}KB")
    
    small_img.seek(0)
    small_uploaded = SimpleUploadedFile(
        name='small_test.jpg',
        content=small_img.read(),
        content_type='image/jpeg'
    )
    
    try:
        validate_image_size(small_uploaded)
        print("Validation: PASSED")
    except Exception as e:
        print(f"Validation: FAILED ({e})")
    
    small_uploaded.seek(0)
    small_compressed = compress_image(small_uploaded)
    small_compressed_size = len(small_compressed.read())
    print(f"Compressed size: {small_compressed_size / 1024:.1f}KB")
    print(f"Within 250KB limit: {small_compressed_size <= 250 * 1024}")
    print()
    
    # Test 3: PNG with transparency (should be converted to JPEG)
    print("Test 3: PNG with transparency (should be converted to JPEG)")
    png_img = Image.new('RGBA', (800, 600), color=(255, 0, 0, 128))
    png_output = BytesIO()
    png_img.save(png_output, format='PNG')
    png_size = png_output.tell()
    print(f"Original PNG size: {png_size / 1024:.1f}KB")
    
    png_output.seek(0)
    png_uploaded = SimpleUploadedFile(
        name='test.png',
        content=png_output.read(),
        content_type='image/png'
    )
    
    png_uploaded.seek(0)
    png_compressed = compress_image(png_uploaded)
    png_compressed_size = len(png_compressed.read())
    print(f"Compressed JPEG size: {png_compressed_size / 1024:.1f}KB")
    print(f"Converted to JPEG: {png_compressed.name.endswith('.jpg')}")
    print()
    
    print("=== All tests completed ===")

if __name__ == '__main__':
    test_compression()
