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
    """
    import re
    from django.utils.safestring import mark_safe
    from django.utils.html import escape, linebreaks
    
    if not text:
        return ""
    
    # Check if text contains HTML tags (especially WYSIWYG content)
    html_pattern = r'<(?:span|div|p|br|strong|em|u|ol|ul|li|h[1-6]|img|table|tr|td|th|thead|tbody)[^>]*>'
    
    if re.search(html_pattern, text, re.IGNORECASE):
        # Text contains HTML, treat as HTML content
        return mark_safe(text)
    else:
        # Plain text, convert to HTML with proper escaping and line breaks
        escaped_text = escape(text)
        return mark_safe(linebreaks(escaped_text))