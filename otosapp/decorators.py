from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def admin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name == 'Admin':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap