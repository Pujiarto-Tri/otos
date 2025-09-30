"""
Context processors untuk mengirimkan data global ke semua template
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import PaymentProof, Message

User = get_user_model()

def sidebar_context(request):
    """Context processor untuk data yang diperlukan di sidebar"""
    context = {}
    
    resolver_match = getattr(request, 'resolver_match', None)
    hide_chrome_names = {
        'take_test',
        'take_package_test',
        'take_package_test_question',
        'submit_package_test',
        'submit_test',
    }
    hide_chrome = False
    if resolver_match is not None:
        hide_chrome = resolver_match.url_name in hide_chrome_names

    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_admin()):
        # Hitung pending payments untuk admin
        pending_payments_count = PaymentProof.objects.filter(status='pending').count()
        context['pending_payments_count'] = pending_payments_count

    # Compute unread message count for inbox badge
    try:
        if request.user.is_authenticated:
            user = request.user
            if user.role and user.role.role_name == 'Student':
                unread_count = Message.objects.filter(thread__student=user, is_read=False).exclude(sender=user).count()
            else:
                unread_count = Message.objects.filter(
                    (Q(thread__teacher_or_admin=user) | Q(thread__teacher_or_admin=None)),
                    is_read=False
                ).exclude(sender=user).count()
            context['message_unread_count'] = unread_count
    except Exception:
        context['message_unread_count'] = 0

    context['hide_chrome'] = hide_chrome
    context['show_sidebar'] = (
        request.user.is_authenticated
        and not hide_chrome
        and request.path not in ('/otosapp/login/', '/otosapp/register/')
    )
    
    return context
