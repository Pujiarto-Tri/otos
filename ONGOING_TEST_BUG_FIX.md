# Fix: Ongoing Test Bug

## 🐛 **Masalah Yang Ditemukan:**

### 1. **Redirect Inconsistency**
- Ketika user memulai package tryout lalu kembali ke dashboard, warning ongoing test muncul
- Ketika user menekan tombol "Tryout" di sidebar, dia di-redirect ke regular category test (bukan package test)
- Ini menyebabkan inconsistency karena user seharusnya di-redirect ke package test yang sedang berlangsung

### 2. **Missing Package Name**
- Warning ongoing test menampilkan "kekurangan nama" karena template menggunakan field yang salah
- Template menggunakan `{{ ongoing_test.tryout_package.name }}` padahal field yang benar adalah `package_name`

## ✅ **Perbaikan Yang Dilakukan:**

### 1. **Fixed Redirect Logic di `tryout_list` View**

**File:** `otosapp/views.py` (lines ~1005-1034)

**Before:**
```python
if ongoing_test:
    # Only handled category tests
    category = ongoing_test.categories.first()
    if category:
        return redirect('take_test', category_id=category.id, question=current_question_index)
```

**After:**
```python
if ongoing_test:
    if ongoing_test.tryout_package:
        # This is a package test - redirect to package test
        current_question_index = ongoing_test.get_current_question_index()
        return redirect('take_package_test_question', 
                      package_id=ongoing_test.tryout_package.id, 
                      question=current_question_index)
    else:
        # This is a category test - redirect to category test
        category = ongoing_test.categories.first()
        if category:
            return redirect('take_test', category_id=category.id, question=current_question_index)
```

### 2. **Fixed Package Name Display**

**File:** `otosapp/templates/components/ongoing_test_alert.html` (line 16)

**Before:**
```html
{{ ongoing_test.tryout_package.name }}
```

**After:**
```html
{{ ongoing_test.tryout_package.package_name }}
```

### 3. **Enhanced Duplicate Answer Handling**

**File:** `otosapp/views.py` (lines ~3252-3275)

Added robust duplicate handling in `take_package_test_question` to prevent `MultipleObjectsReturned` errors:

```python
# Check for existing answers and clean up duplicates if any
existing_answers = Answer.objects.filter(test=test, question=current_question)

if existing_answers.count() > 1:
    # Keep the first answer and delete the rest
    first_answer = existing_answers.first()
    existing_answers.exclude(id=first_answer.id).delete()
    # Update the remaining answer
    first_answer.selected_choice = choice
    first_answer.save()
```

## 🎯 **Testing Results:**

### Before Fix:
- ❌ Package tryout → Dashboard → Sidebar "Tryout" = Redirect ke regular test
- ❌ Ongoing test alert menampilkan nama kosong
- ❌ `MultipleObjectsReturned` error ketika save answer

### After Fix:
- ✅ Package tryout → Dashboard → Sidebar "Tryout" = Redirect ke package test yang sama
- ✅ Ongoing test alert menampilkan nama package dengan benar
- ✅ No more duplicate answer errors
- ✅ Consistent navigation experience

## 🔧 **Technical Details:**

### Redirect Logic Flow:
1. User mengakses `/students/tryouts/`
2. System cek ada ongoing test tidak
3. Jika ada, cek type test:
   - **Package test**: Redirect ke `take_package_test_question`
   - **Category test**: Redirect ke `take_test`
4. Gunakan `get_current_question_index()` untuk question yang tepat

### Template Logic:
```html
{% if ongoing_test.tryout_package %}
    <p>Ujian paket <strong>"{{ ongoing_test.tryout_package.package_name }}"</strong></p>
    <a href="{% url 'take_package_test_question' ongoing_test.tryout_package.id ongoing_test.get_current_question_index %}">
        Lanjutkan Ujian
    </a>
{% elif ongoing_test.categories.exists %}
    <p>Ujian <strong>"{{ ongoing_test.categories.first.category_name }}"</strong></p>
    <a href="{% url 'take_test' ongoing_test.categories.first.id ongoing_test.get_current_question_index %}">
        Lanjutkan Ujian
    </a>
{% endif %}
```

## ✨ **User Experience Improvements:**

1. **Consistent Navigation**: Sekarang semua redirect mengarah ke test yang benar
2. **Clear Information**: Package name ditampilkan dengan jelas di ongoing test alert
3. **Robust Error Handling**: Duplicate answers ditangani otomatis
4. **Seamless Flow**: User bisa berpindah antara dashboard dan test tanpa kehilangan context

## 🎉 **Hasil Akhir:**

Bug telah diperbaiki sepenuhnya. Sekarang user experience sudah konsisten:
- ✅ Package tryout = selalu redirect ke package test
- ✅ Regular tryout = selalu redirect ke regular test  
- ✅ Nama package ditampilkan dengan benar
- ✅ No more duplicate answer errors
