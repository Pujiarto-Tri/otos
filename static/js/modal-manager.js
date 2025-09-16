// Modal Management for Admin Interface
class ModalManager {
  constructor() {
    this.activeModal = null;
    this.modalStack = [];
  }

  // Initialize all modal functionality
  initialize() {
    this.initializeImageModal();
    this.initializeCloseHandlers();
  }

  // Initialize image modal specifically
  initializeImageModal() {
    // Create image modal if it doesn't exist
    if (!document.getElementById('imageModal')) {
      this.createImageModal();
    }
  }

  // Create the image modal structure
  createImageModal() {
    const modalHTML = `
      <div id="imageModal" class="fixed inset-0 z-50 hidden overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true"></div>
          <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
          <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div class="sm:flex sm:items-start">
                <div class="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4" id="modal-title">
                    Image Preview
                  </h3>
                  <div class="mt-2 text-center">
                    <img id="modalImage" src="" alt="Preview" class="max-w-full max-h-96 mx-auto rounded">
                  </div>
                </div>
              </div>
            </div>
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button type="button" 
                      class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                      onclick="modalManager.closeModal()">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
  }

  // Open image modal with specific image
  openImageModal(src, title = 'Image Preview') {
    const modal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalTitle = document.getElementById('modal-title');
    
    if (!modal || !modalImage) return;
    
    modalImage.src = src;
    modalTitle.textContent = title;
    
    this.openModal(modal);
  }

  // Generic modal opener
  openModal(modalElement) {
    if (this.activeModal) {
      this.modalStack.push(this.activeModal);
    }
    
    this.activeModal = modalElement;
    modalElement.classList.remove('hidden');
    document.body.classList.add('overflow-hidden');
    
    // Focus trap
    this.trapFocus(modalElement);
  }

  // Close the current modal
  closeModal() {
    if (!this.activeModal) return;
    
    this.activeModal.classList.add('hidden');
    this.activeModal = null;
    
    // Restore previous modal if any
    if (this.modalStack.length > 0) {
      this.activeModal = this.modalStack.pop();
    } else {
      document.body.classList.remove('overflow-hidden');
    }
  }

  // Close all modals
  closeAllModals() {
    this.modalStack = [];
    if (this.activeModal) {
      this.activeModal.classList.add('hidden');
      this.activeModal = null;
    }
    document.body.classList.remove('overflow-hidden');
  }

  // Initialize close handlers (ESC key, overlay click)
  initializeCloseHandlers() {
    // ESC key handler
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.activeModal) {
        this.closeModal();
      }
    });

    // Click outside handler
    document.addEventListener('click', (e) => {
      if (this.activeModal && e.target === this.activeModal) {
        this.closeModal();
      }
    });
  }

  // Focus trap for accessibility
  trapFocus(modal) {
    const focusableElements = modal.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    // Focus first element
    firstElement.focus();
    
    // Handle tab navigation
    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    });
  }

  // Check if any modal is currently open
  isModalOpen() {
    return this.activeModal !== null;
  }

  // Get the currently active modal
  getActiveModal() {
    return this.activeModal;
  }
}

// Global instance and helper function
window.modalManager = new ModalManager();

// Global helper function for opening image modal (for backward compatibility)
window.openImageModal = (src, title) => {
  window.modalManager.openImageModal(src, title);
};