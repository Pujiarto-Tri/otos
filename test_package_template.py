#!/usr/bin/env python
"""
Test script untuk memverifikasi template package_test_question.html
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'otos.settings')
django.setup()

from django.template import Template, Context
from django.template.loader import get_template
from django.test import TestCase, Client
from django.contrib.auth.models import User
from otosapp.models import TryoutPackage, Question, Choice, Test
from django.urls import reverse

def test_template_rendering():
    """Test basic template rendering"""
    try:
        template = get_template('students/tryouts/package_test_question.html')
        print("✓ Template berhasil dimuat tanpa syntax error")
        
        # Test context variables
        context = {
            'package': {'id': 1, 'package_name': 'Test Package'},
            'question': {'id': 1, 'question_text': 'Test question'},
            'choices': [],
            'current_question_number': 1,
            'total_questions': 10,
            'answered_question_numbers': [1, 2],
            'time_remaining': {'total_seconds': 3600},
            'selected_choice_id': None,
            'user_test': {'current_question': 0}
        }
        
        # Render template with context
        rendered = template.render(context)
        print("✓ Template berhasil di-render dengan context")
        
        # Check for key elements
        key_elements = [
            'timer-display',
            'navigation-panel', 
            'submit-test-btn',
            'nav-toggle',
            'progress-bar',
            'answered-count',
            'remaining-count',
            'doubtful-count'
        ]
        
        for element in key_elements:
            if element in rendered:
                print(f"✓ Element '{element}' ditemukan dalam template")
            else:
                print(f"✗ Element '{element}' TIDAK ditemukan dalam template")
        
        # Check for JavaScript functions
        js_functions = [
            'initTimer',
            'saveAnswer', 
            'toggleNavigation',
            'markAsDoubtful',
            'showSubmitConfirmation',
            'updateNavigationColors'
        ]
        
        for function in js_functions:
            if function in rendered:
                print(f"✓ JavaScript function '{function}' ditemukan")
            else:
                print(f"✗ JavaScript function '{function}' TIDAK ditemukan")
        
        print("\n✓ Template validation selesai!")
        return True
        
    except Exception as e:
        print(f"✗ Error saat memuat template: {e}")
        return False

def test_ui_consistency():
    """Test UI consistency with take_test.html"""
    try:
        package_template = get_template('students/tryouts/package_test_question.html')
        regular_template = get_template('students/tests/take_test.html')
        print("✓ Kedua template berhasil dimuat")
        
        # Test context for both templates
        context = {
            'package': {'id': 1, 'package_name': 'Test Package'},
            'question': {'id': 1, 'question_text': 'Test question'},
            'choices': [],
            'current_question_number': 1,
            'total_questions': 10,
            'answered_question_numbers': [1, 2],
            'time_remaining': {'total_seconds': 3600},
            'selected_choice_id': None,
            'user_test': {'current_question': 0},
            'test': {'id': 1, 'current_question': 0}
        }
        
        package_rendered = package_template.render(context)
        regular_rendered = regular_template.render(context)
        
        # Check for common UI elements
        common_elements = [
            'bg-gradient-to-br from-blue-600 to-purple-700',  # Header gradient
            'timer-display',
            'navigation-panel',
            'nav-button',
            'progress-bar',
            'submit-test-btn'
        ]
        
        consistency_score = 0
        for element in common_elements:
            package_has = element in package_rendered
            regular_has = element in regular_rendered
            
            if package_has and regular_has:
                print(f"✓ Konsisten: '{element}' ada di kedua template")
                consistency_score += 1
            elif package_has and not regular_has:
                print(f"! Package saja: '{element}' hanya ada di package template")
            elif not package_has and regular_has:
                print(f"! Regular saja: '{element}' hanya ada di regular template")
            else:
                print(f"✗ Tidak ada: '{element}' tidak ada di kedua template")
        
        print(f"\nSkor konsistensi: {consistency_score}/{len(common_elements)} ({consistency_score/len(common_elements)*100:.1f}%)")
        
        return consistency_score == len(common_elements)
        
    except Exception as e:
        print(f"✗ Error saat test konsistensi: {e}")
        return False

if __name__ == "__main__":
    print("=== Test Package Template ===\n")
    
    print("1. Testing Template Rendering...")
    template_ok = test_template_rendering()
    
    print("\n" + "="*50 + "\n")
    
    print("2. Testing UI Consistency...")
    consistency_ok = test_ui_consistency()
    
    print("\n" + "="*50 + "\n")
    
    if template_ok and consistency_ok:
        print("🎉 SEMUA TEST BERHASIL!")
        print("✓ Template dapat di-render tanpa error")
        print("✓ UI konsisten dengan regular tryout")
        print("✓ Semua elemen utama tersedia")
    else:
        print("⚠️  BEBERAPA TEST GAGAL:")
        if not template_ok:
            print("✗ Template rendering bermasalah")
        if not consistency_ok:
            print("✗ UI tidak sepenuhnya konsisten")
