from django.urls import path
from . import views
from .views import register
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    path('settings/', views.settings_view, name='settings'),
    
    path('admin/categories/', views.category_list, name='category_list'),
    path('admin/categories/create/', views.category_create, name='category_create'),
    path('admin/categories/<int:category_id>/edit/', views.category_update, name='category_update'),
    path('admin/categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('admin/categories/<int:category_id>/update-utbk/', views.update_utbk_coefficients, name='update_utbk_coefficients'),
    path('admin/categories/update-all-utbk/', views.update_all_utbk_coefficients, name='update_all_utbk'),

    path('admin/users/', views.user_list, name='user_list'),
    path('admin/users/create/', views.user_create, name='user_create'),
    path('admin/users/<int:user_id>/edit/', views.user_update, name='user_update'),
    path('admin/users/<int:user_id>/delete/', views.user_delete, name='user_delete'),

    path('admin/question/', views.question_list, name='question_list'),
    path('admin/question/category/<int:category_id>/', views.question_list_by_category, name='question_list_by_category'),
    path('admin/question/create/', views.question_create, name='question_create'),
    path('admin/question/<int:question_id>/edit/', views.question_update, name='question_update'),
    path('admin/question/<int:question_id>/delete/', views.question_delete, name='question_delete'),
    path('admin/image-upload/', views.image_upload, name='image_upload'),

    # Teacher routes
    path('teacher/categories/', views.teacher_category_list, name='teacher_category_list'),
    path('teacher/categories/create/', views.teacher_category_create, name='teacher_category_create'),
    path('teacher/categories/<int:category_id>/edit/', views.teacher_category_update, name='teacher_category_update'),
    path('teacher/categories/<int:category_id>/delete/', views.teacher_category_delete, name='teacher_category_delete'),
    path('teacher/categories/<int:category_id>/questions/', views.teacher_question_list, name='teacher_question_list'),
    path('teacher/categories/<int:category_id>/questions/create/', views.teacher_question_create, name='teacher_question_create'),
    path('teacher/questions/<int:question_id>/edit/', views.teacher_question_update, name='teacher_question_update'),
    path('teacher/questions/<int:question_id>/delete/', views.teacher_question_delete, name='teacher_question_delete'),
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
    path('teacher/categories/<int:category_id>/scores/', views.teacher_view_student_scores, name='teacher_view_student_scores'),
    path('teacher/categories/<int:category_id>/scores/<int:test_id>/review/', views.teacher_test_review, name='teacher_test_review'),
    path('teacher/image-upload/', views.image_upload, name='teacher_image_upload'),

    path('students/tryouts/', views.tryout_list, name='tryout_list'),
    path('students/tryouts/<int:category_id>/take/<int:question>/', views.take_test, name='take_test'),
    path('students/tryouts/package/<int:package_id>/take/', views.take_package_test, name='take_package_test'),
    path('students/tryouts/package/<int:package_id>/question/<int:question>/', views.take_package_test_question, name='take_package_test_question'),
    path('students/tryouts/package/<int:package_id>/submit/', views.submit_package_test, name='submit_package_test'),
    path('students/tests/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('students/tests/<int:test_id>/force-end/', views.force_end_test, name='force_end_test'),
    path('students/tests/<int:test_id>/results/', views.test_results, name='test_results'),
    path('students/tests/<int:test_id>/results/detail/', views.test_results_detail, name='test_results_detail'),
    path('students/tests/history/', views.test_history, name='test_history'),
    path('students/rankings/', views.student_rankings, name='student_rankings'),
    
    # Messaging System URLs
    path('messages/', views.message_inbox, name='message_inbox'),
    path('messages/create/', views.create_message_thread, name='create_message_thread'),
    path('messages/thread/<int:thread_id>/', views.message_thread, name='message_thread'),
    path('messages/thread/<int:thread_id>/assign/', views.assign_thread, name='assign_thread'),
    path('api/messages/unread-count/', views.message_api_unread_count, name='message_api_unread_count'),
    
    # Subscription & Payment URLs
    path('subscription/packages/', views.subscription_packages, name='subscription_packages'),
    path('subscription/upload-payment/<int:package_id>/', views.upload_payment_proof, name='upload_payment_proof'),
    path('subscription/payment-status/', views.payment_status, name='payment_status'),
    
    # Admin Subscription Management URLs
    path('admin/subscription/packages/', views.admin_subscription_packages, name='admin_subscription_packages'),
    path('admin/subscription/packages/create/', views.create_subscription_package, name='create_subscription_package'),
    path('admin/subscription/packages/<int:package_id>/edit/', views.update_subscription_package, name='update_subscription_package'),
    path('admin/subscription/packages/<int:package_id>/delete/', views.delete_subscription_package, name='delete_subscription_package'),
    
    # Payment Method Management URLs
    path('admin/payment/methods/', views.admin_payment_methods, name='admin_payment_methods'),
    path('admin/payment/methods/create/', views.create_payment_method, name='create_payment_method'),
    path('admin/payment/methods/<int:method_id>/edit/', views.update_payment_method, name='update_payment_method'),
    path('admin/payment/methods/<int:method_id>/delete/', views.delete_payment_method, name='delete_payment_method'),
    
    path('admin/payment/verifications/', views.admin_payment_verifications, name='admin_payment_verifications'),
    path('admin/payment/verify/<int:payment_id>/', views.verify_payment, name='verify_payment'),
    path('admin/subscription/users/', views.admin_user_subscriptions, name='admin_user_subscriptions'),
    path('admin/subscription/<int:subscription_id>/details/', views.subscription_details, name='subscription_details'),
    path('admin/subscription/<int:subscription_id>/edit/', views.edit_user_subscription, name='edit_user_subscription'),
    path('admin/subscription/extend/<int:subscription_id>/', views.extend_user_subscription, name='extend_user_subscription'),
    path('admin/subscription/toggle/<int:subscription_id>/', views.toggle_subscription_status, name='toggle_subscription_status'),
    path('admin/users/<int:user_id>/change-role/', views.manual_role_change, name='manual_role_change'),
    
    # University Management URLs
    path('admin/university/', views.admin_university_list, name='admin_university_list'),
    path('admin/university/create/', views.admin_university_create, name='admin_university_create'),
    path('admin/university/<int:university_id>/edit/', views.admin_university_update, name='admin_university_update'),
    path('admin/university/<int:university_id>/delete/', views.admin_university_delete, name='admin_university_delete'),
    
    # Tryout Package Management URLs
    path('admin/packages/', views.admin_package_list, name='admin_package_list'),
    path('admin/packages/create/', views.admin_package_create, name='admin_package_create'),
    path('admin/packages/<int:package_id>/edit/', views.admin_package_update, name='admin_package_update'),
    path('admin/packages/<int:package_id>/delete/', views.admin_package_delete, name='admin_package_delete'),
    path('admin/packages/<int:package_id>/detail/', views.admin_package_detail, name='admin_package_detail'),
    # API for admin UI
    path('api/category/<int:category_id>/question-count/', views.api_category_question_count, name='api_category_question_count'),
    
    # Student University Target URLs
    path('students/university/target/', views.student_university_target, name='student_university_target'),
    path('students/university/recommendations/', views.student_university_recommendations, name='student_university_recommendations'),
    # API endpoint for university ajax search
    path('api/universities/', views.api_universities, name='api_universities'),
]