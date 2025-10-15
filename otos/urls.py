"""
URL configuration for otos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/password_reset/', RedirectView.as_view(pattern_name='password_reset', permanent=False), name='admin_password_reset_redirect'),
    path('admin/password_reset/done/', RedirectView.as_view(pattern_name='password_reset_done', permanent=False), name='admin_password_reset_done_redirect'),
    path('admin/reset/<uidb64>/<token>/', RedirectView.as_view(pattern_name='password_reset_confirm', permanent=False), name='admin_password_reset_confirm_redirect'),
    path('admin/reset/done/', RedirectView.as_view(pattern_name='password_reset_complete', permanent=False), name='admin_password_reset_complete_redirect'),
    path('', include("otosapp.urls")),
    path('admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
