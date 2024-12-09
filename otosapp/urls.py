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

    path('admin/question/', views.question_list, name='question_list'),
    path('admin/question/create/', views.question_create, name='question_create'),
    path('admin/question/<int:question_id>/edit/', views.question_update, name='question_update'),
    path('admin/question/<int:question_id>/delete/', views.question_delete, name='question_delete'),

    path('students/tryouts/', views.tryout_list, name='tryout_list'),
    path('students/tryouts/<int:category_id>/take/<int:question>/', views.take_test, name='take_test'),
]