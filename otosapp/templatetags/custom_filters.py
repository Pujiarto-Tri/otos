from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


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
    """Add arg to value (convert to int)"""
    try:
        return int(float(value)) + int(float(arg))
    except (ValueError, TypeError):
        return 0
    

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