// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('SaaS POS System loaded');
    
    // Initialize Bootstrap components
    initBootstrapComponents();
    
    // Initialize theme
    initTheme();
    
    // Initialize auto-fade messages
    initAutoFadeMessages();
    
    // Initialize custom color picker
    initColorPicker();
    
    // Initialize counters animation
    initCounters();
});

function initBootstrapComponents() {
    // Tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Modals
    var modals = document.querySelectorAll('.modal');
    modals.forEach(function(modal) {
        modal.addEventListener('shown.bs.modal', function() {
            // Focus first input in modal
            var input = this.querySelector('input[type="text"], input[type="email"], input[type="password"]');
            if (input) input.focus();
        });
    });
}

// static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    console.log('SaaS POS System loaded');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide success/error messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Apply custom theme if saved
    function applyCustomTheme() {
        const savedTheme = localStorage.getItem('customTheme');
        if (savedTheme) {
            try {
                const theme = JSON.parse(savedTheme);
                const root = document.documentElement;
                
                if (theme.primary) root.style.setProperty('--primary-color', theme.primary);
                if (theme.secondary) root.style.setProperty('--secondary-color', theme.secondary);
                if (theme.success) root.style.setProperty('--success-color', theme.success);
                if (theme.danger) root.style.setProperty('--danger-color', theme.danger);
                if (theme.warning) root.style.setProperty('--warning-color', theme.warning);
                
                // Apply custom CSS
                if (theme.custom_css) {
                    let styleTag = document.getElementById('customThemeStyle');
                    if (!styleTag) {
                        styleTag = document.createElement('style');
                        styleTag.id = 'customThemeStyle';
                        document.head.appendChild(styleTag);
                    }
                    styleTag.textContent = theme.custom_css;
                }
            } catch (e) {
                console.error('Error applying custom theme:', e);
            }
        }
    }
    
    // Load and apply custom theme
    applyCustomTheme();
    
    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
});

// Utility function for showing loading indicators
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Processing...';
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

// Function to show toast notifications
function showToast(message, type = 'info') {
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="position-fixed bottom-0 end-0 p-3" style="z-index: 9999">
            <div class="toast show" role="alert">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">
                        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'}"></i>
                        ${type.charAt(0).toUpperCase() + type.slice(1)}
                    </strong>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', toastHtml);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.remove();
        }
    }, 5000);
}

// Fade in animation for elements
function fadeIn(element, duration = 500) {
    element.style.opacity = 0;
    element.style.display = 'block';
    
    let start = null;
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        const opacity = Math.min(progress / duration, 1);
        element.style.opacity = opacity;
        
        if (progress < duration) {
            window.requestAnimationFrame(animate);
        }
    }
    window.requestAnimationFrame(animate);
}

// Get CSRF token for AJAX requests
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function initTheme() {
    const themeSwitch = document.getElementById('themeSwitch');
    const themeSelect = document.getElementById('themeSelect');
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    const savedColor = localStorage.getItem('themeColor') || 'blue';
    
    // Apply saved theme
    document.documentElement.setAttribute('data-theme', savedTheme);
    document.documentElement.classList.add(`theme-${savedColor}`);
    
    // Set switch state
    if (themeSwitch) {
        themeSwitch.checked = savedTheme === 'dark';
        themeSwitch.addEventListener('change', function() {
            const newTheme = this.checked ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
    
    // Set color theme
    if (themeSelect) {
        themeSelect.value = savedColor;
        themeSelect.addEventListener('change', function() {
            const colors = ['blue', 'green', 'red', 'purple', 'orange'];
            colors.forEach(color => {
                document.documentElement.classList.remove(`theme-${color}`);
            });
            
            document.documentElement.classList.add(`theme-${this.value}`);
            localStorage.setItem('themeColor', this.value);
        });
    }
}

function initAutoFadeMessages() {
    const alerts = document.querySelectorAll('.alert');
    
    alerts.forEach(function(alert) {
        // Auto fade success messages after 5 seconds
        if (alert.classList.contains('alert-success')) {
            setTimeout(function() {
                fadeOut(alert, function() {
                    alert.remove();
                });
            }, 5000);
        }
        
        // Auto fade info messages after 7 seconds
        if (alert.classList.contains('alert-info')) {
            setTimeout(function() {
                fadeOut(alert, function() {
                    alert.remove();
                });
            }, 7000);
        }
        
        // Auto fade warning messages after 10 seconds
        if (alert.classList.contains('alert-warning')) {
            setTimeout(function() {
                fadeOut(alert, function() {
                    alert.remove();
                });
            }, 10000);
        }
        
        // Add close button functionality
        const closeBtn = alert.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                fadeOut(alert, function() {
                    alert.remove();
                });
            });
        }
    });
}

function fadeOut(element, callback) {
    element.style.transition = 'opacity 0.5s ease';
    element.style.opacity = '0';
    
    setTimeout(function() {
        if (callback) callback();
    }, 500);
}

function initColorPicker() {
    const colorOptions = document.querySelectorAll('.theme-color');
    
    colorOptions.forEach(function(colorOption) {
        colorOption.addEventListener('click', function() {
            const color = this.getAttribute('data-color');
            
            // Remove active class from all
            colorOptions.forEach(opt => opt.classList.remove('active'));
            
            // Add active class to clicked
            this.classList.add('active');
            
            // Remove all color classes
            const colors = ['blue', 'green', 'red', 'purple', 'orange'];
            colors.forEach(color => {
                document.documentElement.classList.remove(`theme-${color}`);
            });
            
            // Add selected color
            document.documentElement.classList.add(`theme-${color}`);
            localStorage.setItem('themeColor', color);
        });
    });
}

function initCounters() {
    const counters = document.querySelectorAll('.counter');
    
    counters.forEach(function(counter) {
        const target = parseInt(counter.getAttribute('data-target'));
        const increment = target / 100;
        let current = 0;
        
        const updateCounter = function() {
            if (current < target) {
                current += increment;
                counter.textContent = Math.ceil(current);
                setTimeout(updateCounter, 20);
            } else {
                counter.textContent = target;
            }
        };
        
        // Start counter when element is in viewport
        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    updateCounter();
                    observer.unobserve(entry.target);
                }
            });
        });
        
        observer.observe(counter);
    });
}

// Utility Functions
function showLoading(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="spinner"></span> Processing...';
    button.disabled = true;
    return originalText;
}

function hideLoading(button, originalText) {
    button.innerHTML = originalText;
    button.disabled = false;
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        fadeOut(toast, () => toast.remove());
    }, 5000);
    
    // Remove toast when close button is clicked
    const closeBtn = toast.querySelector('.btn-close');
    closeBtn.addEventListener('click', () => {
        fadeOut(toast, () => toast.remove());
    });
}

// Confirm Dialog
function confirmDialog(message, callback) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Action</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="confirmButton">Confirm</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    const confirmButton = modal.querySelector('#confirmButton');
    confirmButton.addEventListener('click', function() {
        callback();
        modalInstance.hide();
    });
    
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}