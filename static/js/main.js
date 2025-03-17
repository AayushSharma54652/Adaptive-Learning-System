/**
 * Main JavaScript for Adaptive Learning System
 */

// DOM Ready event
document.addEventListener('DOMContentLoaded', function() {
    // Add any global event listeners or initializations here
    initializeTooltips();
    handleFormValidation();
});

/**
 * Initialize tooltips across the site
 */
function initializeTooltips() {
    // Simple tooltip implementation
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('data-tooltip');
            
            // Create tooltip element
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = tooltipText;
            
            // Position tooltip
            const rect = this.getBoundingClientRect();
            tooltip.style.top = `${rect.bottom + window.scrollY + 5}px`;
            tooltip.style.left = `${rect.left + window.scrollX + (rect.width / 2)}px`;
            tooltip.style.transform = 'translateX(-50%)';
            
            // Add to DOM
            document.body.appendChild(tooltip);
            
            // Store reference for removal
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            // Remove tooltip
            if (this._tooltip) {
                document.body.removeChild(this._tooltip);
                this._tooltip = null;
            }
        });
    });
}

/**
 * Handle form validation across the site
 */
function handleFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check required fields
            const requiredFields = form.querySelectorAll('[required]');
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    highlightInvalidField(field);
                } else {
                    removeInvalidHighlight(field);
                }
            });
            
            // Check email format
            const emailFields = form.querySelectorAll('input[type="email"]');
            emailFields.forEach(field => {
                if (field.value && !isValidEmail(field.value)) {
                    isValid = false;
                    highlightInvalidField(field, 'Please enter a valid email address');
                }
            });
            
            // Check password length
            const passwordFields = form.querySelectorAll('input[type="password"]');
            passwordFields.forEach(field => {
                if (field.value && field.value.length < 6) {
                    isValid = false;
                    highlightInvalidField(field, 'Password must be at least 6 characters');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} - Is the email valid
 */
function isValidEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

/**
 * Highlight an invalid form field
 * @param {HTMLElement} field - The field to highlight
 * @param {string} message - Optional error message
 */
function highlightInvalidField(field, message = 'This field is required') {
    field.classList.add('invalid');
    
    // Remove any existing error message
    const existingError = field.parentNode.querySelector('.error-text');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message
    const errorText = document.createElement('div');
    errorText.className = 'error-text';
    errorText.textContent = message;
    
    // Insert after the field
    field.parentNode.insertBefore(errorText, field.nextSibling);
    
    // Add event listener to remove error on input
    field.addEventListener('input', function() {
        removeInvalidHighlight(field);
    }, { once: true });
}

/**
 * Remove invalid highlight from a field
 * @param {HTMLElement} field - The field to remove highlighting from
 */
function removeInvalidHighlight(field) {
    field.classList.remove('invalid');
    
    // Remove error message if it exists
    const errorText = field.parentNode.querySelector('.error-text');
    if (errorText) {
        errorText.remove();
    }
}

/**
 * Format a date as a relative time (e.g., "2 days ago")
 * @param {string} dateString - ISO date string
 * @returns {string} - Formatted relative time
 */
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return 'just now';
    }
    
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    if (diffInMinutes < 60) {
        return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''} ago`;
    }
    
    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) {
        return `${diffInHours} hour${diffInHours !== 1 ? 's' : ''} ago`;
    }
    
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 30) {
        return `${diffInDays} day${diffInDays !== 1 ? 's' : ''} ago`;
    }
    
    const diffInMonths = Math.floor(diffInDays / 30);
    if (diffInMonths < 12) {
        return `${diffInMonths} month${diffInMonths !== 1 ? 's' : ''} ago`;
    }
    
    const diffInYears = Math.floor(diffInMonths / 12);
    return `${diffInYears} year${diffInYears !== 1 ? 's' : ''} ago`;
}

/**
 * Create error page elements
 * @param {string} code - Error code (e.g., "404")
 * @param {string} message - Error message
 * @param {string} description - Error description
 * @returns {HTMLElement} - Error page element
 */
function createErrorPage(code, message, description) {
    const container = document.createElement('div');
    container.className = 'error-page';
    
    const errorCode = document.createElement('div');
    errorCode.className = 'error-code';
    errorCode.textContent = code;
    
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.textContent = message;
    
    const errorDescription = document.createElement('div');
    errorDescription.className = 'error-description';
    errorDescription.textContent = description;
    
    const errorActions = document.createElement('div');
    errorActions.className = 'error-actions';
    
    const homeLink = document.createElement('a');
    homeLink.href = '/';
    homeLink.className = 'btn btn-primary';
    homeLink.textContent = 'Go to Homepage';
    
    errorActions.appendChild(homeLink);
    
    container.appendChild(errorCode);
    container.appendChild(errorMessage);
    container.appendChild(errorDescription);
    container.appendChild(errorActions);
    
    return container;
}