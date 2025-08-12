#!/usr/bin/env python
"""
Script untuk membersihkan data Answer duplikasi
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from otosapp.models import Answer, Test
from django.db.models import Count

def clean_duplicate_answers():
    """Clean up duplicate Answer records"""
    print("🔍 Mencari data Answer duplikasi...")
    
    # Find tests with duplicate answers for the same question
    duplicate_groups = Answer.objects.values('test', 'question').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    total_duplicates = 0
    total_deleted = 0
    
    for group in duplicate_groups:
        test_id = group['test']
        question_id = group['question']
        count = group['count']
        
        print(f"\n📋 Test ID {test_id}, Question ID {question_id}: {count} jawaban duplikasi")
        
        # Get all answers for this test-question combination
        answers = Answer.objects.filter(
            test_id=test_id,
            question_id=question_id
        ).order_by('id')
        
        # Keep the first answer (oldest), delete the rest
        first_answer = answers.first()
        duplicates_to_delete = answers.exclude(id=first_answer.id)
        
        print(f"  ✅ Menyimpan: Answer ID {first_answer.id}")
        for dup in duplicates_to_delete:
            print(f"  🗑️ Menghapus: Answer ID {dup.id}")
            dup.delete()
            total_deleted += 1
        
        total_duplicates += 1
    
    print(f"\n🎉 Selesai!")
    print(f"📊 Total grup duplikasi ditemukan: {total_duplicates}")
    print(f"🗑️ Total record duplikasi dihapus: {total_deleted}")
    
    if total_duplicates == 0:
        print("✅ Tidak ada data duplikasi ditemukan!")
    else:
        print("✅ Semua duplikasi telah dibersihkan!")

def verify_cleanup():
    """Verify no duplicates remain"""
    print("\n🔍 Memverifikasi pembersihan...")
    
    remaining_duplicates = Answer.objects.values('test', 'question').annotate(
        count=Count('id')
    ).filter(count__gt=1)
    
    if remaining_duplicates.count() == 0:
        print("✅ Verifikasi berhasil: Tidak ada duplikasi tersisa!")
        return True
    else:
        print(f"⚠️ Masih ada {remaining_duplicates.count()} grup duplikasi tersisa!")
        return False

if __name__ == "__main__":
    print("=== Cleanup Answer Duplikasi ===\n")
    clean_duplicate_answers()
    verify_cleanup()
    print("\n" + "="*40)
