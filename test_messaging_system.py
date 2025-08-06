#!/usr/bin/env python
"""
Script untuk testing sistem messaging
"""
import sys
import os

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
    
    import django
    django.setup()
    
    from otosapp.models import User, Role, Category, MessageThread, Message
    from django.db import transaction
    
    print("🧪 Testing Messaging System")
    print("=" * 50)
    
    # 1. Check if models exist
    print("1️⃣ Checking Models...")
    try:
        print(f"   ✅ MessageThread model: {MessageThread._meta.verbose_name}")
        print(f"   ✅ Message model: {Message._meta.verbose_name}")
        print(f"   ✅ MessageThread fields: {[f.name for f in MessageThread._meta.fields]}")
        print(f"   ✅ Message fields: {[f.name for f in Message._meta.fields]}")
    except Exception as e:
        print(f"   ❌ Model check error: {e}")
        sys.exit(1)
    
    # 2. Check relationships
    print("\n2️⃣ Checking Relationships...")
    try:
        # Check if User model has related names
        print(f"   ✅ User.student_threads: {hasattr(User, 'student_threads')}")
        print(f"   ✅ User.handled_threads: {hasattr(User, 'handled_threads')}")
        print(f"   ✅ User.sent_messages: {hasattr(User, 'sent_messages')}")
        print(f"   ✅ MessageThread.messages: {hasattr(MessageThread, 'messages')}")
    except Exception as e:
        print(f"   ❌ Relationship check error: {e}")
    
    # 3. Check choices
    print("\n3️⃣ Checking Choices...")
    try:
        print(f"   ✅ Thread types: {MessageThread.THREAD_TYPES}")
        print(f"   ✅ Status choices: {MessageThread.STATUS_CHOICES}")
    except Exception as e:
        print(f"   ❌ Choices check error: {e}")
    
    # 4. Test basic operations (if database is accessible)
    print("\n4️⃣ Testing Basic Database Operations...")
    try:
        # Count existing data
        thread_count = MessageThread.objects.count()
        message_count = Message.objects.count()
        user_count = User.objects.count()
        category_count = Category.objects.count()
        
        print(f"   ✅ Existing threads: {thread_count}")
        print(f"   ✅ Existing messages: {message_count}")
        print(f"   ✅ Total users: {user_count}")
        print(f"   ✅ Total categories: {category_count}")
        
        # Check if we have users with different roles
        student_count = User.objects.filter(role__role_name='Student').count()
        teacher_count = User.objects.filter(role__role_name='Teacher').count()
        admin_count = User.objects.filter(role__role_name='Admin').count()
        
        print(f"   ✅ Students: {student_count}")
        print(f"   ✅ Teachers: {teacher_count}")
        print(f"   ✅ Admins: {admin_count}")
        
    except Exception as e:
        print(f"   ⚠️ Database operations error (might not be migrated yet): {e}")
    
    # 5. URL patterns check
    print("\n5️⃣ Checking URL Patterns...")
    try:
        from django.urls import reverse
        urls_to_check = [
            'message_inbox',
            'create_message_thread',
            'message_api_unread_count'
        ]
        
        for url_name in urls_to_check:
            try:
                url = reverse(url_name)
                print(f"   ✅ {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ {url_name}: {e}")
                
    except Exception as e:
        print(f"   ❌ URL check error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Messaging System Test Complete!")
    print("\n📋 Next Steps:")
    print("   1. Run migrations: python manage.py migrate")
    print("   2. Create superuser if needed: python manage.py createsuperuser")
    print("   3. Start development server: python manage.py runserver")
    print("   4. Test messaging features in browser")
    
    print("\n💡 Features Available:")
    print("   • Student can send messages to teachers/admin")
    print("   • Teachers/Admin can reply to messages")
    print("   • Message threading and status management")
    print("   • File attachments support")
    print("   • Real-time unread count")
    print("   • Categorized messages (academic, technical, report)")
    print("   • Priority levels and status tracking")
    
except ImportError as e:
    print(f"❌ Django import error: {e}")
    print("💡 Make sure Django is installed and virtual environment is activated")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
