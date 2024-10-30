from django.urls import path
from . import views
from .views import register
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('admin/categories/', views.category_list, name='category_list'),
    path('admin/categories/create/', views.category_create, name='category_create'),
    path('admin/categories/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('admin/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),

    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:user_id>/edit/', views.user_update, name='user_update'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
]