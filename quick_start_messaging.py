#!/usr/bin/env python
"""
Quick Start Guide untuk Messaging System
"""

print("""
🚀 QUICK START - MESSAGING SYSTEM
==================================

📋 Langkah-langkah untuk menjalankan sistem messaging:

1️⃣ ACTIVATE VIRTUAL ENVIRONMENT
   # Jika menggunakan venv
   .\\venv\\Scripts\\activate  (Windows)
   source venv/bin/activate   (Linux/Mac)
   
   # Jika menggunakan conda
   conda activate your_env_name

2️⃣ INSTALL DEPENDENCIES (jika belum)
   pip install django
   pip install django-ckeditor-5
   pip install pillow

3️⃣ RUN MIGRATIONS
   python manage.py makemigrations
   python manage.py migrate

4️⃣ CREATE SAMPLE DATA (opsional)
   python manage.py shell
   >>> from otosapp.models import *
   >>> # Buat role jika belum ada
   >>> Role.objects.get_or_create(role_name='Student')
   >>> Role.objects.get_or_create(role_name='Teacher') 
   >>> Role.objects.get_or_create(role_name='Admin')

5️⃣ START SERVER
   python manage.py runserver

6️⃣ TEST FEATURES
   📍 Login sebagai student: /messages/create/
   📍 Login sebagai teacher/admin: /messages/
   📍 API endpoint: /api/messages/unread-count/

🎯 FITUR YANG TERSEDIA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👨‍🎓 UNTUK SISWA:
• Kirim pesan ke guru (pertanyaan materi)
• Kirim pesan ke admin (masalah teknis/pelaporan)
• Upload file attachment
• Lihat riwayat percakapan
• Real-time unread count

👨‍🏫 UNTUK GURU:
• Terima dan balas pesan dari siswa
• Filter pesan berdasarkan kategori materi
• Assign thread ke guru lain
• Update status percakapan
• Manage priority levels

👨‍💼 UNTUK ADMIN:
• Handle masalah teknis dan pelaporan
• Assign thread ke admin yang tepat
• Monitor semua komunikasi
• Manage user permissions

🔧 TROUBLESHOOTING:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Error "No module named 'django'":
   ✅ Aktifkan virtual environment terlebih dahulu

❌ Migration error:
   ✅ Pastikan database connection OK
   ✅ Run: python manage.py makemigrations otosapp

❌ Template not found:
   ✅ Pastikan folder templates/messages/ ada
   ✅ Check TEMPLATES setting di settings.py

❌ Static files not loading:
   ✅ Run: python manage.py collectstatic
   ✅ Check STATIC_URL dan STATIC_ROOT

❌ File upload error:
   ✅ Pastikan MEDIA_ROOT dan MEDIA_URL configured
   ✅ Create direktori media/message_attachments/

🌐 URL ENDPOINTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📥 /messages/                     - Inbox (daftar thread)
✉️  /messages/create/             - Buat pesan baru (siswa)
💬 /messages/thread/<id>/         - Detail thread
🔄 /messages/thread/<id>/assign/  - Assign thread
📊 /api/messages/unread-count/    - API unread count

🎨 CUSTOMIZATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Edit templates di: otosapp/templates/messages/
• Modify styles dengan Tailwind CSS classes
• Extend models untuk fitur tambahan
• Add custom middleware untuk notifications
• Integrate dengan email/SMS notifications

💡 TIPS PENGGUNAAN:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Set priority 'urgent' untuk masalah penting
2. Gunakan kategori materi untuk routing otomatis
3. Upload screenshot untuk debugging masalah teknis
4. Close thread setelah masalah resolved
5. Use search function untuk menemukan thread lama

🎉 SELAMAT! Sistem messaging siap digunakan!
""")

print("💻 Untuk menjalankan server:")
print("   python manage.py runserver")
print("\n🌍 Akses aplikasi di: http://localhost:8000")
print("📱 Test messaging di: http://localhost:8000/messages/")
