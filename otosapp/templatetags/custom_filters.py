from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_choice_image(dictionary, choice_number):
    """Get choice image URL by choice number"""
    if not dictionary:
        return ''
    key = f'choice_image_{choice_number}'
    return dictionary.get(key, '')


@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Divide value by arg"""
    try:
        if float(arg) != 0:
            return float(value) / float(arg)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Add arg to value (numeric if possible, else concatenate as string)"""
    try:
        return int(float(value)) + int(float(arg))
    except (ValueError, TypeError):
        try:
            # If either value or arg is not a number, concatenate as string
            return str(value) + str(arg)
        except Exception:
            return value
    

@register.filter
def range_filter(value):
    """Return a range from 1 to value+1"""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(0)

@register.filter
def smart_float(value):
    """Format float: hide .0 if integer, show 1 decimal if not"""
    try:
        value = float(value)
        if value == int(value):
            return str(int(value))
        return f"{value:.1f}"
    except (ValueError, TypeError):
        return value

@register.filter
def smart_question_text(text):
    """
    Smart format for question text that handles both plain text and HTML content.
    If text contains HTML tags, treat as HTML. Otherwise, convert plain text to HTML with line breaks.
    Also cleans up any toolbar remnants.
    """
    import re
    from django.utils.safestring import mark_safe
    from django.utils.html import escape, linebreaks
    
    if not text:
        return ""
    
    def clean_toolbar_content(html_text):
        """Clean toolbar elements and text from HTML content"""
        # Remove toolbar HTML elements
        html_text = re.sub(r'<div[^>]*class="[^"]*image-edit-toolbar[^"]*"[^>]*>.*?</div>', '', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<div[^>]*class="[^"]*resize-handle[^"]*"[^>]*>.*?</div>', '', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<div[^>]*class="[^"]*image-resizer[^"]*"[^>]*>(.*?)</div>', r'\1', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<div[^>]*class="[^"]*resizable-image[^"]*"[^>]*>(.*?)</div>', r'\1', html_text, flags=re.DOTALL)
        
        # Remove toolbar buttons
        html_text = re.sub(r'<button[^>]*onclick="[^"]*resizeImagePercent[^"]*"[^>]*>.*?</button>', '', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<button[^>]*onclick="[^"]*removeImageFromResizer[^"]*"[^>]*>.*?</button>', '', html_text, flags=re.DOTALL)
        html_text = re.sub(r'<button[^>]*class="[^"]*toolbar-btn[^"]*"[^>]*>.*?</button>', '', html_text, flags=re.DOTALL)
        
        # Remove buttons with specific toolbar text
        html_text = re.sub(r'<button[^>]*>(25%|50%|75%|100%|×)</button>', '', html_text)
        
        # Remove any resize-related attributes and classes
        html_text = re.sub(r'data-handle="[^"]*"', '', html_text)
        html_text = re.sub(r'class="[^"]*resize-handle[^"]*"', '', html_text)
        html_text = re.sub(r'class="[^"]*image-resizer[^"]*"', '', html_text)
        html_text = re.sub(r'class="[^"]*resizable-image[^"]*"', '', html_text)
        
        # Remove standalone toolbar text patterns
        html_text = re.sub(r'\b25%\s*50%\s*75%\s*100%\s*×\b', '', html_text)
        html_text = re.sub(r'\b25%\s*50%\s*75%\s*100%\b', '', html_text)
        html_text = re.sub(r'\b(25%|50%|75%|100%)\s*', '', html_text)
        html_text = re.sub(r'\s*×\s*', '', html_text)
        
        # Clean up empty elements and extra whitespace
        html_text = re.sub(r'<div[^>]*>\s*</div>', '', html_text)
        html_text = re.sub(r'<div[^>]*class=""\s*>', '<div>', html_text)
        html_text = re.sub(r'>\s+<', '><', html_text)
        html_text = re.sub(r'\s+', ' ', html_text)
        html_text = html_text.strip()
        
        return html_text
    
    # Check if text contains HTML tags (especially WYSIWYG content)
    html_pattern = r'<(?:span|div|p|br|strong|em|u|ol|ul|li|h[1-6]|img|table|tr|td|th|thead|tbody)[^>]*>'
    
    if re.search(html_pattern, text, re.IGNORECASE):
        # Text contains HTML, clean toolbar content and treat as HTML
        cleaned_text = clean_toolbar_content(text)
        return mark_safe(cleaned_text)
    else:
        # Plain text, convert to HTML with proper escaping and line breaks
        escaped_text = escape(text)
        return mark_safe(linebreaks(escaped_text))