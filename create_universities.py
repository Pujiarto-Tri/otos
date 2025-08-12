#!/usr/bin/env python
"""
Script untuk membuat data universitas default
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import University

def create_universities():
    """Create default universities"""
    universities_data = [
        # Tier 1 Universities (Top)
        {
            'name': 'Universitas Indonesia',
            'location': 'Jakarta',
            'website': 'https://ui.ac.id',
            'description': 'Universitas negeri terbaik di Indonesia dengan berbagai program studi unggulan.',
            'minimum_utbk_score': 650,
            'tier': 'tier1'
        },
        {
            'name': 'Institut Teknologi Bandung',
            'location': 'Bandung',
            'website': 'https://itb.ac.id',
            'description': 'Institut teknologi terkemuka di Indonesia, khususnya untuk bidang teknik dan sains.',
            'minimum_utbk_score': 640,
            'tier': 'tier1'
        },
        {
            'name': 'Universitas Gadjah Mada',
            'location': 'Yogyakarta',
            'website': 'https://ugm.ac.id',
            'description': 'Universitas terkemuka dengan tradisi akademik yang kuat dan beragam program studi.',
            'minimum_utbk_score': 630,
            'tier': 'tier1'
        },
        {
            'name': 'Institut Pertanian Bogor',
            'location': 'Bogor',
            'website': 'https://ipb.ac.id',
            'description': 'Institut pertanian terbaik di Indonesia dengan fokus pada sains dan teknologi pertanian.',
            'minimum_utbk_score': 620,
            'tier': 'tier1'
        },
        {
            'name': 'Institut Teknologi Sepuluh Nopember',
            'location': 'Surabaya',
            'website': 'https://its.ac.id',
            'description': 'Institut teknologi terkemuka di Indonesia Timur dengan program teknik yang unggul.',
            'minimum_utbk_score': 610,
            'tier': 'tier1'
        },
        
        # Tier 2 Universities (Good)
        {
            'name': 'Universitas Brawijaya',
            'location': 'Malang',
            'website': 'https://ub.ac.id',
            'description': 'Universitas negeri terkemuka di Jawa Timur dengan berbagai program studi berkualitas.',
            'minimum_utbk_score': 550,
            'tier': 'tier2'
        },
        {
            'name': 'Universitas Diponegoro',
            'location': 'Semarang',
            'website': 'https://undip.ac.id',
            'description': 'Universitas negeri terkemuka di Jawa Tengah dengan reputasi akademik yang baik.',
            'minimum_utbk_score': 540,
            'tier': 'tier2'
        },
        {
            'name': 'Universitas Airlangga',
            'location': 'Surabaya',
            'website': 'https://unair.ac.id',
            'description': 'Universitas negeri terkemuka dengan program kedokteran dan sains yang unggul.',
            'minimum_utbk_score': 530,
            'tier': 'tier2'
        },
        {
            'name': 'Universitas Padjadjaran',
            'location': 'Bandung',
            'website': 'https://unpad.ac.id',
            'description': 'Universitas negeri terkemuka di Jawa Barat dengan berbagai program studi unggulan.',
            'minimum_utbk_score': 520,
            'tier': 'tier2'
        },
        {
            'name': 'Universitas Sebelas Maret',
            'location': 'Surakarta',
            'website': 'https://uns.ac.id',
            'description': 'Universitas negeri dengan program studi berkualitas dan fasilitas yang memadai.',
            'minimum_utbk_score': 510,
            'tier': 'tier2'
        },
        
        # Tier 3 Universities (Standard)
        {
            'name': 'Universitas Negeri Jakarta',
            'location': 'Jakarta',
            'website': 'https://unj.ac.id',
            'description': 'Universitas negeri dengan fokus pada pendidikan dan berbagai program studi.',
            'minimum_utbk_score': 450,
            'tier': 'tier3'
        },
        {
            'name': 'Universitas Jember',
            'location': 'Jember',
            'website': 'https://unej.ac.id',
            'description': 'Universitas negeri dengan program studi yang beragam dan berkualitas.',
            'minimum_utbk_score': 440,
            'tier': 'tier3'
        },
        {
            'name': 'Universitas Lampung',
            'location': 'Bandar Lampung',
            'website': 'https://unila.ac.id',
            'description': 'Universitas negeri terkemuka di Sumatera dengan berbagai program studi.',
            'minimum_utbk_score': 430,
            'tier': 'tier3'
        },
        {
            'name': 'Universitas Riau',
            'location': 'Pekanbaru',
            'website': 'https://unri.ac.id',
            'description': 'Universitas negeri di Sumatera dengan program studi yang berkembang.',
            'minimum_utbk_score': 420,
            'tier': 'tier3'
        },
        {
            'name': 'Universitas Bengkulu',
            'location': 'Bengkulu',
            'website': 'https://unib.ac.id',
            'description': 'Universitas negeri dengan komitmen pada pendidikan berkualitas.',
            'minimum_utbk_score': 410,
            'tier': 'tier3'
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for data in universities_data:
        university, created = University.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        
        if created:
            created_count += 1
            print(f"✓ Created: {university.name}")
        else:
            # Update existing university
            for key, value in data.items():
                setattr(university, key, value)
            university.save()
            updated_count += 1
            print(f"⟳ Updated: {university.name}")
    
    print(f"\n🎉 Summary:")
    print(f"Created: {created_count} universities")
    print(f"Updated: {updated_count} universities")
    print(f"Total: {University.objects.count()} universities in database")

if __name__ == '__main__':
    create_universities()
