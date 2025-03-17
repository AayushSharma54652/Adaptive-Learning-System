/**
 * Dashboard JavaScript for Adaptive Learning System
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeDashboard();
});

/**
 * Initialize dashboard components
 */
function initializeDashboard() {
    // Format dates
    formatDates();
    
    // Format activity timestamps as relative time
    formatActivityTimes();
    
    // Add event listeners for recommendations
    addRecommendationListeners();
}

/**
 * Format dates in the dashboard
 */
function formatDates() {
    const dateElements = document.querySelectorAll('.date-format');
    
    dateElements.forEach(element => {
        const dateString = element.getAttribute('data-date');
        if (dateString) {
            const date = new Date(dateString);
            element.textContent = date.toLocaleDateString();
        }
    });
}

/**
 * Format activity timestamps as relative time
 */
function formatActivityTimes() {
    const timeElements = document.querySelectorAll('.activity-time');
    
    timeElements.forEach(element => {
        const dateString = element.textContent;
        if (dateString) {
            try {
                // Use the formatRelativeTime function from main.js
                if (typeof formatRelativeTime === 'function') {
                    element.textContent = formatRelativeTime(dateString);
                }
            } catch (error) {
                console.error('Error formatting time:', error);
            }
        }
    });
}

/**
 * Add event listeners for recommendation cards
 */
function addRecommendationListeners() {
    const recommendationCards = document.querySelectorAll('.recommendation-card');
    
    recommendationCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // If the click is on the card but not on the button, trigger the button click
            if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
                const button = this.querySelector('.btn');
                if (button) {
                    button.click();
                }
            }
        });
    });
}

/**
 * Update knowledge component visualization
 * @param {Object} data - Knowledge component data
 */
function updateKnowledgeVisuals(data) {
    // This would be used in a more advanced implementation
    // to update the knowledge component visualization dynamically
    console.log('Knowledge component data updated:', data);
}