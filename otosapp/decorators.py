from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.contrib import messages

def admin_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name == 'Admin':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def operator_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name == 'Operator':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def admin_or_operator_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role.role_name == 'Admin' or request.user.role.role_name == 'Operator'):
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def admin_or_teacher_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role.role_name == 'Admin' or request.user.role.role_name == 'Teacher'):
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def admin_or_teacher_or_operator_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and (request.user.role.role_name in ['Admin', 'Teacher', 'Operator']):
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def students_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name == 'Student':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def visitor_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name == 'Visitor':
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def visitor_or_student_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role.role_name in ['Visitor', 'Student']:
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return wrap

def active_subscription_required(function):
    """Decorator untuk memastikan user memiliki subscription aktif"""
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Silakan login terlebih dahulu.')
            return redirect('login')
        
        if not request.user.can_access_tryouts():
            subscription_status = request.user.get_subscription_status()
            
            if request.user.is_visitor():
                messages.warning(request, 'Silakan berlangganan terlebih dahulu untuk mengakses fitur tryout.')
                return redirect('subscription_packages')
            elif request.user.is_student() and not request.user.has_active_subscription():
                if subscription_status['status'] == 'deactivated':
                    messages.warning(request, 'Langganan Anda telah dinonaktifkan oleh admin. Silakan hubungi admin atau berlangganan kembali.')
                elif subscription_status['status'] == 'expired':
                    messages.warning(request, 'Langganan Anda telah berakhir. Silakan perpanjang untuk melanjutkan.')
                else:
                    messages.warning(request, 'Langganan Anda tidak aktif. Silakan berlangganan untuk melanjutkan.')
                return redirect('subscription_packages')
            else:
                messages.error(request, 'Akses ditolak.')
                return redirect('home')
        
        return function(request, *args, **kwargs)
    return wrap
