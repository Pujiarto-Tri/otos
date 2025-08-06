#!/usr/bin/env python
"""
Test script for extreme large image compression
"""
import os
import sys
import django
from io import BytesIO
from PIL import Image

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.utils import compress_image
from django.core.files.uploadedfile import SimpleUploadedFile

def test_extreme_compression():
    print("=== Testing Extreme Image Compression ===\n")
    
    # Create a very large, high-quality image
    print("Creating very large image (4000x3000, max quality)...")
    img = Image.new('RGB', (4000, 3000), color='blue')
    
    # Add some complexity to make it realistic
    for x in range(0, 4000, 100):
        for y in range(0, 3000, 100):
            # Create random colored squares
            color = (x % 255, y % 255, (x + y) % 255)
            for i in range(x, min(x + 50, 4000)):
                for j in range(y, min(y + 50, 3000)):
                    img.putpixel((i, j), color)
    
    output = BytesIO()
    img.save(output, format='JPEG', quality=100)
    large_size = output.tell()
    print(f"Original size: {large_size / 1024:.1f}KB ({large_size / (1024*1024):.1f}MB)")
    
    # Create uploaded file
    output.seek(0)
    uploaded_file = SimpleUploadedFile(
        name='extreme_test.jpg',
        content=output.read(),
        content_type='image/jpeg'
    )
    
    # Test compression
    print("Compressing image...")
    compressed = compress_image(uploaded_file, max_size_kb=250)
    compressed_size = len(compressed.read())
    
    print(f"Compressed size: {compressed_size / 1024:.1f}KB")
    print(f"Compression ratio: {(large_size - compressed_size) / large_size * 100:.1f}%")
    print(f"Within 250KB limit: {compressed_size <= 250 * 1024}")
    print(f"Size reduction: {large_size / compressed_size:.1f}x smaller")
    
    print("\n=== Extreme compression test completed ===")

if __name__ == '__main__':
    test_extreme_compression()
