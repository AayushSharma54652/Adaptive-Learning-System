/**
 * Settings Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize settings navigation
    initializeSettingsNav();
    
    // Initialize profile picture upload
    initializeProfilePicUpload();
    
    // Initialize password validation
    initializePasswordValidation();
    
    // Initialize data management buttons
    initializeDataManagement();
});

/**
 * Initialize settings navigation tabs
 */
function initializeSettingsNav() {
    const navItems = document.querySelectorAll('.settings-nav-item');
    const sections = document.querySelectorAll('.settings-section');
    
    // Check for hash in URL
    const hash = window.location.hash;
    if (hash) {
        const targetTab = document.querySelector(`.settings-nav-item[href="${hash}"]`);
        if (targetTab) {
            showSettingsSection(targetTab);
        }
    }
    
    // Add click event to nav items
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update URL hash without scrolling
            const hash = this.getAttribute('href');
            history.pushState(null, null, hash);
            
            showSettingsSection(this);
        });
    });
    
    // Function to show the correct section
    function showSettingsSection(navItem) {
        // Remove active class from all nav items and sections
        navItems.forEach(item => item.classList.remove('active'));
        sections.forEach(section => section.classList.remove('active'));
        
        // Add active class to clicked nav item
        navItem.classList.add('active');
        
        // Show the corresponding section
        const targetId = navItem.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
    }
}

/**
 * Initialize profile picture upload functionality
 */
function initializeProfilePicUpload() {
    const uploadBtn = document.getElementById('upload-pic-btn');
    const fileInput = document.getElementById('profile-pic');
    const preview = document.getElementById('profile-pic-preview');
    
    if (!uploadBtn || !fileInput || !preview) return;
    
    uploadBtn.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                preview.src = e.target.result;
            };
            
            reader.readAsDataURL(this.files[0]);
        }
    });
}

/**
 * Initialize password validation
 */
function initializePasswordValidation() {
    const passwordForm = document.querySelector('form[action*="change_password"]');
    if (!passwordForm) return;
    
    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-password');
    
    passwordForm.addEventListener('submit', function(e) {
        // Reset any previous error messages
        const errorMessages = this.querySelectorAll('.field-error');
        errorMessages.forEach(msg => msg.remove());
        
        // Check if passwords match
        if (newPassword.value !== confirmPassword.value) {
            e.preventDefault();
            
            // Create error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'field-error';
            errorMessage.textContent = 'Passwords do not match';
            errorMessage.style.color = 'var(--warn-color)';
            errorMessage.style.fontSize = '0.9rem';
            errorMessage.style.marginTop = '5px';
            
            // Add error message after confirm password field
            confirmPassword.parentNode.appendChild(errorMessage);
            
            // Focus the confirm password field
            confirmPassword.focus();
        }
        
        // Check password strength
        if (newPassword.value.length < 8) {
            e.preventDefault();
            
            // Create error message
            const errorMessage = document.createElement('div');
            errorMessage.className = 'field-error';
            errorMessage.textContent = 'Password must be at least 8 characters long';
            errorMessage.style.color = 'var(--warn-color)';
            errorMessage.style.fontSize = '0.9rem';
            errorMessage.style.marginTop = '5px';
            
            // Add error message after new password field
            newPassword.parentNode.appendChild(errorMessage);
            
            // Focus the new password field
            newPassword.focus();
        }
    });
}

/**
 * Initialize data management buttons
 */
function initializeDataManagement() {
    // Export data button
    const exportBtn = document.getElementById('export-data-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Show loading state
            this.textContent = 'Preparing export...';
            this.disabled = true;
            
            // Send request to server
            fetch('/api/export-user-data', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to export data');
                }
                return response.blob();
            })
            .then(blob => {
                // Create download link
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = 'my-learning-data.json';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                
                // Reset button
                this.textContent = 'Export My Data';
                this.disabled = false;
            })
            .catch(error => {
                console.error('Error exporting data:', error);
                
                // Show error message
                alert('Failed to export data. Please try again later.');
                
                // Reset button
                this.textContent = 'Export My Data';
                this.disabled = false;
            });
        });
    }
    
    // Clear history button
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', function() {
            // Show confirmation dialog
            if (confirm('Are you sure you want to clear your learning history? This action cannot be undone.')) {
                // Show loading state
                this.textContent = 'Clearing...';
                this.disabled = true;
                
                // Send request to server
                fetch('/api/clear-learning-history', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to clear history');
                    }
                    return response.json();
                })
                .then(data => {
                    // Show success message
                    alert('Your learning history has been cleared successfully.');
                    
                    // Reset button
                    this.textContent = 'Clear Learning History';
                    this.disabled = false;
                    
                    // Reload the page to update the UI
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error clearing history:', error);
                    
                    // Show error message
                    alert('Failed to clear history. Please try again later.');
                    
                    // Reset button
                    this.textContent = 'Clear Learning History';
                    this.disabled = false;
                });
            }
        });
    }
    
    // Delete account button
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    if (deleteAccountBtn) {
        deleteAccountBtn.addEventListener('click', function() {
            // Show confirmation dialog with additional verification
            const confirmation = prompt('This action will permanently delete your account and all associated data. This cannot be undone. Type "DELETE" to confirm.');
            
            if (confirmation === 'DELETE') {
                // Show loading state
                this.textContent = 'Deleting...';
                this.disabled = true;
                
                // Send request to server
                fetch('/api/delete-account', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Failed to delete account');
                    }
                    return response.json();
                })
                .then(data => {
                    // Show success message
                    alert('Your account has been deleted successfully.');
                    
                    // Redirect to home page
                    window.location.href = '/';
                })
                .catch(error => {
                    console.error('Error deleting account:', error);
                    
                    // Show error message
                    alert('Failed to delete account. Please try again later.');
                    
                    // Reset button
                    this.textContent = 'Delete Account';
                    this.disabled = false;
                });
            }
        });
    }
}