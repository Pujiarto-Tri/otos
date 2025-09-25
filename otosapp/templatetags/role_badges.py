from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Define pastel color classes for roles
ROLE_BADGE_MAP = {
    'Student': ('bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-100', 'bg-pink-200/50'),
    'Teacher': ('bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100', 'bg-purple-200/50'),
    'Operator': ('bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-100', 'bg-teal-200/50'),
    'Admin': ('bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100', 'bg-yellow-200/50'),
}


@register.simple_tag
def role_badge(role_name, small=False):
    """Return HTML for a pastel badge for the given role name."""
    classes, _bg = ROLE_BADGE_MAP.get(role_name, ('bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-100', 'bg-gray-200/50'))
    size_classes = 'px-2 py-0.5 text-xs font-medium rounded-full' if small else 'px-3 py-1 text-sm font-medium rounded-full'
    html = f'<span class="{classes} {size_classes}">{role_name}</span>'
    return mark_safe(html)
