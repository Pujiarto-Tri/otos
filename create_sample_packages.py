#!/usr/bin/env python3
"""
Script untuk membuat contoh paket tryout UTBK
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.contrib.auth import get_user_model
from otosapp.models import Category, TryoutPackage, TryoutPackageCategory, Role

User = get_user_model()

def create_sample_packages():
    """Create sample tryout packages"""
    
    # Get or create admin user
    admin_role, _ = Role.objects.get_or_create(role_name='Admin')
    
    # Try to get existing admin user first
    try:
        admin_user = User.objects.filter(role=admin_role).first()
        if not admin_user:
            # Create with unique username
            admin_user = User.objects.create_user(
                email='admin.packages@example.com',
                username='admin_packages',
                password='admin123',
                role=admin_role,
                is_staff=True,
                is_superuser=True
            )
            print("✓ Admin user created for packages")
        else:
            print("✓ Using existing admin user")
    except Exception as e:
        print(f"Using first available admin user")
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            print("❌ No admin user found. Please create one manually.")
            return
    
    # Get available categories
    try:
        matematika = Category.objects.get(category_name__icontains='matematika')
    except Category.DoesNotExist:
        matematika = None
        
    try:
        ipa = Category.objects.get(category_name__icontains='ipa')
    except Category.DoesNotExist:
        ipa = None
        
    try:
        indonesia = Category.objects.get(category_name__icontains='indonesia')
    except Category.DoesNotExist:
        indonesia = None
        
    try:
        inggris = Category.objects.get(category_name__icontains='inggris')
    except Category.DoesNotExist:
        inggris = None
    
    available_categories = [cat for cat in [matematika, ipa, indonesia, inggris] if cat is not None]
    
    if len(available_categories) < 2:
        print("❌ Perlu minimal 2 kategori untuk membuat paket tryout")
        print("Kategori yang tersedia:")
        for cat in Category.objects.all():
            print(f"  - {cat.category_name} ({cat.get_question_count()} soal)")
        return
    
    print(f"✓ Ditemukan {len(available_categories)} kategori")
    
    # Sample Package 1: UTBK Saintek
    if len(available_categories) >= 2:
        package1, created = TryoutPackage.objects.get_or_create(
            package_name='UTBK Saintek 2025',
            defaults={
                'description': 'Simulasi UTBK Saintek dengan komposisi sesuai aturan resmi UTBK',
                'total_time': 180,  # 3 jam
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Configure categories for Saintek package
            categories_config = []
            
            if matematika:
                categories_config.append({
                    'category': matematika,
                    'question_count': min(15, matematika.get_question_count()),
                    'max_score': 300,
                    'order': 1
                })
            
            if ipa:
                categories_config.append({
                    'category': ipa,
                    'question_count': min(20, ipa.get_question_count()),
                    'max_score': 400,
                    'order': 2
                })
            
            if indonesia:
                categories_config.append({
                    'category': indonesia,
                    'question_count': min(15, indonesia.get_question_count()),
                    'max_score': 200,
                    'order': 3
                })
                
            if inggris:
                categories_config.append({
                    'category': inggris,
                    'question_count': min(10, inggris.get_question_count()),
                    'max_score': 100,
                    'order': 4
                })
            
            # Add remaining categories to reach 1000 points
            total_assigned = sum([config['max_score'] for config in categories_config])
            remaining = 1000 - total_assigned
            
            if remaining > 0 and len(categories_config) > 0:
                # Distribute remaining points to first category
                categories_config[0]['max_score'] += remaining
            
            for config in categories_config:
                TryoutPackageCategory.objects.create(
                    package=package1,
                    **config
                )
            
            print(f"✓ Paket '{package1.package_name}' dibuat dengan {len(categories_config)} kategori")
            print(f"  Total soal: {package1.get_total_questions()}")
            print(f"  Total skor: {package1.get_total_max_score()}")
    
    # Sample Package 2: UTBK Soshum (if we have enough categories)
    if len(available_categories) >= 3:
        package2, created = TryoutPackage.objects.get_or_create(
            package_name='UTBK Soshum 2025',
            defaults={
                'description': 'Simulasi UTBK Soshum untuk jurusan sosial dan humaniora',
                'total_time': 180,  # 3 jam
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Configure categories for Soshum package (different composition)
            categories_config = []
            
            if indonesia:
                categories_config.append({
                    'category': indonesia,
                    'question_count': min(20, indonesia.get_question_count()),
                    'max_score': 400,
                    'order': 1
                })
                
            if inggris:
                categories_config.append({
                    'category': inggris,
                    'question_count': min(15, inggris.get_question_count()),
                    'max_score': 300,
                    'order': 2
                })
            
            if matematika:
                categories_config.append({
                    'category': matematika,
                    'question_count': min(15, matematika.get_question_count()),
                    'max_score': 300,
                    'order': 3
                })
            
            # Add remaining categories to reach 1000 points
            total_assigned = sum([config['max_score'] for config in categories_config])
            remaining = 1000 - total_assigned
            
            if remaining > 0 and len(categories_config) > 0:
                # Distribute remaining points to first category
                categories_config[0]['max_score'] += remaining
            
            for config in categories_config:
                TryoutPackageCategory.objects.create(
                    package=package2,
                    **config
                )
            
            print(f"✓ Paket '{package2.package_name}' dibuat dengan {len(categories_config)} kategori")
            print(f"  Total soal: {package2.get_total_questions()}")
            print(f"  Total skor: {package2.get_total_max_score()}")
    
    # Sample Package 3: Try Out Singkat
    if len(available_categories) >= 2:
        package3, created = TryoutPackage.objects.get_or_create(
            package_name='Try Out Singkat',
            defaults={
                'description': 'Try out singkat untuk latihan cepat dengan waktu terbatas',
                'total_time': 90,  # 1.5 jam
                'is_active': True,
                'created_by': admin_user
            }
        )
        
        if created:
            # Configure categories for short package
            categories_config = []
            
            # Take first two categories and distribute evenly
            for i, category in enumerate(available_categories[:2]):
                categories_config.append({
                    'category': category,
                    'question_count': min(10, category.get_question_count()),
                    'max_score': 500,
                    'order': i + 1
                })
            
            for config in categories_config:
                TryoutPackageCategory.objects.create(
                    package=package3,
                    **config
                )
            
            print(f"✓ Paket '{package3.package_name}' dibuat dengan {len(categories_config)} kategori")
            print(f"  Total soal: {package3.get_total_questions()}")
            print(f"  Total skor: {package3.get_total_max_score()}")

def main():
    print("🚀 Membuat contoh paket tryout...")
    print("=" * 50)
    
    create_sample_packages()
    
    print("=" * 50)
    print("✅ Selesai! Paket tryout berhasil dibuat.")
    
    # Show summary
    packages = TryoutPackage.objects.all()
    print(f"\n📊 Total paket tryout: {packages.count()}")
    
    for package in packages:
        print(f"\n📦 {package.package_name}")
        print(f"   Status: {'✅ Siap digunakan' if package.can_be_taken() else '⚠️ Perlu perbaikan'}")
        print(f"   Soal: {package.get_total_questions()}")
        print(f"   Skor: {package.get_total_max_score()}/1000")
        print(f"   Waktu: {package.total_time} menit")
        print(f"   Kategori: {package.tryoutpackagecategory_set.count()}")

if __name__ == '__main__':
    main()
