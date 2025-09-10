from django import template
from django.conf import settings
import os

register = template.Library()

@register.filter
def fix_media_url(value):
    """
    Fix media URL untuk backward compatibility.
    Jika file path relatif dan tidak ada di storage, return placeholder.
    """
    if not value:
        return ""
    
    # Jika sudah URL lengkap (Vercel Blob), kembalikan apa adanya
    if str(value).startswith('http'):
        return str(value)
    
    # Jika path relatif, cek apakah file ada
    if hasattr(value, 'url'):
        try:
            return value.url
        except:
            # File tidak ada, return placeholder atau URL default
            return "/static/images/placeholder.jpg"  # Atau URL placeholder lainnya
    
    return str(value)

@register.filter
def safe_image_url(image_field):
    """
    Safely get image URL with fallback for missing files.
    """
    if not image_field:
        return "/static/images/no-image.svg"
    
    try:
        # Jika sudah URL lengkap (Vercel Blob)
        if str(image_field).startswith('http'):
            return str(image_field)
        
        # Jika FileField, coba get URL
        if hasattr(image_field, 'url'):
            # Untuk path relatif yang mungkin tidak ada di Vercel
            url = image_field.url
            if url.startswith('/media/'):
                # Jika masih menggunakan /media/ path di production, 
                # kemungkinan file tidak ada - return placeholder
                return "/static/images/no-image.svg"
            return url
        
        # Fallback ke string value
        image_str = str(image_field)
        if image_str.startswith('http'):
            return image_str
        else:
            return "/static/images/no-image.svg"
        
    except Exception:
        # Jika error (file tidak ada), return placeholder
        return "/static/images/no-image.svg"
