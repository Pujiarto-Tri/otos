# Vercel Blob Storage Setup untuk OTOS

## Masalah
Gambar menunjukkan 404 error di Vercel tetapi bekerja normal di server lokal.

## Penyebab
1. Token Vercel Blob tidak valid atau belum di-setup dengan benar
2. Konfigurasi storage tidak menggunakan Vercel Blob yang sebenarnya

## Solusi

### 1. Setup Vercel Blob Store
1. Buka [Vercel Dashboard](https://vercel.com/dashboard)
2. Pilih project `otos`
3. Buka tab "Storage"
4. Klik "Connect Database"
5. Pilih "Blob" → "Continue"
6. Beri nama: `otos-media`
7. Pilih region (misalnya `iad1` untuk US East)
8. Pilih environment: Production, Preview, Development
9. Klik "Create"

### 2. Mendapatkan Token
Setelah blob store dibuat, Anda akan mendapat environment variable:
```
BLOB_READ_WRITE_TOKEN=vercel_blob_rw_XXXXXXXXXXXXXXXXXXXXXXXXXX
```

### 3. Konfigurasi Environment Variable
- Token akan otomatis tersedia di Vercel deployment
- Untuk development lokal, buat file `.env` dan tambahkan:
  ```
  BLOB_READ_WRITE_TOKEN=vercel_blob_rw_XXXXXXXXXXXXXXXXXXXXXXXXXX
  ```

### 4. Update Kode (Sudah Dilakukan)
- ✅ Storage backend sudah diupdate di `otosapp/storage.py`
- ✅ Settings sudah dikonfigurasi di `otos/settings.py`
- ✅ Fallback ke local storage jika token tidak valid

### 5. Deployment
1. Commit semua perubahan:
   ```bash
   git add .
   git commit -m "Update Vercel Blob storage implementation"
   git push
   ```

2. Deploy ke Vercel (akan otomatis jika sudah di-link ke Git)

### 6. Testing
Setelah deployment:
1. Upload gambar baru di production
2. Periksa apakah URL gambar berubah dari `/media/...` ke `https://xxxxxx.public.blob.vercel-storage.com/...`
3. Test apakah gambar dapat diakses

### 7. Migrasi Gambar Lama (Opsional)
Untuk gambar yang sudah ada di local storage, Anda bisa:
1. Upload ulang secara manual
2. Atau buat script migrasi (bisa dibantu jika diperlukan)

## Verifikasi
Jalankan command berikut untuk memverifikasi setup:
```bash
python setup_vercel_blob.py
```

## Troubleshooting
1. **Token masih invalid**: Pastikan menggunakan `BLOB_READ_WRITE_TOKEN` bukan `VERCEL_BLOB_TOKEN`
2. **Gambar lama 404**: Normal, karena gambar lama masih di local storage
3. **Upload error**: Periksa logs Vercel untuk error detail

## Status Saat Ini
- ✅ Storage backend dengan fallback sudah siap
- ✅ Konfigurasi settings sudah benar
- ⏳ Menunggu setup blob store dan token yang valid
- ⏳ Deployment dengan token yang benar
