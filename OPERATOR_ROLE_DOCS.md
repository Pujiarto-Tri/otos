# Role Operator - Dokumentasi

## Deskripsi
Role **Operator** adalah role baru yang ditambahkan ke sistem OTOS (Online Test Exam System) untuk memberikan akses administratif terbatas tanpa akses ke data finansial yang sensitif.

## Perbedaan dengan Role Admin
| Fitur | Admin | Operator |
|-------|--------|----------|
| **Dashboard** | ✅ Lengkap dengan data finansial | ⚠️ Tanpa data finansial |
| | - Total Revenue | ❌ Tidak ada |
| | - Monthly Revenue | ❌ Tidak ada |
| | - Package Terpopuler | ❌ Tidak ada |
| | - Trend Penjualan | ⚠️ Hanya count, tanpa revenue |
| **User Management** | ✅ Penuh | ✅ Penuh |
| **Category Management** | ✅ Penuh | ✅ Penuh |
| **Question Management** | ✅ Penuh | ✅ Penuh |
| **Subscription Management** | ✅ Penuh | ✅ Penuh |
| **Payment Verification** | ✅ Penuh | ✅ Penuh |
| **Package Management** | ✅ Penuh (buat/edit/hapus) | ❌ Tidak ada akses |
| **Message/Support** | ✅ Penuh | ✅ Penuh |

## Hak Akses Operator

### ✅ **Yang BISA Diakses:**
1. **User Management**
   - Lihat daftar pengguna
   - Buat pengguna baru
   - Edit data pengguna
   - Hapus pengguna
   - Ubah role pengguna

2. **Category Management**
   - Lihat kategori ujian
   - Buat kategori baru
   - Edit kategori
   - Hapus kategori

3. **Question Management**
   - Lihat soal berdasarkan kategori
   - Buat soal baru
   - Edit soal
   - Hapus soal

4. **Subscription Management**
   - Lihat daftar langganan pengguna
   - Perpanjang langganan
   - Aktifkan/nonaktifkan langganan
   - Edit detail langganan

5. **Payment Verification**
   - Lihat pembayaran pending
   - Approve/reject pembayaran
   - Lihat riwayat pembayaran

6. **Support/Messages**
   - Balas pesan siswa
   - Assign thread ke staff lain
   - Kelola support ticket

7. **Dashboard Analytics**
   - Statistik jumlah pengguna
   - Jumlah langganan aktif
   - Jumlah pembayaran pending
   - Trend langganan (tanpa nilai rupiah)

### ❌ **Yang TIDAK BISA Diakses:**
1. **Financial Data**
   - Total revenue
   - Monthly revenue
   - Revenue trends
   - Package pricing details

2. **Package Management**
   - Buat paket berlangganan baru
   - Edit harga paket
   - Hapus paket
   - Kelola featured packages

## Cara Menambahkan User dengan Role Operator

### Melalui Admin Panel:
1. Login sebagai Admin
2. Buka "Kelola Pengguna" → "Tambah Pengguna Baru"
3. Isi data pengguna
4. Pilih Role: **Operator**
5. Simpan

### Melalui Django Admin:
1. Akses `/admin/`
2. Buka "Users"
3. Buat user baru atau edit user existing
4. Set Role ke "Operator"

### Melalui Management Command:
```bash
# Untuk menambahkan role Operator (sekali saja)
python manage.py add_operator_role
```

## Implementasi Teknis

### Models yang Dimodifikasi:
- `User.is_operator()` - method baru untuk cek role operator

### Decorators Baru:
- `@operator_required` - akses khusus operator
- `@admin_or_operator_required` - akses admin atau operator
- `@admin_or_teacher_or_operator_required` - akses admin, teacher, atau operator

### Views yang Diupdate:
- User management views
- Category management views  
- Question management views
- Subscription management views
- Payment verification views
- Message/support views

### Templates yang Diupdate:
- `home.html` - dashboard operator
- Dashboard charts dengan filter data

## Security Considerations

1. **Data Separation**: Operator tidak bisa melihat data revenue
2. **Permission Control**: Menggunakan decorator yang tepat untuk setiap view
3. **Role Hierarchy**: Admin > Operator > Teacher > Student > Visitor

## Best Practices

1. **Gunakan untuk**:
   - Customer support staff
   - Content moderator
   - Administrative assistant

2. **Jangan gunakan untuk**:
   - Financial operations
   - Strategic decision making
   - Access to business metrics

## Monitoring & Audit

Semua aksi operator dicatat dalam:
- Django admin logs
- User activity tracking (jika diimplementasikan)
- Database audit trail

---

**Dibuat pada**: 11 Agustus 2025  
**Versi**: 1.0  
**Status**: Active
