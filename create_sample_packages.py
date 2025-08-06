#!/usr/bin/env python
"""
Script untuk membuat sample subscription packages
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import SubscriptionPackage

def create_sample_packages():
    """Create sample subscription packages"""
    try:
        # Paket Dasar
        basic_package, created = SubscriptionPackage.objects.get_or_create(
            name='Paket Dasar',
            defaults={
                'package_type': 'basic',
                'description': 'Paket berlangganan dasar untuk akses tryout online dengan fitur standar.',
                'features': '''Akses 50+ soal tryout
Akses ke semua kategori
Statistik hasil ujian
Support customer service''',
                'price': 50000,
                'duration_days': 30,
                'is_active': True,
                'is_featured': False
            }
        )
        if created:
            print("✅ Paket Dasar berhasil dibuat!")
        
        # Paket Premium
        premium_package, created = SubscriptionPackage.objects.get_or_create(
            name='Paket Premium',
            defaults={
                'package_type': 'premium',
                'description': 'Paket berlangganan premium dengan fitur lengkap dan akses unlimited.',
                'features': '''Akses unlimited soal tryout
Akses ke semua kategori
Statistik detail dan analisis
Bank soal terbaru
Pembahasan lengkap
Support prioritas''',
                'price': 100000,
                'duration_days': 30,
                'is_active': True,
                'is_featured': True
            }
        )
        if created:
            print("✅ Paket Premium berhasil dibuat!")
        
        # Paket Pro
        pro_package, created = SubscriptionPackage.objects.get_or_create(
            name='Paket Pro',
            defaults={
                'package_type': 'pro',
                'description': 'Paket berlangganan pro untuk persiapan ujian serius dengan mentoring.',
                'features': '''Akses unlimited soal tryout
Akses ke semua kategori
Statistik advanced analytics
Bank soal terbaru + eksklusif
Pembahasan video
Konsultasi dengan mentor
Mock test berkala
Support 24/7''',
                'price': 200000,
                'duration_days': 30,
                'is_active': True,
                'is_featured': False
            }
        )
        if created:
            print("✅ Paket Pro berhasil dibuat!")
        
        # Paket 3 Bulan (Ultimate)
        ultimate_package, created = SubscriptionPackage.objects.get_or_create(
            name='Paket Ultimate (3 Bulan)',
            defaults={
                'package_type': 'ultimate',
                'description': 'Paket berlangganan 3 bulan dengan benefit maksimal dan harga terjangkau.',
                'features': '''Semua fitur Paket Pro
Berlaku 3 bulan
Bonus materi eksklusif
Kelas online gratis
Sertifikat digital
Konsultasi intensif
Grup belajar eksklusif
Garansi nilai''',
                'price': 450000,
                'duration_days': 90,
                'is_active': True,
                'is_featured': True
            }
        )
        if created:
            print("✅ Paket Ultimate (3 Bulan) berhasil dibuat!")
            
        print("\n📦 Paket berlangganan yang tersedia:")
        for package in SubscriptionPackage.objects.filter(is_active=True).order_by('price'):
            featured = " ⭐ (Unggulan)" if package.is_featured else ""
            print(f"  - {package.name}: Rp {package.price:,.0f} ({package.duration_days} hari){featured}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    create_sample_packages()
