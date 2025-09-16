// Notification System for Admin Interface
class NotificationManager {
  constructor() {
    this.container = null;
    this.notifications = new Map();
    this.notificationId = 0;
    this.defaultDuration = 5000; // 5 seconds
    
    this.initialize();
  }

  // Initialize notification container
  initialize() {
    this.createContainer();
  }

  // Create notification container
  createContainer() {
    if (document.getElementById('notification-container')) return;
    
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.className = 'fixed top-4 right-4 z-50 space-y-2';
    container.style.pointerEvents = 'none';
    
    document.body.appendChild(container);
    this.container = container;
  }

  // Show notification
  show(message, type = 'info', duration = null) {
    if (!this.container) this.createContainer();
    
    const id = ++this.notificationId;
    const notification = this.createNotification(id, message, type);
    
    this.container.appendChild(notification);
    this.notifications.set(id, notification);
    
    // Animate in
    requestAnimationFrame(() => {
      notification.classList.add('show');
    });
    
    // Auto dismiss
    const dismissTime = duration || this.defaultDuration;
    if (dismissTime > 0) {
      setTimeout(() => {
        this.dismiss(id);
      }, dismissTime);
    }
    
    return id;
  }

  // Create notification element
  createNotification(id, message, type) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.pointerEvents = 'auto';
    
    const config = this.getTypeConfig(type);
    
    notification.innerHTML = `
      <div class="flex items-start">
        <div class="flex-shrink-0">
          ${config.icon}
        </div>
        <div class="ml-3 flex-1">
          <p class="text-sm font-medium ${config.textColor}">
            ${message}
          </p>
        </div>
        <div class="ml-4 flex-shrink-0 flex">
          <button 
            type="button" 
            class="inline-flex ${config.textColor} hover:opacity-75 focus:outline-none"
            onclick="notificationManager.dismiss(${id})"
          >
            <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    `;
    
    return notification;
  }

  // Get configuration for notification type
  getTypeConfig(type) {
    const configs = {
      success: {
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-800',
        icon: `
          <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
        `
      },
      error: {
        bgColor: 'bg-red-50',
        borderColor: 'border-red-200',
        textColor: 'text-red-800',
        icon: `
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        `
      },
      warning: {
        bgColor: 'bg-yellow-50',
        borderColor: 'border-yellow-200',
        textColor: 'text-yellow-800',
        icon: `
          <svg class="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        `
      },
      info: {
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200',
        textColor: 'text-blue-800',
        icon: `
          <svg class="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
        `
      }
    };
    
    const config = configs[type] || configs.info;
    
    // Apply styling to the notification
    setTimeout(() => {
      const notification = this.container.lastElementChild;
      if (notification) {
        notification.className += ` ${config.bgColor} ${config.borderColor} border rounded-lg p-4 shadow-lg transform transition-all duration-300 ease-in-out translate-x-full opacity-0`;
        notification.classList.add('notification-enter');
      }
    }, 0);
    
    return config;
  }

  // Dismiss notification
  dismiss(id) {
    const notification = this.notifications.get(id);
    if (!notification) return;
    
    // Animate out
    notification.classList.add('notification-exit');
    notification.style.transform = 'translateX(100%)';
    notification.style.opacity = '0';
    
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
      this.notifications.delete(id);
    }, 300);
  }

  // Clear all notifications
  clearAll() {
    this.notifications.forEach((notification, id) => {
      this.dismiss(id);
    });
  }

  // Shorthand methods
  success(message, duration) {
    return this.show(message, 'success', duration);
  }

  error(message, duration) {
    return this.show(message, 'error', duration);
  }

  warning(message, duration) {
    return this.show(message, 'warning', duration);
  }

  info(message, duration) {
    return this.show(message, 'info', duration);
  }
}

// Global instance and helper function
window.notificationManager = new NotificationManager();

// Global helper function (for backward compatibility)
window.showNotification = (message, type, duration) => {
  return window.notificationManager.show(message, type, duration);
};