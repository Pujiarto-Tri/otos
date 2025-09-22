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
    
    return context
