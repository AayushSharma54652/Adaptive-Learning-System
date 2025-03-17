/**
 * Admin Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin navigation
    initializeAdminNav();
    
    // Initialize charts
    initializeOverviewCharts();
    initializeAnalyticsCharts();
    
    // Initialize tables
    initializeDataTables();
    
    // Initialize modals
    initializeModals();
    
    // Initialize range inputs
    initializeRangeInputs();
    
    // Initialize buttons and actions
    initializeButtons();
});

/**
 * Initialize admin navigation tabs
 */
function initializeAdminNav() {
    const navItems = document.querySelectorAll('.admin-nav-item');
    const sections = document.querySelectorAll('.admin-section');
    
    // Check for hash in URL
    const hash = window.location.hash;
    if (hash) {
        const targetTab = document.querySelector(`.admin-nav-item[href="${hash}"]`);
        if (targetTab) {
            showAdminSection(targetTab);
        }
    }
    
    // Add click event to nav items
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update URL hash without scrolling
            const hash = this.getAttribute('href');
            history.pushState(null, null, hash);
            
            showAdminSection(this);
        });
    });
    
    // Function to show the correct section
    function showAdminSection(navItem) {
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
 * Initialize overview charts
 */
function initializeOverviewCharts() {
    // Activity chart
    const activityChart = document.getElementById('activity-chart');
    if (activityChart) {
        new Chart(activityChart, {
            type: 'line',
            data: {
                labels: getLastNDays(30),
                datasets: [{
                    label: 'Active Users',
                    data: generateRandomData(30, 50, 150),
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Number of Users'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    // Paths chart
    const pathsChart = document.getElementById('paths-chart');
    if (pathsChart) {
        new Chart(pathsChart, {
            type: 'bar',
            data: {
                labels: ['Basic Arithmetic', 'Algebra Fundamentals', 'Geometry Basics', 'Statistics Intro', 'Probability'],
                datasets: [{
                    label: 'Completion Rate',
                    data: [85, 72, 65, 48, 30],
                    backgroundColor: 'rgba(46, 204, 113, 0.7)',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Completion Rate (%)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize analytics charts
 */
function initializeAnalyticsCharts() {
    // Engagement chart
    const engagementChart = document.getElementById('engagement-chart');
    if (engagementChart) {
        new Chart(engagementChart, {
            type: 'line',
            data: {
                labels: getLastNDays(30),
                datasets: [{
                    label: 'Daily Active Users',
                    data: generateRandomData(30, 80, 150),
                    borderColor: 'rgba(52, 152, 219, 1)',
                    backgroundColor: 'transparent',
                    tension: 0.4
                }, {
                    label: 'Session Duration (min)',
                    data: generateRandomData(30, 15, 45),
                    borderColor: 'rgba(46, 204, 113, 1)',
                    backgroundColor: 'transparent',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }
    
    // Mastery chart
    const masteryChart = document.getElementById('mastery-chart');
    if (masteryChart) {
        new Chart(masteryChart, {
            type: 'radar',
            data: {
                labels: ['Addition', 'Subtraction', 'Multiplication', 'Division', 'Fractions', 'Decimals', 'Percentages', 'Basic Algebra'],
                datasets: [{
                    label: 'Average Mastery',
                    data: [0.92, 0.87, 0.78, 0.75, 0.68, 0.72, 0.65, 0.45],
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                    pointBorderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scale: {
                    min: 0,
                    max: 1
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + Math.round(context.raw * 100) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Assessment chart
    const assessmentChart = document.getElementById('assessment-chart');
    if (assessmentChart) {
        new Chart(assessmentChart, {
            type: 'bar',
            data: {
                labels: ['Addition', 'Subtraction', 'Multiplication', 'Division', 'Fractions', 'Decimals'],
                datasets: [{
                    label: 'Success Rate',
                    data: [92, 88, 75, 72, 65, 68],
                    backgroundColor: 'rgba(52, 152, 219, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Success Rate (%)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.raw + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Effectiveness chart
    const effectivenessChart = document.getElementById('effectiveness-chart');
    if (effectivenessChart) {
        new Chart(effectivenessChart, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Content Items',
                    data: [
                        { x: 78, y: 150 },
                        { x: 92, y: 120 },
                        { x: 65, y: 90 },
                        { x: 87, y: 110 },
                        { x: 73, y: 130 },
                        { x: 55, y: 40 },
                        { x: 62, y: 70 },
                        { x: 95, y: 160 },
                        { x: 88, y: 140 },
                        { x: 76, y: 95 }
                    ],
                    backgroundColor: 'rgba(52, 152, 219, 0.7)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    pointRadius: 8,
                    pointHoverRadius: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Engagement (views)'
                        }
                    },
                    x: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Mastery Improvement (%)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return 'Mastery: ' + context.raw.x + '%, Engagement: ' + context.raw.y + ' views';
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Initialize data tables and pagination
 */
function initializeDataTables() {
    // Users table
    const userSearch = document.getElementById('user-search');
    if (userSearch) {
        userSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const userRows = document.querySelectorAll('.users-table tbody tr');
            
            userRows.forEach(row => {
                const username = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                const email = row.querySelector('td:nth-child(3)').textContent.toLowerCase();
                
                if (username.includes(searchTerm) || email.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Content table
    const contentSearch = document.getElementById('content-search');
    if (contentSearch) {
        contentSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const contentRows = document.querySelectorAll('.content-table tbody tr');
            
            contentRows.forEach(row => {
                const title = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                
                if (title.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Apply filters button
    const applyFiltersBtn = document.getElementById('apply-filters');
    if (applyFiltersBtn) {
        applyFiltersBtn.addEventListener('click', function() {
            const typeFilter = document.getElementById('content-type-filter').value;
            const difficultyFilter = document.getElementById('difficulty-filter').value;
            const knowledgeFilter = document.getElementById('knowledge-filter').value;
            
            const contentRows = document.querySelectorAll('.content-table tbody tr');
            
            contentRows.forEach(row => {
                const type = row.querySelector('td:nth-child(3)').textContent;
                const difficulty = row.querySelector('td:nth-child(4)').textContent;
                const knowledge = row.querySelector('td:nth-child(5)').textContent;
                
                const typeMatch = !typeFilter || type === typeFilter;
                const difficultyMatch = !difficultyFilter || difficulty === difficultyFilter;
                const knowledgeMatch = !knowledgeFilter || knowledge.includes(knowledgeFilter);
                
                if (typeMatch && difficultyMatch && knowledgeMatch) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Reset filters button
    const resetFiltersBtn = document.getElementById('reset-filters');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            const filterSelects = document.querySelectorAll('.content-filters select');
            filterSelects.forEach(select => {
                select.value = '';
            });
            
            const contentRows = document.querySelectorAll('.content-table tbody tr');
            contentRows.forEach(row => {
                row.style.display = '';
            });
        });
    }
    
    // Pagination buttons
    const prevButtons = document.querySelectorAll('.pagination-prev');
    const nextButtons = document.querySelectorAll('.pagination-next');
    
    prevButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                // This would trigger an API call in a real implementation
                // to fetch the previous page of data
                console.log('Previous page');
            }
        });
    });
    
    nextButtons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.disabled) {
                // This would trigger an API call in a real implementation
                // to fetch the next page of data
                console.log('Next page');
            }
        });
    });
}

/**
 * Initialize modals
 */
function initializeModals() {
    // Get all modals
    const modals = document.querySelectorAll('.modal');
    const closeButtons = document.querySelectorAll('.close-modal');
    
    // View user buttons
    const viewUserButtons = document.querySelectorAll('.view-user');
    viewUserButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-id');
            openUserModal(userId);
        });
    });
    
    // View content buttons
    const viewContentButtons = document.querySelectorAll('.view-content');
    viewContentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const contentId = this.getAttribute('data-id');
            openContentModal(contentId);
        });
    });
    
    // View assessment buttons
    const viewAssessmentButtons = document.querySelectorAll('.view-assessment');
    viewAssessmentButtons.forEach(button => {
        button.addEventListener('click', function() {
            const assessmentId = this.getAttribute('data-id');
            openAssessmentModal(assessmentId);
        });
    });
    
    // Close modals
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            modal.style.display = 'none';
        });
    });
    
    // Close when clicking outside modal content
    window.addEventListener('click', function(event) {
        modals.forEach(modal => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Modal open functions
    function openUserModal(userId) {
        const modal = document.getElementById('user-modal');
        const modalTitle = document.getElementById('user-modal-title');
        const modalContent = document.getElementById('user-modal-content');
        
        // In a real implementation, this would fetch user data from the server
        // For now, we'll use dummy data
        modalTitle.textContent = `User Details (ID: ${userId})`;
        modalContent.innerHTML = `
            <div class="user-profile">
                <div class="user-header">
                    <div class="user-avatar">👤</div>
                    <div class="user-info">
                        <h4>User ${userId}</h4>
                        <p>user${userId}@example.com</p>
                        <p>Registered: 2025-01-15</p>
                    </div>
                </div>
                <div class="user-stats">
                    <h4>Learning Statistics</h4>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">Overall Progress</div>
                            <div class="stat-value">68%</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Learning Time</div>
                            <div class="stat-value">35h 42m</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Completed Content</div>
                            <div class="stat-value">24 items</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Assessment Score</div>
                            <div class="stat-value">75%</div>
                        </div>
                    </div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-primary">Send Message</button>
                    <button class="btn btn-outline">Reset Progress</button>
                    <button class="btn btn-outline">View Complete Activity</button>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
    }
    
    function openContentModal(contentId) {
        const modal = document.getElementById('content-modal');
        const modalTitle = document.getElementById('content-modal-title');
        const modalContent = document.getElementById('content-modal-content');
        
        // In a real implementation, this would fetch content data from the server
        modalTitle.textContent = `Content Details (ID: ${contentId})`;
        modalContent.innerHTML = `
            <div class="content-preview">
                <h4>Content Title Example</h4>
                <p>This is a sample content description. In a real implementation, this would show the actual content details.</p>
                
                <div class="content-meta">
                    <div class="meta-item">
                        <div class="meta-label">Type</div>
                        <div class="meta-value">Lesson</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Difficulty</div>
                        <div class="meta-value">3 - Intermediate</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Knowledge Components</div>
                        <div class="meta-value">Addition, Subtraction</div>
                    </div>
                    <div class="meta-item">
                        <div class="meta-label">Total Views</div>
                        <div class="meta-value">245</div>
                    </div>
                </div>
                
                <div class="content-actions">
                    <button class="btn btn-primary">Edit Content</button>
                    <button class="btn btn-outline">View Full Content</button>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
    }
    
    function openAssessmentModal(assessmentId) {
        const modal = document.getElementById('assessment-modal');
        const modalTitle = document.getElementById('assessment-modal-title');
        const modalContent = document.getElementById('assessment-modal-content');
        
        // In a real implementation, this would fetch assessment data from the server
        modalTitle.textContent = `Assessment Item Details (ID: ${assessmentId})`;
        modalContent.innerHTML = `
            <div class="assessment-preview">
                <div class="assessment-question">
                    <h4>Question</h4>
                    <p>What is 5 + 7?</p>
                </div>
                
                <div class="assessment-options">
                    <h4>Options</h4>
                    <div class="option-list">
                        <div class="option">A) 10</div>
                        <div class="option correct">B) 12</div>
                        <div class="option">C) 13</div>
                        <div class="option">D) 15</div>
                    </div>
                </div>
                
                <div class="assessment-explanation">
                    <h4>Explanation</h4>
                    <p>When we add 5 and 7, we get 12. This is a basic addition problem.</p>
                </div>
                
                <div class="assessment-stats">
                    <h4>Performance Statistics</h4>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-label">Success Rate</div>
                            <div class="stat-value">78%</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Avg. Response Time</div>
                            <div class="stat-value">12s</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Total Attempts</div>
                            <div class="stat-value">156</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Difficulty Rating</div>
                            <div class="stat-value">1.2 (Easy)</div>
                        </div>
                    </div>
                </div>
                
                <div class="assessment-actions">
                    <button class="btn btn-primary">Edit Question</button>
                    <button class="btn btn-outline">View Response Data</button>
                </div>
            </div>
        `;
        
        modal.style.display = 'block';
    }
}

/**
 * Initialize range inputs with live value display
 */
function initializeRangeInputs() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    
    rangeInputs.forEach(input => {
        const valueDisplay = document.getElementById(`${input.id}-value`);
        
        if (valueDisplay) {
            // Set initial value
            valueDisplay.textContent = input.value;
            
            // Update value display when range is changed
            input.addEventListener('input', function() {
                valueDisplay.textContent = this.value;
            });
        }
    });
}

/**
 * Initialize various buttons and their actions
 */
function initializeButtons() {
    // System maintenance buttons
    const rebuildIndexesBtn = document.getElementById('rebuild-indexes-btn');
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    const backupSystemBtn = document.getElementById('backup-system-btn');
    
    if (rebuildIndexesBtn) {
        rebuildIndexesBtn.addEventListener('click', function() {
            this.textContent = 'Rebuilding...';
            this.disabled = true;
            
            // Simulate rebuilding process
            setTimeout(() => {
                alert('Indexes rebuilt successfully!');
                this.textContent = 'Rebuild Indexes';
                this.disabled = false;
            }, 2000);
        });
    }
    
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', function() {
            this.textContent = 'Clearing...';
            this.disabled = true;
            
            // Simulate cache clearing process
            setTimeout(() => {
                alert('Cache cleared successfully!');
                this.textContent = 'Clear Cache';
                this.disabled = false;
            }, 1500);
        });
    }
    
    if (backupSystemBtn) {
        backupSystemBtn.addEventListener('click', function() {
            this.textContent = 'Backing up...';
            this.disabled = true;
            
            // Simulate backup process
            setTimeout(() => {
                const date = new Date().toISOString().slice(0, 10);
                const fakeLink = document.createElement('a');
                fakeLink.href = '#';
                fakeLink.download = `adaptive_learning_backup_${date}.zip`;
                fakeLink.click();
                
                this.textContent = 'Backup System';
                this.disabled = false;
            }, 3000);
        });
    }
    
    // System params form
    const systemParamsForm = document.getElementById('system-params-form');
    if (systemParamsForm) {
        systemParamsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form values
            const learningRate = document.getElementById('learning-rate').value;
            const recommendationDiversity = document.getElementById('recommendation-diversity').value;
            const masteryThreshold = document.getElementById('mastery-threshold').value;
            
            // In a real implementation, this would submit to the server
            console.log('System parameters updated:', {
                learningRate,
                recommendationDiversity,
                masteryThreshold
            });
            
            alert('System parameters updated successfully!');
        });
    }
    
    // Reset settings button
    const resetSettingsBtn = document.getElementById('reset-settings');
    if (resetSettingsBtn) {
        resetSettingsBtn.addEventListener('click', function() {
            // Reset form to default values
            document.getElementById('learning-rate').value = 0.1;
            document.getElementById('learning-rate-value').textContent = 0.1;
            
            document.getElementById('recommendation-diversity').value = 0.3;
            document.getElementById('recommendation-diversity-value').textContent = 0.3;
            
            document.getElementById('mastery-threshold').value = 0.8;
            document.getElementById('mastery-threshold-value').textContent = 0.8;
        });
    }
    
    // Analytics update button
    const updateAnalyticsBtn = document.getElementById('update-analytics');
    if (updateAnalyticsBtn) {
        updateAnalyticsBtn.addEventListener('click', function() {
            const dateRange = document.getElementById('date-range').value;
            const groupBy = document.getElementById('group-by').value;
            
            // In a real implementation, this would fetch new data based on filters
            alert(`Analytics updated with date range: ${dateRange} days, grouped by: ${groupBy}`);
            
            // Here you would re-initialize charts with new data
        });
    }
    
    // Add user button
    const addUserBtn = document.getElementById('add-user-btn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', function() {
            // In a real implementation, this would open a form to add a new user
            alert('This would open a form to add a new user.');
        });
    }
    
    // Add content button
    const addContentBtn = document.getElementById('add-content-btn');
    if (addContentBtn) {
        addContentBtn.addEventListener('click', function() {
            // In a real implementation, this would open a content creation form
            alert('This would open a form to create new content.');
        });
    }
    
    // Add assessment button
    const addAssessmentBtn = document.getElementById('add-assessment-btn');
    if (addAssessmentBtn) {
        addAssessmentBtn.addEventListener('click', function() {
            // In a real implementation, this would open an assessment creation form
            alert('This would open a form to create a new assessment item.');
        });
    }
    
    // Manage knowledge components button
    const manageKcBtn = document.getElementById('manage-kc-btn');
    if (manageKcBtn) {
        manageKcBtn.addEventListener('click', function() {
            // In a real implementation, this would open a knowledge component management interface
            alert('This would open the knowledge component management interface.');
        });
    }
    
    // Manage learning paths button
    const managePathsBtn = document.getElementById('manage-paths-btn');
    if (managePathsBtn) {
        managePathsBtn.addEventListener('click', function() {
            // In a real implementation, this would open a learning path management interface
            alert('This would open the learning path management interface.');
        });
    }
}

/**
 * Helper function to get an array of the last N days
 * @param {number} n - Number of days
 * @returns {Array} - Array of date strings
 */
function getLastNDays(n) {
    const result = [];
    for (let i = n - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        result.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    return result;
}

/**
 * Helper function to generate random data for charts
 * @param {number} count - Number of data points
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {Array} - Array of random numbers
 */
function generateRandomData(count, min, max) {
    return Array.from({ length: count }, () => Math.floor(Math.random() * (max - min + 1)) + min);
}