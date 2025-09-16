# Dokumentasi Fitur Image Resize & Crop untuk WYSIWYG Editor

## Overview
Fitur ini menambahkan kemampuan untuk resize dan crop gambar langsung di dalam Flowbite WYSIWYG editor tanpa perlu menggunakan TipTap atau library eksternal lainnya.

## Fitur yang Ditambahkan

### 1. Image Resize
- **Resize handles**: 8 handle resize (north, south, east, west, northeast, northwest, southeast, southwest)
- **Proportional resize**: Mempertahankan aspect ratio gambar
- **Minimum size**: Mencegah gambar menjadi terlalu kecil (minimum 50px)
- **Real-time resize**: Update langsung saat drag

### 2. Image Crop
- **Crop overlay**: Area gelap dengan selection box yang dapat dipindah dan diresize
- **Crop handles**: 4 corner handles untuk mengubah ukuran area crop
- **Drag to move**: Klik dan drag area crop untuk memindahkan posisi
- **Constrained cropping**: Area crop tidak bisa keluar dari batas gambar

### 3. Image Toolbar
- **Reset**: Mengembalikan ukuran gambar ke ukuran original
- **Crop**: Toggle mode crop on/off dan apply crop
- **Size presets**: 25%, 50%, 75%, 100% dari ukuran original

### 4. Integration
- **Auto-sync**: Perubahan gambar langsung tersinkronisasi dengan textarea hidden
- **Event handling**: Trigger input events untuk compatibility
- **Existing images**: Gambar yang sudah ada juga mendapat fitur resize/crop

## CSS Classes yang Ditambahkan

```css
.resizable-image          /* Container wrapper untuk gambar */
.resizable-image.selected /* State ketika gambar dipilih */
.resize-handles          /* Container untuk resize handles */
.resize-handle           /* Individual resize handle */
.resize-handle.nw/.ne/.sw/.se/.n/.s/.w/.e  /* Posisi handles */
.image-toolbar           /* Toolbar di atas gambar */
.crop-overlay            /* Dark overlay saat crop mode */
.crop-area               /* Selection area untuk crop */
.crop-handle             /* Handles untuk resize crop area */
```

## JavaScript Functions

### Core Functions
- `initializeImageEditor(container, img)` - Initialize resize/crop untuk gambar
- `selectImage(container)` - Select gambar dan tampilkan controls
- `deselectImage(container)` - Deselect gambar dan hide controls

### Resize Functions
- `createResizeHandles(container)` - Buat resize handles
- `startResize(e, type, container)` - Mulai resize operation
- `resize(e, type, container)` - Handle resize drag

### Crop Functions
- `toggleCropMode(container)` - Toggle crop mode on/off
- `createCropOverlay(container)` - Buat crop overlay dan selection
- `applyCrop(container)` - Apply crop menggunakan Canvas API
- `startCropResize(e, type, cropArea, container)` - Resize crop area
- `startCropDrag(e, cropArea, container)` - Drag crop area

### Utility Functions
- `createImageToolbar(container)` - Buat toolbar dengan buttons
- `handleToolbarAction(action, value, container)` - Handle toolbar clicks
- `syncEditorContent(container)` - Sync ke textarea
- `initializeExistingImages()` - Initialize existing images

## Usage

### Untuk Gambar Baru
Gambar yang diupload melalui button "Upload Image" akan otomatis mendapat fitur resize/crop.

### Untuk Gambar Existing
Panggil `initializeExistingImages()` saat page load untuk memberikan fitur pada gambar yang sudah ada.

### Interaksi User
1. **Select**: Klik gambar untuk select dan menampilkan controls
2. **Resize**: Drag salah satu dari 8 resize handles
3. **Quick resize**: Klik button 25%, 50%, 75%, atau 100%
4. **Crop**: Klik "Crop" untuk masuk crop mode, adjust area, klik "Apply"
5. **Reset**: Klik "Reset" untuk kembali ke ukuran original
6. **Deselect**: Klik di luar gambar untuk hide controls

## Technical Details

### Crop Implementation
- Menggunakan HTML5 Canvas API untuk actual cropping
- Menghitung scaling ratio antara display size dan natural size
- Generate blob baru dan update image source
- Mempertahankan aspect ratio dan constraint dalam bounds

### Integration dengan Flowbite WYSIWYG
- Tidak mengubah struktur editor yang existing
- Compatible dengan sistem textarea sync yang ada
- Trigger events yang sama seperti editing normal
- Mendukung multiple editors di satu halaman

### Browser Compatibility
- Modern browsers yang support Canvas API
- ES6+ features (arrow functions, const/let)
- Event delegation untuk dynamic content

## Deployment
File sudah diupdate di:
`otosapp/templates/admin/manage_questions/question_form.html`

Tidak perlu dependency tambahan atau file terpisah.