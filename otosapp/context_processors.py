"""
Context processors untuk mengirimkan data global ke semua template
"""
from django.contrib.auth import get_user_model
from .models import PaymentProof

User = get_user_model()

def sidebar_context(request):
    """Context processor untuk data yang diperlukan di sidebar"""
    context = {}
    
    if request.user.is_authenticated and (request.user.is_superuser or request.user.is_admin()):
        # Hitung pending payments untuk admin
        pending_payments_count = PaymentProof.objects.filter(status='pending').count()
        context['pending_payments_count'] = pending_payments_count
    
    return context
