/**
 * Dashboard Visualization Script
 * Creates interactive charts and visualizations for the dashboard
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize visualizations
    initializeKnowledgeRadarChart();
    initializeProgressChart();
    initializeLearningPathVisual();
});

/**
 * Creates a radar chart for knowledge components mastery visualization
 */
function initializeKnowledgeRadarChart() {
    // Check if the knowledge-radar element exists
    const radarContainer = document.getElementById('knowledge-radar');
    if (!radarContainer) return;

    // Get knowledge component data from the DOM
    const knowledgeComponents = [];
    const masteryLevels = [];
    
    document.querySelectorAll('.knowledge-component').forEach(component => {
        const name = component.querySelector('.component-name').textContent;
        const masteryText = component.querySelector('.mastery-value').textContent;
        const mastery = parseFloat(masteryText) / 100; // Convert percentage to decimal
        
        knowledgeComponents.push(name);
        masteryLevels.push(mastery);
    });
    
    // Create the radar chart canvas
    const canvas = document.createElement('canvas');
    canvas.id = 'radar-chart';
    radarContainer.appendChild(canvas);
    
    // Create the radar chart using Chart.js
    new Chart(canvas, {
        type: 'radar',
        data: {
            labels: knowledgeComponents,
            datasets: [{
                label: 'Knowledge Mastery',
                data: masteryLevels,
                backgroundColor: 'rgba(52, 152, 219, 0.2)',
                borderColor: 'rgba(52, 152, 219, 1)',
                pointBackgroundColor: 'rgba(52, 152, 219, 1)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgba(52, 152, 219, 1)'
            }]
        },
        options: {
            scale: {
                ticks: {
                    beginAtZero: true,
                    max: 1,
                    stepSize: 0.2
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Knowledge Component Mastery'
                },
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

/**
 * Creates a line chart showing progress over time
 */
function initializeProgressChart() {
    // Check if the progress-chart element exists
    const progressContainer = document.getElementById('progress-chart');
    if (!progressContainer) return;
    
    // In a real implementation, this data would be fetched from the server
    // For now, we'll use sample data
    const progressData = {
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Current'],
        datasets: [{
            label: 'Overall Mastery',
            data: [0.1, 0.25, 0.4, 0.65, getCurrentMastery()],
            borderColor: 'rgba(52, 152, 219, 1)',
            backgroundColor: 'rgba(52, 152, 219, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };
    
    // Create the progress chart canvas
    const canvas = document.createElement('canvas');
    canvas.id = 'mastery-progress-chart';
    progressContainer.appendChild(canvas);
    
    // Create the line chart using Chart.js
    new Chart(canvas, {
        type: 'line',
        data: progressData,
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            return Math.round(value * 100) + '%';
                        }
                    },
                    title: {
                        display: true,
                        text: 'Mastery Level'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Time'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Learning Progress Over Time'
                },
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

/**
 * Create a visual representation of the learning path
 */
function initializeLearningPathVisual() {
    // Check if the learning-path-visual element exists
    const pathContainer = document.getElementById('learning-path-visual');
    if (!pathContainer) return;
    
    // Create the SVG element
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '150');
    svg.setAttribute('viewBox', '0 0 1000 150');
    pathContainer.appendChild(svg);
    
    // Get the current position from the DOM
    let currentPosition = 0;
    let totalItems = 5; // Default value
    
    const pathProgress = document.querySelector('.path-progress-label');
    if (pathProgress) {
        const progressText = pathProgress.textContent;
        const match = progressText.match(/Progress: (\d+) \/ (\d+)/);
        if (match) {
            currentPosition = parseInt(match[1]);
            totalItems = parseInt(match[2]);
        }
    }
    
    // Create the path
    const pathWidth = 800;
    const nodeRadius = 15;
    const nodeDistance = pathWidth / (totalItems > 1 ? totalItems - 1 : 1);
    const pathStartX = 100;
    const pathY = 75;
    
    // Draw the path line
    const pathLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathLine.setAttribute('d', `M ${pathStartX} ${pathY} H ${pathStartX + pathWidth}`);
    pathLine.setAttribute('stroke', '#ddd');
    pathLine.setAttribute('stroke-width', '4');
    pathLine.setAttribute('fill', 'none');
    svg.appendChild(pathLine);
    
    // Draw the completed part of the path
    if (currentPosition > 0) {
        const completedLine = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const completedWidth = Math.min(currentPosition, totalItems - 1) * nodeDistance;
        completedLine.setAttribute('d', `M ${pathStartX} ${pathY} H ${pathStartX + completedWidth}`);
        completedLine.setAttribute('stroke', '#2ecc71');
        completedLine.setAttribute('stroke-width', '4');
        completedLine.setAttribute('fill', 'none');
        svg.appendChild(completedLine);
    }
    
    // Draw nodes
    for (let i = 0; i < totalItems; i++) {
        const nodeX = pathStartX + (i * nodeDistance);
        
        // Draw node circle
        const nodeCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        nodeCircle.setAttribute('cx', nodeX);
        nodeCircle.setAttribute('cy', pathY);
        nodeCircle.setAttribute('r', nodeRadius);
        
        if (i < currentPosition) {
            // Completed nodes
            nodeCircle.setAttribute('fill', '#2ecc71');
            nodeCircle.setAttribute('stroke', '#27ae60');
        } else if (i === currentPosition) {
            // Current node
            nodeCircle.setAttribute('fill', '#3498db');
            nodeCircle.setAttribute('stroke', '#2980b9');
        } else {
            // Future nodes
            nodeCircle.setAttribute('fill', '#ecf0f1');
            nodeCircle.setAttribute('stroke', '#bdc3c7');
        }
        
        nodeCircle.setAttribute('stroke-width', '2');
        svg.appendChild(nodeCircle);
        
        // Draw checkmark for completed nodes
        if (i < currentPosition) {
            const checkmark = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            checkmark.setAttribute('x', nodeX);
            checkmark.setAttribute('y', pathY + 5);
            checkmark.setAttribute('text-anchor', 'middle');
            checkmark.setAttribute('fill', 'white');
            checkmark.setAttribute('font-weight', 'bold');
            checkmark.textContent = '✓';
            svg.appendChild(checkmark);
        } else {
            // Draw node number
            const nodeText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            nodeText.setAttribute('x', nodeX);
            nodeText.setAttribute('y', pathY + 5);
            nodeText.setAttribute('text-anchor', 'middle');
            nodeText.setAttribute('fill', i === currentPosition ? 'white' : '#7f8c8d');
            nodeText.setAttribute('font-weight', 'bold');
            nodeText.textContent = (i + 1).toString();
            svg.appendChild(nodeText);
        }
        
        // Add node label
        const nodeLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        nodeLabel.setAttribute('x', nodeX);
        nodeLabel.setAttribute('y', pathY + 35);
        nodeLabel.setAttribute('text-anchor', 'middle');
        nodeLabel.setAttribute('fill', '#34495e');
        nodeLabel.setAttribute('font-size', '12');
        nodeLabel.textContent = `Step ${i + 1}`;
        svg.appendChild(nodeLabel);
    }
}

/**
 * Get the current mastery level from the DOM
 * @returns {number} Mastery level (0-1)
 */
function getCurrentMastery() {
    const masteryElement = document.querySelector('.progress-metrics .metric:first-child .progress-value');
    if (masteryElement) {
        const masteryText = masteryElement.textContent.trim();
        return parseFloat(masteryText) / 100;
    }
    return 0.5; // Default value
}