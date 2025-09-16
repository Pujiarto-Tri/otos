// Image Editor for Resize and Crop Functionality
class ImageEditor {
  constructor() {
    this.instances = new Map();
  }

  initialize(container, img) {
    const instance = {
      container,
      img,
      isSelected: false,
      isDragging: false,
      isCropMode: false,
      cropData: null,
      startX: 0,
      startY: 0,
      startWidth: 0,
      startHeight: 0
    };

    this.attachEventListeners(instance);
    this.instances.set(container, instance);
  }

  attachEventListeners(instance) {
    const { container, img } = instance;

    // Select image on click
    img.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      if (instance.isSelected) {
        return;
      }
      
      this.selectImage(instance);
    });
    
    // Add double-click for modal if not already set
    if (!img.hasAttribute('data-modal-handler')) {
      img.setAttribute('data-modal-handler', 'true');
      img.addEventListener('dblclick', (e) => {
        e.preventDefault();
        e.stopPropagation();
        window.openImageModal(img.src, 'Image Preview');
      });
    }

    // Deselect when clicking outside
    document.addEventListener('click', (e) => {
      if (!container.contains(e.target)) {
        this.deselectImage(instance);
      }
    });
  }

  selectImage(instance) {
    // Deselect other images first
    this.instances.forEach(otherInstance => {
      if (otherInstance !== instance) {
        this.deselectImage(otherInstance);
      }
    });

    instance.isSelected = true;
    instance.container.classList.add('selected');
    
    this.createResizeHandles(instance);
    this.createImageToolbar(instance);
    
    window.showNotification?.('Image selected! Use handles to resize, toolbar to crop, or double-click to preview', 'info');
  }

  deselectImage(instance) {
    instance.isSelected = false;
    instance.container.classList.remove('selected');
    
    // Remove resize handles
    const handles = instance.container.querySelector('.resize-handles');
    if (handles) handles.remove();
    
    // Remove toolbar
    const toolbar = instance.container.querySelector('.image-toolbar');
    if (toolbar) toolbar.remove();
    
    // Remove crop overlay if exists
    this.removeCropOverlay(instance);
  }

  createResizeHandles(instance) {
    const handles = document.createElement('div');
    handles.className = 'resize-handles';
    
    const handleTypes = ['nw', 'ne', 'sw', 'se', 'n', 's', 'w', 'e'];
    
    handleTypes.forEach(type => {
      const handle = document.createElement('div');
      handle.className = `resize-handle ${type}`;
      handle.addEventListener('mousedown', (e) => this.startResize(e, type, instance));
      handles.appendChild(handle);
    });
    
    instance.container.appendChild(handles);
  }

  createImageToolbar(instance) {
    const toolbar = document.createElement('div');
    toolbar.className = 'image-toolbar';
    
    const buttons = [
      { text: 'Reset', action: 'reset' },
      { text: 'Crop', action: 'crop' },
      { text: '25%', action: 'size', value: 25 },
      { text: '50%', action: 'size', value: 50 },
      { text: '75%', action: 'size', value: 75 },
      { text: '100%', action: 'size', value: 100 }
    ];
    
    buttons.forEach(btn => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = btn.text;
      button.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        this.handleToolbarAction(btn.action, btn.value, instance);
      });
      toolbar.appendChild(button);
    });
    
    instance.container.appendChild(toolbar);
  }

  handleToolbarAction(action, value, instance) {
    const { img } = instance;
    
    switch(action) {
      case 'reset':
        img.style.width = '';
        img.style.height = '';
        img.style.maxWidth = '100%';
        this.syncEditorContent(instance);
        window.showNotification?.('Image size reset to original', 'success');
        break;
      case 'crop':
        this.toggleCropMode(instance);
        break;
      case 'size':
        const originalWidth = img.naturalWidth;
        const newWidth = (originalWidth * value) / 100;
        img.style.width = newWidth + 'px';
        img.style.height = 'auto';
        this.syncEditorContent(instance);
        window.showNotification?.(`Image resized to ${value}%`, 'success');
        break;
    }
  }

  startResize(e, type, instance) {
    e.preventDefault();
    e.stopPropagation();
    
    instance.isDragging = true;
    instance.startX = e.clientX;
    instance.startY = e.clientY;
    
    const rect = instance.img.getBoundingClientRect();
    instance.startWidth = rect.width;
    instance.startHeight = rect.height;
    
    const onMouseMove = (e) => this.resize(e, type, instance);
    const onMouseUp = () => {
      instance.isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      this.syncEditorContent(instance);
    };
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  resize(e, type, instance) {
    if (!instance.isDragging) return;
    
    const { img, startX, startY, startWidth, startHeight } = instance;
    const deltaX = e.clientX - startX;
    const deltaY = e.clientY - startY;
    
    let newWidth = startWidth;
    let newHeight = startHeight;
    
    switch(type) {
      case 'se':
      case 'e':
        newWidth = startWidth + deltaX;
        break;
      case 'sw':
      case 'w':
        newWidth = startWidth - deltaX;
        break;
      case 'ne':
        newWidth = startWidth + deltaX;
        break;
      case 'nw':
        newWidth = startWidth - deltaX;
        break;
      case 's':
        newHeight = startHeight + deltaY;
        newWidth = (newHeight * img.naturalWidth) / img.naturalHeight;
        break;
      case 'n':
        newHeight = startHeight - deltaY;
        newWidth = (newHeight * img.naturalWidth) / img.naturalHeight;
        break;
    }
    
    // Maintain aspect ratio for corner handles
    if (['se', 'sw', 'ne', 'nw'].includes(type)) {
      newHeight = (newWidth * img.naturalHeight) / img.naturalWidth;
    }
    
    // Set minimum size
    newWidth = Math.max(50, newWidth);
    newHeight = Math.max(50, newHeight);
    
    img.style.width = newWidth + 'px';
    img.style.height = newHeight + 'px';
  }

  toggleCropMode(instance) {
    if (instance.isCropMode) {
      this.applyCrop(instance);
      this.removeCropOverlay(instance);
      instance.isCropMode = false;
    } else {
      this.createCropOverlay(instance);
      instance.isCropMode = true;
    }
  }

  createCropOverlay(instance) {
    const { container, img } = instance;
    const rect = img.getBoundingClientRect();
    
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'crop-overlay';
    
    // Create crop area (start with 80% of image)
    const cropArea = document.createElement('div');
    cropArea.className = 'crop-area';
    const cropWidth = rect.width * 0.8;
    const cropHeight = rect.height * 0.8;
    const cropLeft = (rect.width - cropWidth) / 2;
    const cropTop = (rect.height - cropHeight) / 2;
    
    cropArea.style.left = cropLeft + 'px';
    cropArea.style.top = cropTop + 'px';
    cropArea.style.width = cropWidth + 'px';
    cropArea.style.height = cropHeight + 'px';
    
    // Add crop handles
    const handleTypes = ['nw', 'ne', 'sw', 'se'];
    handleTypes.forEach(type => {
      const handle = document.createElement('div');
      handle.className = `crop-handle ${type}`;
      handle.addEventListener('mousedown', (e) => this.startCropResize(e, type, cropArea, instance));
      cropArea.appendChild(handle);
    });
    
    // Add drag functionality for crop area
    cropArea.addEventListener('mousedown', (e) => {
      if (e.target === cropArea) {
        this.startCropDrag(e, cropArea, instance);
      }
    });
    
    overlay.appendChild(cropArea);
    container.appendChild(overlay);
    
    // Store crop data
    instance.cropData = { left: cropLeft, top: cropTop, width: cropWidth, height: cropHeight };
    
    // Update toolbar button
    const toolbar = container.querySelector('.image-toolbar');
    const cropBtn = Array.from(toolbar.children).find(btn => btn.textContent === 'Crop');
    if (cropBtn) {
      cropBtn.textContent = 'Apply';
      cropBtn.classList.add('active');
    }
  }

  removeCropOverlay(instance) {
    const overlay = instance.container.querySelector('.crop-overlay');
    if (overlay) overlay.remove();
    
    // Reset toolbar button
    const toolbar = instance.container.querySelector('.image-toolbar');
    if (toolbar) {
      const cropBtn = Array.from(toolbar.children).find(btn => btn.textContent === 'Apply');
      if (cropBtn) {
        cropBtn.textContent = 'Crop';
        cropBtn.classList.remove('active');
      }
    }
  }

  applyCrop(instance) {
    if (!instance.cropData) return;
    
    const { img } = instance;
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Calculate crop ratios
    const scaleX = img.naturalWidth / img.offsetWidth;
    const scaleY = img.naturalHeight / img.offsetHeight;
    
    const cropX = instance.cropData.left * scaleX;
    const cropY = instance.cropData.top * scaleY;
    const cropWidth = instance.cropData.width * scaleX;
    const cropHeight = instance.cropData.height * scaleY;
    
    canvas.width = cropWidth;
    canvas.height = cropHeight;
    
    // Create new image for cropping
    const tempImg = new Image();
    tempImg.crossOrigin = 'anonymous';
    tempImg.onload = () => {
      ctx.drawImage(tempImg, cropX, cropY, cropWidth, cropHeight, 0, 0, cropWidth, cropHeight);
      
      // Convert to blob and create new URL
      canvas.toBlob((blob) => {
        const newUrl = URL.createObjectURL(blob);
        img.src = newUrl;
        img.style.width = instance.cropData.width + 'px';
        img.style.height = instance.cropData.height + 'px';
        
        this.syncEditorContent(instance);
        window.showNotification?.('Image cropped successfully!', 'success');
      }, 'image/png');
    };
    tempImg.src = img.src;
    
    instance.cropData = null;
  }

  startCropResize(e, type, cropArea, instance) {
    e.preventDefault();
    e.stopPropagation();
    
    instance.isDragging = true;
    instance.startX = e.clientX;
    instance.startY = e.clientY;
    
    const rect = cropArea.getBoundingClientRect();
    instance.startWidth = rect.width;
    instance.startHeight = rect.height;
    
    const onMouseMove = (e) => {
      if (!instance.isDragging) return;
      
      const deltaX = e.clientX - instance.startX;
      const deltaY = e.clientY - instance.startY;
      const imgRect = instance.img.getBoundingClientRect();
      
      let newWidth = instance.startWidth;
      let newHeight = instance.startHeight;
      let newLeft = parseFloat(cropArea.style.left);
      let newTop = parseFloat(cropArea.style.top);
      
      switch(type) {
        case 'se':
          newWidth = instance.startWidth + deltaX;
          newHeight = instance.startHeight + deltaY;
          break;
        case 'sw':
          newWidth = instance.startWidth - deltaX;
          newHeight = instance.startHeight + deltaY;
          newLeft = parseFloat(cropArea.style.left) + deltaX;
          break;
        case 'ne':
          newWidth = instance.startWidth + deltaX;
          newHeight = instance.startHeight - deltaY;
          newTop = parseFloat(cropArea.style.top) + deltaY;
          break;
        case 'nw':
          newWidth = instance.startWidth - deltaX;
          newHeight = instance.startHeight - deltaY;
          newLeft = parseFloat(cropArea.style.left) + deltaX;
          newTop = parseFloat(cropArea.style.top) + deltaY;
          break;
      }
      
      // Constrain to image bounds
      newWidth = Math.max(50, Math.min(newWidth, imgRect.width - newLeft));
      newHeight = Math.max(50, Math.min(newHeight, imgRect.height - newTop));
      newLeft = Math.max(0, Math.min(newLeft, imgRect.width - newWidth));
      newTop = Math.max(0, Math.min(newTop, imgRect.height - newHeight));
      
      cropArea.style.width = newWidth + 'px';
      cropArea.style.height = newHeight + 'px';
      cropArea.style.left = newLeft + 'px';
      cropArea.style.top = newTop + 'px';
      
      // Update crop data
      instance.cropData = { left: newLeft, top: newTop, width: newWidth, height: newHeight };
    };
    
    const onMouseUp = () => {
      instance.isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  startCropDrag(e, cropArea, instance) {
    e.preventDefault();
    e.stopPropagation();
    
    instance.isDragging = true;
    instance.startX = e.clientX;
    instance.startY = e.clientY;
    
    const startLeft = parseFloat(cropArea.style.left);
    const startTop = parseFloat(cropArea.style.top);
    
    const onMouseMove = (e) => {
      if (!instance.isDragging) return;
      
      const deltaX = e.clientX - instance.startX;
      const deltaY = e.clientY - instance.startY;
      const imgRect = instance.img.getBoundingClientRect();
      const cropRect = cropArea.getBoundingClientRect();
      
      let newLeft = startLeft + deltaX;
      let newTop = startTop + deltaY;
      
      // Constrain to image bounds
      newLeft = Math.max(0, Math.min(newLeft, imgRect.width - cropRect.width));
      newTop = Math.max(0, Math.min(newTop, imgRect.height - cropRect.height));
      
      cropArea.style.left = newLeft + 'px';
      cropArea.style.top = newTop + 'px';
      
      // Update crop data
      instance.cropData = { 
        left: newLeft, 
        top: newTop, 
        width: parseFloat(cropArea.style.width), 
        height: parseFloat(cropArea.style.height) 
      };
    };
    
    const onMouseUp = () => {
      instance.isDragging = false;
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };
    
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }

  syncEditorContent(instance) {
    // Find the parent editor
    const editor = instance.container.closest('[data-wysiwyg="true"]');
    if (!editor) return;
    
    // Update corresponding textarea
    let textarea = null;
    if (editor.id === 'wysiwyg-question-text-admin') {
      textarea = document.querySelector('#id_question_text');
    } else if (editor.id === 'wysiwyg-explanation-text-admin') {
      textarea = document.querySelector('#id_explanation');
    } else if (editor.id.startsWith('wysiwyg-choice-text-')) {
      const choiceNumber = editor.id.split('-').pop();
      const choiceIndex = parseInt(choiceNumber) - 1;
      textarea = document.querySelector(`#id_choices-${choiceIndex}-choice_text`);
    }
    
    if (textarea) {
      textarea.value = editor.innerHTML;
    }
    
    // Trigger input event
    editor.dispatchEvent(new Event('input', { bubbles: true }));
  }

  initializeExistingImages() {
    document.querySelectorAll('.wysiwyg-editor img').forEach(img => {
      if (!img.closest('.resizable-image')) {
        const container = document.createElement('div');
        container.className = 'resizable-image';
        img.parentNode.insertBefore(container, img);
        container.appendChild(img);
        
        // Remove existing onclick handler if present
        if (img.onclick) {
          const originalSrc = img.src;
          img.onclick = null;
          
          // Add double-click handler for modal
          img.addEventListener('dblclick', function(e) {
            e.preventDefault();
            e.stopPropagation();
            window.openImageModal(originalSrc, 'Image Preview');
          });
        }
        
        // Remove any existing click event listeners by cloning the node
        const newImg = img.cloneNode(true);
        img.parentNode.replaceChild(newImg, img);
        
        // Re-add double-click handler after cloning
        newImg.addEventListener('dblclick', function(e) {
          e.preventDefault();
          e.stopPropagation();
          window.openImageModal(newImg.src, 'Image Preview');
        });
        
        this.initialize(container, newImg);
      }
    });
  }
}

// Global instance
window.imageEditor = new ImageEditor();