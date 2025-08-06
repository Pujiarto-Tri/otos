# 📨 Sistem Messaging - Dokumentasi Lengkap

## 🎯 Fitur Messaging System

Sistem messaging yang telah ditambahkan memungkinkan komunikasi dua arah antara:
- **Siswa ↔ Guru** (untuk pertanyaan materi)
- **Siswa ↔ Admin** (untuk masalah teknis/aplikasi dan pelaporan)

## 🏗️ Struktur Model

### 1. MessageThread
Model untuk thread pesan yang berisi metadata percakapan:

```python
class MessageThread(models.Model):
    title = models.CharField(max_length=200)  # Judul thread
    thread_type = models.CharField(max_length=20, choices=THREAD_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    student = models.ForeignKey(User, related_name='student_threads')
    teacher_or_admin = models.ForeignKey(User, related_name='handled_threads')
    category = models.ForeignKey(Category, null=True, blank=True)  # Untuk pertanyaan materi
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
```

**Thread Types:**
- `academic`: Pertanyaan Materi
- `technical`: Masalah Teknis/Aplikasi  
- `report`: Pelaporan Masalah
- `general`: Umum

**Status:**
- `open`: Terbuka
- `pending`: Menunggu Respons
- `resolved`: Selesai
- `closed`: Ditutup

**Priority:**
- `low`: Rendah
- `normal`: Normal
- `high`: Tinggi
- `urgent`: Mendesak

### 2. Message
Model untuk pesan individual dalam thread:

```python
class Message(models.Model):
    thread = models.ForeignKey(MessageThread, related_name='messages')
    sender = models.ForeignKey(User, related_name='sent_messages')
    content = models.TextField()  # Isi pesan
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    is_read = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

## 🌐 URL Patterns

```python
# URLs untuk messaging system
path('messages/', views.message_inbox, name='message_inbox'),
path('messages/create/', views.create_message_thread, name='create_message_thread'),
path('messages/thread/<int:thread_id>/', views.message_thread, name='message_thread'),
path('messages/thread/<int:thread_id>/assign/', views.assign_thread, name='assign_thread'),
path('api/messages/unread-count/', views.message_api_unread_count, name='message_api_unread_count'),
```

## 🎛️ Views yang Tersedia

### 1. `message_inbox`
- **Fungsi**: Menampilkan daftar thread pesan
- **Akses**: Semua user yang login
- **Filter**: Status, tipe, pencarian
- **Pagination**: Ya (10 thread per halaman)

### 2. `create_message_thread`
- **Fungsi**: Membuat thread pesan baru
- **Akses**: Khusus siswa
- **Validasi**: Judul dan isi pesan wajib diisi

### 3. `message_thread`
- **Fungsi**: Menampilkan detail thread dan pesan-pesannya
- **Akses**: Siswa (thread sendiri), Guru/Admin (assigned threads)
- **Fitur**: Kirim balasan, ubah status, attachment

### 4. `assign_thread`
- **Fungsi**: Assign thread ke guru/admin tertentu
- **Akses**: Guru dan Admin

### 5. `message_api_unread_count`
- **Fungsi**: API untuk mendapatkan jumlah pesan belum dibaca
- **Akses**: Semua user yang login
- **Return**: JSON dengan unread_count

## 🖼️ Template Files

### 1. `messages/inbox.html`
- Daftar thread pesan dengan filter dan search
- Pagination
- Badge untuk unread count
- Empty state yang informatif

### 2. `messages/create_thread.html`
- Form untuk membuat thread baru
- Conditional field untuk kategori materi
- Tips untuk pesan yang efektif
- File upload support

### 3. `messages/thread_detail.html`
- Chat-like interface untuk percakapan
- Form reply dengan attachment
- Status management untuk guru/admin
- Message threading yang jelas

## 🧭 Navigation Integration

Sistem messaging telah terintegrasi dengan sidebar navigation:

- **Student**: Menu "Pesan" dengan unread badge
- **Teacher**: Menu "Teacher Inbox" dengan unread badge  
- **Admin**: Menu "Admin Inbox" dengan unread badge

## 🔧 Setup Instructions

### 1. Database Migration
```bash
# Buat migration file (sudah dibuat: 0007_messagethread_message.py)
python manage.py makemigrations

# Jalankan migration
python manage.py migrate
```

### 2. Admin Configuration
Model telah didaftarkan di admin dengan interface yang user-friendly:
- MessageThreadAdmin: Inline messages, filtering, search
- MessageAdmin: Content preview, thread relationship

### 3. File Storage
Pastikan direktori untuk attachment tersedia:
```
MEDIA_ROOT/message_attachments/
```

## 🎯 Use Cases

### Untuk Siswa:
1. **Bertanya Materi**:
   - Pilih tipe "Pertanyaan Materi"
   - Pilih kategori mata pelajaran
   - Tulis pertanyaan detail
   - Upload screenshot/file jika perlu

2. **Lapor Masalah Teknis**:
   - Pilih tipe "Masalah Teknis/Aplikasi"
   - Jelaskan masalah dan langkah yang sudah dicoba
   - Upload screenshot error

3. **Pelaporan**:
   - Pilih tipe "Pelaporan Masalah"
   - Berikan detail waktu, tempat, kronologi
   - Set priority jika urgent

### Untuk Guru:
1. **Menjawab Pertanyaan Materi**:
   - Lihat thread dengan tipe "Pertanyaan Materi"
   - Berikan penjelasan detail
   - Upload materi tambahan jika perlu
   - Ubah status menjadi "Selesai" setelah terjawab

### Untuk Admin:
1. **Handle Masalah Teknis**:
   - Assign thread ke admin yang tepat
   - Troubleshoot dan berikan solusi
   - Update status sesuai progress

2. **Manage Pelaporan**:
   - Assign berdasarkan jenis laporan
   - Follow up dengan pihak terkait
   - Close thread setelah resolved

## 🔒 Security Features

1. **Access Control**: User hanya bisa akses thread yang relevan
2. **File Validation**: Validasi ukuran dan tipe file attachment
3. **Input Sanitization**: Django form validation dan CSRF protection
4. **Role-based Permissions**: Akses fitur berdasarkan role user

## 📊 Monitoring Features

1. **Unread Count**: Real-time update setiap 30 detik
2. **Thread Status**: Tracking status dari open hingga closed
3. **Priority Management**: Prioritas untuk handling urgent issues
4. **Activity Tracking**: Last activity timestamp untuk sorting

## 🎨 UI/UX Features

1. **Responsive Design**: Works on desktop dan mobile
2. **Dark Mode Support**: Compatible dengan theme switching
3. **Real-time Updates**: Auto-refresh unread count
4. **Intuitive Interface**: Chat-like conversation view
5. **Smart Filtering**: Filter berdasarkan status, tipe, search
6. **Empty States**: Helpful messages ketika tidak ada data

## 🚀 Advanced Features

1. **Auto-assignment**: Thread otomatis assign ke guru/admin yang available
2. **Smart Categorization**: Automatic routing berdasarkan thread type
3. **Notification System**: Badge dan count untuk unread messages
4. **File Management**: Safe file upload dengan validation
5. **Search & Filter**: Comprehensive search across thread content

---

## 📝 Kesimpulan

Sistem messaging ini menyediakan platform komunikasi yang lengkap untuk mendukung proses pembelajaran dan administrasi dalam aplikasi ujian online. Dengan fitur-fitur yang user-friendly dan security yang baik, sistem ini akan meningkatkan interaksi antara siswa, guru, dan admin.

**Next Steps**:
1. Run migration untuk membuat tabel database
2. Test fitur-fitur messaging di browser
3. Customize sesuai kebutuhan spesifik
4. Monitor penggunaan dan optimize performance
