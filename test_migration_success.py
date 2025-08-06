#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

try:
    from otosapp.models import MessageThread, Message, User, Role
    
    print("🎉 MESSAGING SYSTEM - MIGRATION BERHASIL!")
    print("=" * 50)
    
    print("✅ MessageThread model tersedia")
    print("✅ Message model tersedia")
    
    # Test model counts
    thread_count = MessageThread.objects.count()
    message_count = Message.objects.count()
    
    print(f"📊 MessageThread count: {thread_count}")
    print(f"📊 Message count: {message_count}")
    
    # Test model fields
    print("\n🔧 MessageThread fields:")
    for field in MessageThread._meta.fields:
        print(f"   - {field.name}: {field.__class__.__name__}")
    
    print("\n🔧 Message fields:")
    for field in Message._meta.fields:
        print(f"   - {field.name}: {field.__class__.__name__}")
    
    # Test choices
    print(f"\n📋 Thread Types: {dict(MessageThread.THREAD_TYPES)}")
    print(f"📋 Status Choices: {dict(MessageThread.STATUS_CHOICES)}")
    
    print("\n" + "=" * 50)
    print("🚀 SISTEM MESSAGING SIAP DIGUNAKAN!")
    print("\n📍 Next Steps:")
    print("   1. Start server: python manage.py runserver")
    print("   2. Test messaging: http://localhost:8000/messages/")
    print("   3. Create new message: http://localhost:8000/messages/create/")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
