# 🎓 SISTEM REKOMENDASI UNIVERSITAS - FITUR BARU

## 📋 SUMMARY PERUBAHAN

### 1. **PERBAIKAN SISTEM UTBK**
- ✅ **Nilai maksimal UTBK diupdate menjadi 1000** (sesuai standar UTBK sesungguhnya)
- ✅ Algoritma scoring UTBK diperbaiki untuk menggunakan skala 1000
- ✅ Koefisien kesulitan soal dinormalisasi ke total 1000 poin

### 2. **MODEL BARU: UNIVERSITY**
```python
class University(models.Model):
    name = models.CharField(max_length=200)  # Nama universitas
    location = models.CharField(max_length=100)  # Lokasi
    website = models.URLField()  # Website universitas
    description = models.TextField()  # Deskripsi
    minimum_utbk_score = models.IntegerField(default=400)  # Nilai UTBK minimum (aman)
    tier = models.CharField()  # Tingkatan: tier1, tier2, tier3
    is_active = models.BooleanField(default=True)
```

### 3. **MODEL BARU: UNIVERSITYTARGET**
```python
class UniversityTarget(models.Model):
    user = models.OneToOneField(User)  # Student yang memiliki target
    primary_university = models.ForeignKey(University)  # Target utama (impian)
    secondary_university = models.ForeignKey(University)  # Target cadangan
    backup_university = models.ForeignKey(University)  # Target aman
    notes = models.TextField()  # Catatan personal
```

## 🛠️ FITUR ADMIN & OPERATOR

### **Manajemen Universitas**
- **URL**: `/admin/university/`
- **Fitur**:
  - ✅ Tambah/edit/hapus universitas
  - ✅ Set nilai UTBK minimum (passing grade aman)
  - ✅ Kategori tier universitas (Tier 1: Top, Tier 2: Good, Tier 3: Standard)
  - ✅ Filter dan pencarian universitas
  - ✅ Statistik universitas per tier

### **Form Input Universitas**
- ✅ **Nama universitas** dan lokasi
- ✅ **Website** (opsional)
- ✅ **Deskripsi** universitas
- ✅ **Nilai UTBK minimum** (0-1000) - nilai aman untuk masuk
- ✅ **Tier classification**:
  - Tier 1: Universitas top (UI, ITB, UGM) - min 600-800
  - Tier 2: Universitas negeri favorit - min 500-650  
  - Tier 3: Universitas standar - min 400-500
- ✅ **Status aktif/nonaktif**

## 🎯 FITUR STUDENT

### **Pengaturan Target Universitas**
- **URL**: `/students/university/target/`
- **Fitur**:
  - ✅ Set 3 target universitas: Utama, Cadangan, Aman
  - ✅ Catatan personal untuk motivasi
  - ✅ Validasi: tidak boleh memilih universitas yang sama
  - ✅ Preview rekomendasi berdasarkan skor UTBK terbaru

### **Rekomendasi Universitas**
- **URL**: `/students/university/recommendations/`
- **Fitur**:
  - ✅ **Analisis skor UTBK** dengan grade (A, B+, B, C+, C, D)
  - ✅ **Status rekomendasi target** dengan 4 kategori:
    - 🟢 **Sangat Aman** (skor ≥ min + 100)
    - 🔵 **Aman** (skor ≥ min)
    - 🟡 **Kurang Aman** (skor ≥ min - 50)
    - 🔴 **Tidak Aman** (skor < min - 50)
  - ✅ **Persentase kelayakan** berdasarkan nilai aman
  - ✅ **Rekomendasi umum** dari semua universitas yang diurutkan berdasarkan kesesuaian

## 🧮 ALGORITMA REKOMENDASI

### **Perhitungan Status Rekomendasi**
```python
def get_recommendation_for_score(self, utbk_score):
    if utbk_score >= self.minimum_utbk_score + 100:
        return "Sangat Aman" (> 100% dari nilai aman)
    elif utbk_score >= self.minimum_utbk_score:
        return "Aman" (≥ nilai aman)
    elif utbk_score >= self.minimum_utbk_score - 50:
        return "Kurang Aman" (mendekati nilai aman)
    else:
        return "Tidak Aman" (jauh di bawah nilai aman)
```

### **Persentase Kelayakan**
```python
percentage = (utbk_score / minimum_utbk_score) * 100
```

## 📊 HASIL TEST UTBK

### **Fitur di Halaman Hasil**
- ✅ **Analisis skor detail**:
  - Raw score (0-1000)
  - Persentase (%)
  - Grade letter (A-D)
  - Interpretasi tekstual
- ✅ **Rekomendasi universitas langsung** setelah test
- ✅ **Perbandingan dengan target** yang sudah ditetapkan

## 🗃️ DATA DEFAULT

### **15 Universitas Sudah Dibuat**
- **Tier 1** (5): UI (650), ITB (640), UGM (630), IPB (620), ITS (610)
- **Tier 2** (5): UNAIR (530), UNDIP (540), UNPAD (520), UB (550), UNS (510)
- **Tier 3** (5): UNJ (450), UNEJ (440), UNILA (430), UNRI (420), UNIB (410)

### **4 Kategori UTBK Dibuat**
- ✅ Tes Potensi Skolastik (TPS) - 120 menit
- ✅ Literasi Bahasa Indonesia - 90 menit  
- ✅ Literasi Bahasa Inggris - 90 menit
- ✅ Penalaran Matematika - 90 menit

### **9 Soal Contoh UTBK**
- ✅ Setiap kategori memiliki 2-3 soal contoh
- ✅ Koefisien kesulitan sudah diset proporsional

## 🔗 URL ROUTING BARU

```python
# Admin University Management
path('admin/university/', views.admin_university_list, name='admin_university_list'),
path('admin/university/create/', views.admin_university_create, name='admin_university_create'),
path('admin/university/<int:university_id>/edit/', views.admin_university_update, name='admin_university_update'),
path('admin/university/<int:university_id>/delete/', views.admin_university_delete, name='admin_university_delete'),

# Student University Target
path('students/university/target/', views.student_university_target, name='student_university_target'),
path('students/university/recommendations/', views.student_university_recommendations, name='student_university_recommendations'),
```

## 🎨 TEMPLATE BARU

### **Admin Templates**
- ✅ `admin/university/university_list.html` - Daftar universitas dengan filter
- ✅ `admin/university/university_form.html` - Form tambah/edit universitas

### **Student Templates**  
- ✅ `students/university/target_settings.html` - Pengaturan target universitas
- ✅ `students/university/recommendations.html` - Halaman rekomendasi

## 💡 CARA PENGGUNAAN

### **Untuk Admin/Operator:**
1. Login sebagai admin/operator
2. Masuk ke `/admin/university/` untuk kelola universitas
3. Tambah universitas baru dengan nilai UTBK minimum
4. Set tier sesuai kategori universitas

### **Untuk Student:**
1. Login sebagai student dengan subscription aktif
2. Masuk ke `/students/university/target/` untuk set target
3. Pilih 3 universitas target (utama, cadangan, aman)
4. Kerjakan tryout UTBK untuk mendapat rekomendasi
5. Lihat hasil rekomendasi di `/students/university/recommendations/`

## 🚀 TESTING

### **Script untuk Data Setup:**
- ✅ `create_universities.py` - Membuat 15 universitas default
- ✅ `create_utbk_data.py` - Membuat kategori UTBK dan soal contoh

### **Test Flow:**
1. Jalankan server: `python manage.py runserver`
2. Login sebagai admin → kelola universitas
3. Login sebagai student → set target universitas
4. Kerjakan tryout UTBK → lihat rekomendasi

---

## 🎯 **HASIL AKHIR**

Sistem rekomendasi universitas yang lengkap dengan:
- ✅ **Nilai UTBK maksimal 1000** sesuai standar resmi
- ✅ **15 universitas** dengan passing grade realistis
- ✅ **Sistem target personal** untuk setiap student
- ✅ **Rekomendasi otomatis** berdasarkan hasil tryout
- ✅ **4 level status kelayakan** dengan persentase akurat
- ✅ **Interface admin** untuk mengelola universitas
- ✅ **Interface student** untuk setting target dan melihat rekomendasi

🎉 **Student sekarang bisa mendapat panduan yang jelas tentang universitas mana yang sesuai dengan kemampuan mereka berdasarkan hasil tryout UTBK!**
